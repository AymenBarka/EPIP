"""Thread-safe single official EPIP execution engine."""

import logging
from dataclasses import replace
from threading import RLock
from time import perf_counter

from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import integrity_boundary
from epip.execution.config import ExecutionConfig
from epip.execution.events import (
    ExecutionCompleted,
    OrderCancelled,
    OrderCreated,
    OrderFilled,
    OrderRejected,
    OrderSubmitted,
)
from epip.execution.fill_manager import FillManager
from epip.execution.graph import ExecutionGraph
from epip.execution.history import ExecutionHistory
from epip.execution.models import (
    ExecutionReason,
    ExecutionReport,
    ExecutionSnapshot,
    ExecutionStatistics,
    Order,
    OrderState,
)
from epip.execution.order_manager import OrderManager
from epip.execution.paper_adapter import PaperTradingAdapter
from epip.execution.protocols import BrokerAdapterProtocol
from epip.execution.retry_manager import RetryManager
from epip.execution.state_machine import OrderStateMachine
from epip.execution.statistics import StatisticsCollector
from epip.execution.validators import validate_order, validate_plan
from epip.risk.models import PositionPlan


class ExecutionEngine:
    def __init__(
        self,
        *,
        event_bus: EventBus,
        config: ExecutionConfig | None = None,
        broker: BrokerAdapterProtocol | None = None,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._bus = event_bus
        self._config = config or ExecutionConfig()
        self._broker = broker or PaperTradingAdapter(self._config)
        self._logger = logger or logging.getLogger("epip.execution")
        self._orders = OrderManager()
        self._fills = FillManager()
        self._retry = RetryManager()
        self._states = OrderStateMachine()
        self._statistics = StatisticsCollector()
        self._snapshots: dict[str, ExecutionSnapshot] = {}
        self._histories: dict[str, ExecutionHistory] = {}
        self._graphs: dict[str, ExecutionGraph] = {}
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    @integrity_boundary
    def execute(
        self, plan: PositionPlan, *, timestamp: str, **observations: float
    ) -> ExecutionSnapshot:
        validate_plan(plan)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(plan.symbol)
            order = self._orders.create(plan, self._config)
            validate_order(order)
            self._publish(OrderCreated, timestamp, order)
            order = self._states.transition(order, OrderState.VALIDATED)
            order = self._states.transition(order, OrderState.SUBMITTED)
            self._publish(OrderSubmitted, timestamp, order)
            response, retries = self._retry.submit(self._broker, order, self._config)
            reasons: tuple[ExecutionReason, ...]
            if response.accepted:
                order = self._states.transition(order, OrderState.ACKNOWLEDGED)
                order = self._fills.apply(order, response.fills)
                reasons = (ExecutionReason("BROKER_ACCEPTED", response.message, True),)
            else:
                order = self._states.transition(order, OrderState.REJECTED)
                reasons = (ExecutionReason("BROKER_REJECTED", response.message, False),)
            average = self._fills.average_price(order)
            commission = sum(fill.commission for fill in order.fills)
            slippage = 0.0 if average is None else average - order.requested_price
            report = ExecutionReport(
                order,
                order.quantity,
                order.filled_quantity,
                average,
                slippage,
                commission,
                order.state == OrderState.FILLED,
                reasons,
            )
            snapshot = ExecutionSnapshot(
                timestamp,
                plan.symbol,
                previous.version + 1 if previous else 1,
                plan.plan_id,
                report,
                self._config.engine_version,
            )
            self._snapshots[plan.symbol] = snapshot
            self._histories[plan.symbol] = self._histories.get(
                plan.symbol, ExecutionHistory()
            ).append(snapshot)
            self._graphs[plan.symbol] = self._graphs.get(plan.symbol, ExecutionGraph()).append(
                snapshot
            )
            self._statistics.record(report, perf_counter() - started, retries)
            self._publish_result(snapshot)
            self._logger.debug("execution v%d completed for %s", snapshot.version, plan.symbol)
            return snapshot

    @integrity_boundary
    def cancel(self, symbol: str, *, timestamp: str) -> ExecutionSnapshot:
        with self._lock:
            current = self._snapshots[symbol]
            order = current.report.order
            response = self._broker.cancel(order)
            if not response.accepted:
                return current
            order = self._states.transition(order, OrderState.CANCELLED)
            report = replace(current.report, order=order, completed=False)
            snapshot = replace(
                current, timestamp=timestamp, version=current.version + 1, report=report
            )
            self._snapshots[symbol] = snapshot
            self._histories[symbol] = self._histories[symbol].append(snapshot)
            self._graphs[symbol] = self._graphs[symbol].append(snapshot)
            self._publish(OrderCancelled, timestamp, order)
            return snapshot

    def snapshot(self, symbol: str) -> ExecutionSnapshot | None:
        with self._lock:
            return self._snapshots.get(symbol)

    def history(self, symbol: str) -> ExecutionHistory:
        with self._lock:
            return self._histories.get(symbol, ExecutionHistory())

    def graph(self, symbol: str) -> ExecutionGraph:
        with self._lock:
            return self._graphs.get(symbol, ExecutionGraph())

    def metrics(self) -> ExecutionStatistics:
        return self._statistics.snapshot()

    def _publish(
        self,
        event_type: type[OrderCreated] | type[OrderSubmitted] | type[OrderCancelled],
        timestamp: str,
        order: Order,
    ) -> None:
        self._bus.publish(
            event_type(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"{event_type.__name__}-{order.order_id}",
                timestamp=timestamp,
                symbol=order.symbol,
                order_id=order.order_id,
                plan_id=order.plan_id,
            )
        )

    def _publish_result(self, snapshot: ExecutionSnapshot) -> None:
        report = snapshot.report
        order = report.order
        event_id = f"result-{order.order_id}"
        if report.completed:
            self._bus.publish(
                OrderFilled(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    order_id=order.order_id,
                    plan_id=order.plan_id,
                    quantity=report.filled_quantity,
                )
            )
            self._bus.publish(
                ExecutionCompleted(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    order_id=order.order_id,
                    plan_id=order.plan_id,
                    commission=report.commission,
                )
            )
        elif order.state == OrderState.REJECTED:
            self._bus.publish(
                OrderRejected(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    order_id=order.order_id,
                    plan_id=order.plan_id,
                    reason=report.reasons[0].message,
                )
            )
