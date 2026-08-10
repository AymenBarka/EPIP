"""Thread-safe single official EPIP portfolio manager."""

import logging
from threading import RLock
from time import perf_counter

from epip.core.atomicity import EngineTransaction
from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import integrity_boundary
from epip.execution.models import ExecutionSnapshot, OrderSide
from epip.portfolio.allocation import calculate_allocations
from epip.portfolio.capital import available_cash, used_margin
from epip.portfolio.config import PortfolioConfig
from epip.portfolio.correlation import correlation_exposure
from epip.portfolio.equity import calculate_equity
from epip.portfolio.events import (
    AllocationChanged,
    ExposureExceeded,
    PortfolioRebalanced,
    PortfolioUpdated,
    RiskLimitReached,
)
from epip.portfolio.exposure import calculate_exposure
from epip.portfolio.graph import PortfolioGraph
from epip.portfolio.history import PortfolioHistory
from epip.portfolio.models import (
    PortfolioMetrics,
    PortfolioPosition,
    PortfolioSnapshot,
    PortfolioState,
    PositionDirection,
)
from epip.portfolio.pnl import calculate_pnl
from epip.portfolio.rebalancing import RebalanceInstruction, recommend_rebalance
from epip.portfolio.risk_limits import evaluate_limits
from epip.portfolio.statistics import PortfolioStatistics
from epip.portfolio.validators import validate_config, validate_execution


class PortfolioEngine:
    def __init__(
        self,
        *,
        event_bus: EventBus,
        config: PortfolioConfig | None = None,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._config = config or PortfolioConfig()
        validate_config(self._config)
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.portfolio")
        self._positions: dict[str, PortfolioPosition] = {}
        self._realized = self._commission = 0.0
        self._peak = self._config.initial_capital
        self._snapshot: PortfolioSnapshot | None = None
        self._history = PortfolioHistory()
        self._graph = PortfolioGraph()
        self._statistics = PortfolioStatistics()
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    @integrity_boundary
    def process(self, execution: ExecutionSnapshot) -> PortfolioSnapshot:
        validate_execution(execution)
        with self._lock:
            started = perf_counter()
            next_positions = dict(self._positions)
            report = execution.report
            assert report.average_fill_price is not None
            side = report.order.side
            signed = (
                report.filled_quantity
                if side in (OrderSide.LONG, OrderSide.BUY)
                else -report.filled_quantity
            )
            realized_delta = self._apply_fill_to(
                next_positions, execution.symbol, signed, report.average_fill_price
            )
            next_realized = self._realized + realized_delta
            next_commission = self._commission + report.commission
            positions = tuple(sorted(next_positions.values(), key=lambda item: item.symbol))
            pnl = calculate_pnl(positions, next_realized, next_commission)
            margin = used_margin(positions, self._config.margin_rate)
            cash = available_cash(
                self._config.initial_capital, next_realized, next_commission, margin
            )
            equity = calculate_equity(
                self._config.initial_capital,
                next_realized,
                pnl.unrealized,
                next_commission,
                self._peak,
                cash,
                margin,
            )
            exposure = calculate_exposure(positions, equity.current)
            allocations = calculate_allocations(positions, self._config.correlation_groups)
            correlations = correlation_exposure(allocations)
            reasons = evaluate_limits(exposure, allocations, correlations, equity, self._config)
            state = PortfolioState(
                positions, exposure, allocations, pnl, equity, correlations, reasons
            )
            version = self._snapshot.version + 1 if self._snapshot else 1
            snapshot = PortfolioSnapshot(
                execution.timestamp,
                version,
                execution.version,
                execution.position_plan_id,
                state,
                self._config.engine_version,
            )
            previous = self._snapshot
            history = self._history.append(snapshot)
            graph = self._graph.append(snapshot)
            self._statistics.record(snapshot, perf_counter() - started)
            transaction = EngineTransaction(self)
            transaction.stage("_positions", next_positions)
            transaction.stage("_realized", next_realized)
            transaction.stage("_commission", next_commission)
            transaction.stage("_peak", equity.peak)
            transaction.stage("_snapshot", snapshot)
            transaction.stage("_history", history)
            transaction.stage("_graph", graph)
            transaction.commit()
            self._logger.debug("portfolio v%d updated by %s", version, execution.position_plan_id)
        self._publish(snapshot, previous)
        return snapshot

    def snapshot(self) -> PortfolioSnapshot | None:
        with self._lock:
            return self._snapshot

    def history(self) -> PortfolioHistory:
        with self._lock:
            return self._history

    def graph(self) -> PortfolioGraph:
        with self._lock:
            return self._graph

    def metrics(self) -> PortfolioMetrics:
        return self._statistics.snapshot()

    def rebalance(self) -> tuple[RebalanceInstruction, ...]:
        with self._lock:
            if self._snapshot is None:
                return ()
            snapshot = self._snapshot
            instructions = recommend_rebalance(
                snapshot.state.allocations, self._config.max_symbol_allocation
            )
        if instructions:
            self._bus.publish(
                PortfolioRebalanced(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"rebalance-{snapshot.version}",
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                    execution_plan_id=snapshot.execution_plan_id,
                    symbols=tuple(item.symbol for item in instructions),
                )
            )
        return instructions

    def _apply_fill(self, symbol: str, signed: float, price: float) -> float:
        """Apply a fill to live state (retained for internal compatibility)."""
        return self._apply_fill_to(self._positions, symbol, signed, price)

    @classmethod
    def _apply_fill_to(
        cls,
        positions: dict[str, PortfolioPosition],
        symbol: str,
        signed: float,
        price: float,
    ) -> float:
        current = positions.get(symbol)
        if current is None:
            positions[symbol] = cls._new_position(symbol, signed, price, 0.0)
            return 0.0
        existing = current.signed_quantity
        if existing * signed > 0:
            quantity = abs(existing) + abs(signed)
            average = (current.average_price * abs(existing) + price * abs(signed)) / quantity
            positions[symbol] = cls._new_position(
                symbol, existing + signed, average, current.realized_pnl
            )
            return 0.0
        closed = min(abs(existing), abs(signed))
        realized = (price - current.average_price) * closed * (1.0 if existing > 0 else -1.0)
        remaining = existing + signed
        cumulative = current.realized_pnl + realized
        if abs(remaining) < 1e-12:
            positions.pop(symbol)
        else:
            average = current.average_price if existing * remaining > 0 else price
            positions[symbol] = cls._new_position(symbol, remaining, average, cumulative)
        return realized

    @staticmethod
    def _new_position(
        symbol: str, signed: float, price: float, realized: float
    ) -> PortfolioPosition:
        direction = PositionDirection.LONG if signed > 0 else PositionDirection.SHORT
        return PortfolioPosition(symbol, abs(signed), direction, price, price, realized, 0.0)

    def _publish(self, snapshot: PortfolioSnapshot, previous: PortfolioSnapshot | None) -> None:
        event_id = f"portfolio-{snapshot.version}"
        plan = snapshot.execution_plan_id
        self._bus.publish(
            PortfolioUpdated(
                clock=self._clock,
                id_generator=self._id_generator,
                id=event_id,
                timestamp=snapshot.timestamp,
                version=snapshot.version,
                execution_plan_id=plan,
                positions=len(snapshot.state.positions),
            )
        )
        if snapshot.state.exposure.gross_exposure > self._config.max_gross_exposure:
            self._bus.publish(
                ExposureExceeded(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                    execution_plan_id=plan,
                    gross_exposure=snapshot.state.exposure.gross_exposure,
                )
            )
        if snapshot.state.limit_reasons:
            self._bus.publish(
                RiskLimitReached(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                    execution_plan_id=plan,
                    reasons=snapshot.state.limit_reasons,
                )
            )
        old = (
            {item.symbol: item.fraction for item in previous.state.allocations} if previous else {}
        )
        for item in snapshot.state.allocations:
            if old.get(item.symbol) != item.fraction:
                self._bus.publish(
                    AllocationChanged(
                        clock=self._clock,
                        id_generator=self._id_generator,
                        id=f"allocation-{snapshot.version}-{item.symbol}",
                        timestamp=snapshot.timestamp,
                        version=snapshot.version,
                        execution_plan_id=plan,
                        symbol=item.symbol,
                        allocation=item.fraction,
                    )
                )
