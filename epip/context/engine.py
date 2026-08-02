"""Thread-safe single official Market Context source."""

import logging
from threading import RLock
from time import perf_counter

from epip.context.builder import MarketContextBuilder
from epip.context.config import MarketContextConfig
from epip.context.events import (
    BiasChanged,
    ConfluenceUpdated,
    ContextCreated,
    ContextUpdated,
    PhaseChanged,
)
from epip.context.exceptions import InvalidMarketContextInputError
from epip.context.graph import MarketContextGraph
from epip.context.history import MarketContextHistory
from epip.context.metrics import MarketContextMetrics
from epip.context.snapshot import MarketContextSnapshot, MarketContextVersion
from epip.context.statistics import MarketContextStatistics
from epip.context.validators import MarketContextValidator
from epip.core.event_bus import EventBus
from epip.fibonacci.models import FibonacciSnapshot
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class MarketContextEngine:
    def __init__(
        self,
        *,
        config: MarketContextConfig,
        event_bus: EventBus,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.context")
        self._builder = MarketContextBuilder()
        self._validator = MarketContextValidator()
        self._statistics = MarketContextStatistics()
        self._snapshots: dict[tuple[str, str], MarketContextSnapshot] = {}
        self._histories: dict[tuple[str, str], MarketContextHistory] = {}
        self._graphs: dict[tuple[str, str], MarketContextGraph] = {}
        self._lock = RLock()

    def process(
        self,
        swings: SwingSequence,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
        fibonacci: FibonacciSnapshot,
    ) -> MarketContextSnapshot:
        if not self._validator.validate(swings, structure, liquidity, fibonacci):
            raise InvalidMarketContextInputError(
                "snapshots must identify one version-aligned stream"
            )
        key = (swings.symbol, swings.timeframe)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(key)
            context = self._builder.build(swings, structure, liquidity, fibonacci)
            version = previous.version.context + 1 if previous else 1
            snapshot = MarketContextSnapshot(
                fibonacci.timestamp,
                MarketContextVersion(
                    version, structure.version, liquidity.version, fibonacci.version
                ),
                context,
                self._config.engine_version,
            )
            self._snapshots[key] = snapshot
            self._histories[key] = self._histories.get(key, MarketContextHistory()).append(snapshot)
            self._graphs[key] = self._graphs.get(key, MarketContextGraph()).append(snapshot)
            bias_changed = previous is not None and previous.context.bias != context.bias
            phase_changed = previous is not None and previous.context.phase != context.phase
            self._statistics.record(
                perf_counter() - started,
                context.confluence_score,
                bias_changed=bias_changed,
                phase_changed=phase_changed,
            )
            self._publish(snapshot, previous, bias_changed, phase_changed)
            self._logger.debug("market context v%d created for %s", version, key)
            return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> MarketContextSnapshot | None:
        with self._lock:
            return self._snapshots.get((symbol, timeframe))

    def history(self, symbol: str, timeframe: str) -> MarketContextHistory:
        with self._lock:
            return self._histories.get((symbol, timeframe), MarketContextHistory())

    def graph(self, symbol: str, timeframe: str) -> MarketContextGraph:
        with self._lock:
            return self._graphs.get((symbol, timeframe), MarketContextGraph())

    def metrics(self) -> MarketContextMetrics:
        return self._statistics.snapshot()

    def _publish(
        self,
        snapshot: MarketContextSnapshot,
        previous: MarketContextSnapshot | None,
        bias_changed: bool,
        phase_changed: bool,
    ) -> None:
        event_type = ContextUpdated if previous else ContextCreated
        self._bus.publish(
            event_type(
                id=f"context-{snapshot.symbol}-{snapshot.version.context}",
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                timestamp=snapshot.timestamp,
                version=snapshot.version.context,
            )
        )
        if bias_changed and previous is not None:
            self._bus.publish(
                BiasChanged(
                    id=f"bias-{snapshot.symbol}-{snapshot.version.context}",
                    previous=previous.context.institutional_bias,
                    current=snapshot.context.institutional_bias,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version.context,
                )
            )
        if phase_changed and previous is not None:
            self._bus.publish(
                PhaseChanged(
                    id=f"phase-{snapshot.symbol}-{snapshot.version.context}",
                    previous=previous.context.phase,
                    current=snapshot.context.phase,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version.context,
                )
            )
        self._bus.publish(
            ConfluenceUpdated(
                id=f"context-confluence-{snapshot.symbol}-{snapshot.version.context}",
                score=snapshot.context.confluence_score,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                timestamp=snapshot.timestamp,
                version=snapshot.version.context,
            )
        )
