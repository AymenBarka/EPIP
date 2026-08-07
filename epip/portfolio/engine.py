"""Thread-safe single official EPIP portfolio manager."""

import logging
from threading import RLock
from time import perf_counter

from epip.core.event_bus import EventBus
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

    def process(self, execution: ExecutionSnapshot) -> PortfolioSnapshot:
        validate_execution(execution)
        with self._lock:
            started = perf_counter()
            report = execution.report
            assert report.average_fill_price is not None
            side = report.order.side
            signed = (
                report.filled_quantity
                if side in (OrderSide.LONG, OrderSide.BUY)
                else -report.filled_quantity
            )
            realized = self._apply_fill(execution.symbol, signed, report.average_fill_price)
            self._realized += realized
            self._commission += report.commission
            positions = tuple(sorted(self._positions.values(), key=lambda item: item.symbol))
            pnl = calculate_pnl(positions, self._realized, self._commission)
            margin = used_margin(positions, self._config.margin_rate)
            cash = available_cash(
                self._config.initial_capital, self._realized, self._commission, margin
            )
            equity = calculate_equity(
                self._config.initial_capital,
                self._realized,
                pnl.unrealized,
                self._commission,
                self._peak,
                cash,
                margin,
            )
            self._peak = equity.peak
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
            self._snapshot = snapshot
            self._history = self._history.append(snapshot)
            self._graph = self._graph.append(snapshot)
            self._statistics.record(snapshot, perf_counter() - started)
            self._publish(snapshot, previous)
            self._logger.debug("portfolio v%d updated by %s", version, execution.position_plan_id)
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
            instructions = recommend_rebalance(
                self._snapshot.state.allocations, self._config.max_symbol_allocation
            )
            if instructions:
                self._bus.publish(
                    PortfolioRebalanced(
                        id=f"rebalance-{self._snapshot.version}",
                        timestamp=self._snapshot.timestamp,
                        version=self._snapshot.version,
                        execution_plan_id=self._snapshot.execution_plan_id,
                        symbols=tuple(item.symbol for item in instructions),
                    )
                )
            return instructions

    def _apply_fill(self, symbol: str, signed: float, price: float) -> float:
        current = self._positions.get(symbol)
        if current is None:
            self._positions[symbol] = self._new_position(symbol, signed, price, 0.0)
            return 0.0
        existing = current.signed_quantity
        if existing * signed > 0:
            quantity = abs(existing) + abs(signed)
            average = (current.average_price * abs(existing) + price * abs(signed)) / quantity
            self._positions[symbol] = self._new_position(
                symbol, existing + signed, average, current.realized_pnl
            )
            return 0.0
        closed = min(abs(existing), abs(signed))
        realized = (price - current.average_price) * closed * (1.0 if existing > 0 else -1.0)
        remaining = existing + signed
        cumulative = current.realized_pnl + realized
        if abs(remaining) < 1e-12:
            self._positions.pop(symbol)
        else:
            average = current.average_price if existing * remaining > 0 else price
            self._positions[symbol] = self._new_position(symbol, remaining, average, cumulative)
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
                        id=f"allocation-{snapshot.version}-{item.symbol}",
                        timestamp=snapshot.timestamp,
                        version=snapshot.version,
                        execution_plan_id=plan,
                        symbol=item.symbol,
                        allocation=item.fraction,
                    )
                )
