"""Thread-safe official EPIP liquidity source."""

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
from epip.liquidity.analyzer import LiquidityAnalyzer
from epip.liquidity.config import LiquidityConfig
from epip.liquidity.events import (
    EqualHighDetected,
    EqualLowDetected,
    LiquidityDetected,
    LiquidityPoolCreated,
    LiquiditySweepDetected,
)
from epip.liquidity.exceptions import InvalidLiquidityInputError
from epip.liquidity.graph import LiquidityGraph
from epip.liquidity.history import LiquidityHistory
from epip.liquidity.metrics import LiquidityMetrics
from epip.liquidity.models import LiquiditySnapshot
from epip.liquidity.statistics import LiquidityStatistics
from epip.liquidity.validators import LiquidityInputValidator
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class LiquidityEngine:
    def __init__(
        self,
        *,
        config: LiquidityConfig,
        event_bus: EventBus,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._config = config
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.liquidity")
        self._analyzer = LiquidityAnalyzer(config)
        self._validator = LiquidityInputValidator()
        self._stats = LiquidityStatistics()
        self._snapshots: dict[tuple[str, str], LiquiditySnapshot] = {}
        self._histories: dict[tuple[str, str], LiquidityHistory] = {}
        self._graphs: dict[tuple[str, str], LiquidityGraph] = {}
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    def process(
        self, structure: MarketStructureSnapshot, sequence: SwingSequence
    ) -> LiquiditySnapshot:
        if not self._validator.validate(structure, sequence):
            raise InvalidLiquidityInputError(
                "structure and swings must identify the same non-empty stream"
            )
        key = (sequence.symbol, sequence.timeframe)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(key)
            version = previous.version + 1 if previous else 1
            snapshot = self._analyzer.analyze(structure, sequence, version)
            self._snapshots[key] = snapshot
            self._histories[key] = self._histories.get(key, LiquidityHistory()).append(snapshot)
            self._graphs[key] = self._graphs.get(key, LiquidityGraph()).append(snapshot)
            elapsed = perf_counter() - started
            self._stats.record(
                pools=len(snapshot.pools),
                sweeps=len(snapshot.sweeps),
                highs=len(snapshot.equal_highs),
                lows=len(snapshot.equal_lows),
                stop_hunts=sum(x.stop_hunt for x in snapshot.sweeps),
                elapsed=elapsed,
            )
            self._publish(snapshot)
            return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> LiquiditySnapshot | None:
        with self._lock:
            return self._snapshots.get((symbol, timeframe))

    def history(self, symbol: str, timeframe: str) -> LiquidityHistory:
        with self._lock:
            return self._histories.get((symbol, timeframe), LiquidityHistory())

    def graph(self, symbol: str, timeframe: str) -> LiquidityGraph:
        with self._lock:
            return self._graphs.get((symbol, timeframe), LiquidityGraph())

    def metrics(self) -> LiquidityMetrics:
        return self._stats.snapshot()

    def _publish(self, snapshot: LiquiditySnapshot) -> None:
        self._bus.publish(
            LiquidityDetected(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"liquidity-{snapshot.symbol}-{snapshot.timeframe}-{snapshot.version}",
                version=snapshot.version,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                timestamp=snapshot.timestamp,
            )
        )
        for pool in snapshot.pools:
            self._bus.publish(
                LiquidityPoolCreated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"pool-{pool.pool_id}",
                    pool_id=pool.pool_id,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                )
            )
        for sweep in snapshot.sweeps:
            self._bus.publish(
                LiquiditySweepDetected(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"sweep-{snapshot.version}-{sweep.side}",
                    side=sweep.side,
                    price=sweep.sweep_price,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                )
            )
        for high in snapshot.equal_highs:
            self._bus.publish(
                EqualHighDetected(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"eqh-{snapshot.version}-{high.price}",
                    price=high.price,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                )
            )
        for low in snapshot.equal_lows:
            self._bus.publish(
                EqualLowDetected(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"eql-{snapshot.version}-{low.price}",
                    price=low.price,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                )
            )
