"""Thread-safe official Fibonacci source."""

import logging
from threading import RLock
from time import perf_counter

from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.fibonacci.analyzer import FibonacciAnalyzer
from epip.fibonacci.config import FibonacciConfig
from epip.fibonacci.events import (
    ConfluenceUpdated,
    ExtensionComputed,
    FibonacciComputed,
    GoldenZoneDetected,
    OTEFound,
)
from epip.fibonacci.exceptions import InvalidFibonacciInputError
from epip.fibonacci.graph import FibonacciGraph
from epip.fibonacci.history import FibonacciHistory
from epip.fibonacci.metrics import FibonacciMetrics
from epip.fibonacci.models import FibonacciSnapshot
from epip.fibonacci.statistics import FibonacciStatistics
from epip.fibonacci.validators import FibonacciInputValidator
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class FibonacciEngine:
    def __init__(
        self,
        *,
        config: FibonacciConfig,
        event_bus: EventBus,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._analyzer = FibonacciAnalyzer(config)
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.fibonacci")
        self._validator = FibonacciInputValidator()
        self._stats = FibonacciStatistics()
        self._snapshots: dict[tuple[str, str], FibonacciSnapshot] = {}
        self._histories: dict[tuple[str, str], FibonacciHistory] = {}
        self._graphs: dict[tuple[str, str], FibonacciGraph] = {}
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    def process(
        self,
        swings: SwingSequence,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
    ) -> FibonacciSnapshot:
        if not self._validator.validate(swings, structure, liquidity):
            raise InvalidFibonacciInputError("inputs must identify one stream with two swings")
        key = (swings.symbol, swings.timeframe)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(key)
            snapshot = self._analyzer.analyze(
                swings, structure, liquidity, previous.version + 1 if previous else 1
            )
            self._snapshots[key] = snapshot
            self._histories[key] = self._histories.get(key, FibonacciHistory()).append(snapshot)
            indices = tuple(x.point.index for x in swings.swings[-2:])
            self._graphs[key] = self._graphs.get(key, FibonacciGraph()).append(snapshot, indices)
            self._stats.record(
                perf_counter() - started, snapshot.confluence_score, snapshot.probability
            )
            self._publish(snapshot)
            return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> FibonacciSnapshot | None:
        with self._lock:
            return self._snapshots.get((symbol, timeframe))

    def history(self, symbol: str, timeframe: str) -> FibonacciHistory:
        with self._lock:
            return self._histories.get((symbol, timeframe), FibonacciHistory())

    def graph(self, symbol: str, timeframe: str) -> FibonacciGraph:
        with self._lock:
            return self._graphs.get((symbol, timeframe), FibonacciGraph())

    def metrics(self) -> FibonacciMetrics:
        return self._stats.snapshot()

    def _publish(self, s: FibonacciSnapshot) -> None:
        self._bus.publish(
            FibonacciComputed(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"fib-{s.symbol}-{s.timeframe}-{s.version}",
                version=s.version,
                symbol=s.symbol,
                timeframe=s.timeframe,
                timestamp=s.timestamp,
            )
        )
        golden = s.zones[3]
        ote = s.zones[2]
        self._bus.publish(
            GoldenZoneDetected(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"golden-{s.version}",
                low=golden.low,
                high=golden.high,
                symbol=s.symbol,
                timeframe=s.timeframe,
                timestamp=s.timestamp,
            )
        )
        self._bus.publish(
            OTEFound(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"ote-{s.version}",
                low=ote.low,
                high=ote.high,
                symbol=s.symbol,
                timeframe=s.timeframe,
                timestamp=s.timestamp,
            )
        )
        self._bus.publish(
            ExtensionComputed(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"ext-{s.version}",
                level_count=len(s.extension.levels),
                symbol=s.symbol,
                timeframe=s.timeframe,
                timestamp=s.timestamp,
            )
        )
        self._bus.publish(
            ConfluenceUpdated(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"conf-{s.version}",
                score=s.confluence_score,
                symbol=s.symbol,
                timeframe=s.timeframe,
                timestamp=s.timestamp,
            )
        )
