"""Thread-safe single official trading Decision Engine."""

import logging
from threading import RLock
from time import perf_counter

from epip.context import MarketContextSnapshot
from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.decision.analyzer import DecisionAnalyzer
from epip.decision.config import DecisionConfig
from epip.decision.events import (
    DecisionCreated,
    DecisionExecuted,
    DecisionExpired,
    DecisionInvalidated,
    DecisionUpdated,
)
from epip.decision.exceptions import InvalidDecisionInputError
from epip.decision.graph import DecisionGraph
from epip.decision.history import DecisionHistory
from epip.decision.metrics import DecisionMetrics
from epip.decision.models import DecisionAction, DecisionSnapshot
from epip.decision.statistics import DecisionStatistics
from epip.decision.validators import DecisionInputValidator
from epip.elliott import WaveSnapshot


class DecisionEngine:
    def __init__(
        self,
        *,
        config: DecisionConfig,
        event_bus: EventBus,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._config = config
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.decision")
        self._analyzer = DecisionAnalyzer(config)
        self._validator = DecisionInputValidator()
        self._statistics = DecisionStatistics()
        self._snapshots: dict[tuple[str, str], DecisionSnapshot] = {}
        self._histories: dict[tuple[str, str], DecisionHistory] = {}
        self._graphs: dict[tuple[str, str], DecisionGraph] = {}
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    def process(self, context: MarketContextSnapshot, elliott: WaveSnapshot) -> DecisionSnapshot:
        if not self._validator.validate(context, elliott):
            raise InvalidDecisionInputError("Context and Elliott snapshots must be stream-aligned")
        key = (context.symbol, context.timeframe)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(key)
            decision = self._analyzer.analyze(
                context, elliott, previous.decision if previous else None
            )
            snapshot = DecisionSnapshot(
                context.timestamp,
                context.symbol,
                context.timeframe,
                previous.version + 1 if previous else 1,
                context.version.context,
                elliott.version,
                decision,
                self._config.engine_version,
            )
            self._snapshots[key] = snapshot
            self._histories[key] = self._histories.get(key, DecisionHistory()).append(snapshot)
            self._graphs[key] = self._graphs.get(key, DecisionGraph()).append(snapshot)
            self._statistics.record(snapshot, perf_counter() - started)
            self._publish(snapshot, previous is not None)
            self._logger.debug("decision v%d created for %s", snapshot.version, key)
            return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> DecisionSnapshot | None:
        with self._lock:
            return self._snapshots.get((symbol, timeframe))

    def history(self, symbol: str, timeframe: str) -> DecisionHistory:
        with self._lock:
            return self._histories.get((symbol, timeframe), DecisionHistory())

    def graph(self, symbol: str, timeframe: str) -> DecisionGraph:
        with self._lock:
            return self._graphs.get((symbol, timeframe), DecisionGraph())

    def metrics(self) -> DecisionMetrics:
        return self._statistics.snapshot()

    def mark_executed(self, snapshot: DecisionSnapshot) -> None:
        self._bus.publish(
            DecisionExecuted(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"executed-{snapshot.decision.decision_id}",
                timestamp=snapshot.timestamp,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                version=snapshot.version,
                decision_id=snapshot.decision.decision_id,
            )
        )

    def mark_expired(self, snapshot: DecisionSnapshot) -> None:
        self._bus.publish(
            DecisionExpired(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"expired-{snapshot.decision.decision_id}",
                timestamp=snapshot.timestamp,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                version=snapshot.version,
                decision_id=snapshot.decision.decision_id,
            )
        )

    def _publish(self, snapshot: DecisionSnapshot, updated: bool) -> None:
        event_type = DecisionUpdated if updated else DecisionCreated
        decision = snapshot.decision
        self._bus.publish(
            event_type(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"decision-{snapshot.symbol}-{snapshot.version}",
                timestamp=snapshot.timestamp,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                version=snapshot.version,
                decision_id=decision.decision_id,
                action=decision.action,
            )
        )
        if decision.action == DecisionAction.INVALID:
            self._bus.publish(
                DecisionInvalidated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"invalid-{snapshot.symbol}-{snapshot.version}",
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    timeframe=snapshot.timeframe,
                    version=snapshot.version,
                    decision_id=decision.decision_id,
                    reason=decision.invalidation.reason,
                )
            )
