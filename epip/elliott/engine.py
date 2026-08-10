"""Thread-safe official Elliott Wave engine."""

import logging
from threading import RLock
from time import perf_counter

from epip.context import MarketContextSnapshot
from epip.core.atomicity import EngineTransaction
from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import integrity_boundary
from epip.elliott.analyzer import ElliottAnalyzer
from epip.elliott.config import ElliottConfig
from epip.elliott.events import (
    AlternateCreated,
    CountUpdated,
    ProjectionUpdated,
    WaveDetected,
    WaveInvalidated,
    WaveValidated,
)
from epip.elliott.exceptions import InvalidElliottInputError
from epip.elliott.graph import WaveGraph
from epip.elliott.history import WaveHistory
from epip.elliott.metrics import ElliottMetrics
from epip.elliott.models import CountStatus, WaveSnapshot
from epip.elliott.statistics import ElliottStatistics
from epip.elliott.validators import ElliottInputValidator


class ElliottWaveEngine:
    def __init__(
        self,
        *,
        config: ElliottConfig,
        event_bus: EventBus,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._config = config
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.elliott")
        self._analyzer = ElliottAnalyzer(config)
        self._validator = ElliottInputValidator()
        self._statistics = ElliottStatistics()
        self._snapshots: dict[tuple[str, str], WaveSnapshot] = {}
        self._histories: dict[tuple[str, str], WaveHistory] = {}
        self._graphs: dict[tuple[str, str], WaveGraph] = {}
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    @integrity_boundary
    def process(self, context: MarketContextSnapshot) -> WaveSnapshot:
        if not self._validator.validate(context):
            raise InvalidElliottInputError("invalid or version-misaligned Market Context")
        key = (context.symbol, context.timeframe)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(key)
            snapshot = WaveSnapshot(
                context.timestamp,
                context.symbol,
                context.timeframe,
                previous.version + 1 if previous else 1,
                context.version.context,
                self._analyzer.analyze(context),
                self._config.engine_version,
            )
            snapshots = {**self._snapshots, key: snapshot}
            histories = {
                **self._histories,
                key: self._histories.get(key, WaveHistory()).append(snapshot),
            }
            graphs = {**self._graphs, key: self._graphs.get(key, WaveGraph()).append(snapshot)}
            self._statistics.record(snapshot, perf_counter() - started)
            transaction = EngineTransaction(self)
            transaction.stage("_snapshots", snapshots)
            transaction.stage("_histories", histories)
            transaction.stage("_graphs", graphs)
            transaction.commit()
            self._logger.debug("Elliott v%d created for %s", snapshot.version, key)
        self._publish(snapshot)
        return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> WaveSnapshot | None:
        with self._lock:
            return self._snapshots.get((symbol, timeframe))

    def history(self, symbol: str, timeframe: str) -> WaveHistory:
        with self._lock:
            return self._histories.get((symbol, timeframe), WaveHistory())

    def graph(self, symbol: str, timeframe: str) -> WaveGraph:
        with self._lock:
            return self._graphs.get((symbol, timeframe), WaveGraph())

    def metrics(self) -> ElliottMetrics:
        return self._statistics.snapshot()

    def _publish(self, snapshot: WaveSnapshot) -> None:
        primary = snapshot.analysis.primary
        self._bus.publish(
            WaveDetected(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"wave-{snapshot.symbol}-{snapshot.version}",
                wave_count=len(primary.sequence.waves),
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                timestamp=snapshot.timestamp,
                version=snapshot.version,
            )
        )
        if primary.status == CountStatus.VALID:
            self._bus.publish(
                WaveValidated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"validated-{snapshot.symbol}-{snapshot.version}",
                    count_id=primary.count_id,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                )
            )
        else:
            self._bus.publish(
                WaveInvalidated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"invalid-{snapshot.symbol}-{snapshot.version}",
                    violation_count=len(primary.violations),
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                )
            )
        if snapshot.analysis.alternates:
            self._bus.publish(
                AlternateCreated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"alternate-{snapshot.symbol}-{snapshot.version}",
                    alternate_count=len(snapshot.analysis.alternates),
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                )
            )
        self._bus.publish(
            CountUpdated(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"count-{snapshot.symbol}-{snapshot.version}",
                probability=primary.probability,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                timestamp=snapshot.timestamp,
                version=snapshot.version,
            )
        )
        if snapshot.analysis.projection is not None:
            self._bus.publish(
                ProjectionUpdated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"projection-{snapshot.symbol}-{snapshot.version}",
                    target_count=len(snapshot.analysis.projection.targets),
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    timestamp=snapshot.timestamp,
                    version=snapshot.version,
                )
            )
