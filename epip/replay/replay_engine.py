"""Replay engine orchestrating market data, features, context, kernel, and events."""

from __future__ import annotations

import logging
import tracemalloc
from time import perf_counter

from epip.core.candle import Candle
from epip.core.context import MarketContext
from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    DeterministicClock,
    DeterministicIdGenerator,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import integrity_boundary
from epip.core.kernel import Kernel
from epip.features.feature_store import FeatureStore
from epip.marketdata.datasource_protocol import DataSourceProtocol
from epip.replay.replay_clock import ReplayClock
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_events import (
    CandleLoaded,
    CandleProcessed,
    ContextUpdated,
    FeatureUpdated,
    ReplayFinished,
    ReplayStarted,
)
from epip.replay.replay_metrics import ReplayMetrics
from epip.replay.replay_scheduler import ReplayScheduler
from epip.replay.replay_session import ReplaySession
from epip.replay.replay_state import ReplayState
from epip.replay.replay_statistics import ReplayStatistics
from epip.replay.replay_transaction import ReplaySessionTransaction


class ReplayEngine:
    """Streams market data through feature/context/kernel/event stages."""

    def __init__(
        self,
        *,
        market_data: DataSourceProtocol,
        feature_store: FeatureStore,
        event_bus: EventBus,
        kernel: Kernel | None = None,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self.market_data = market_data
        self.feature_store = feature_store
        self.event_bus = event_bus
        self.kernel = kernel
        self.logger = logger or logging.getLogger("epip.replay")
        self._deterministic = isinstance(clock, DeterministicClock) and isinstance(
            id_generator, DeterministicIdGenerator
        )
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    def create_session(
        self,
        config: ReplayConfig,
        clock: ReplayClock | None = None,
    ) -> ReplaySession:
        scheduler = ReplayScheduler(market_data=self.market_data, config=config)
        statistics = ReplayStatistics(normalize_runtime=self._deterministic)
        replay_clock = clock or ReplayClock(replay_speed=config.replay_speed)
        return ReplaySession(
            config=config,
            clock=replay_clock,
            statistics=statistics,
            scheduler=scheduler,
            id_generator=self._id_generator,
        )

    @integrity_boundary
    def run(self, session: ReplaySession) -> ReplayMetrics:
        events: list[object] = []
        transaction = ReplaySessionTransaction(session, self.feature_store)
        tracemalloc.start()
        try:
            with transaction:
                session.set_state(ReplayState.READY)
                session.statistics.mark_started()
                self.market_data.connect()
                session.clock.play()
                session.set_state(ReplayState.RUNNING)
                events.append(
                    ReplayStarted(
                        clock=self._clock,
                        id_generator=self._id_generator,
                        id=f"replay-started-{session.session_id}",
                        timestamp=session.config.start_date or "replay-start",
                        session_id=session.session_id,
                    )
                )
                session.statistics.record_event()

                while True:
                    scheduled = session.scheduler.next()
                    if scheduled is None:
                        break
                    self._process_candle(
                        session,
                        scheduled.symbol,
                        scheduled.timeframe,
                        scheduled.candle,
                        events,
                    )
                    if session.state() == ReplayState.STOPPED:
                        break

                peak_memory = tracemalloc.get_traced_memory()[1]
                session.statistics.observe_peak_memory(peak_memory)
                session.statistics.mark_finished()
                session.clock.stop()
                session.set_state(ReplayState.FINISHED)
                events.append(
                    ReplayFinished(
                        clock=self._clock,
                        id_generator=self._id_generator,
                        id=f"replay-finished-{session.session_id}",
                        timestamp=session.clock.now()
                        or (session.config.end_date or "replay-finished"),
                        session_id=session.session_id,
                    )
                )
                session.statistics.record_event()
                metrics = session.statistics.snapshot()
                transaction.commit()
        finally:
            tracemalloc.stop()
        self.event_bus.publish_many(events)
        return metrics

    def _process_candle(
        self,
        session: ReplaySession,
        symbol: str,
        timeframe: str,
        candle: Candle,
        events: list[object],
    ) -> None:
        started = perf_counter()
        events.append(
            CandleLoaded(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"candle-loaded-{candle.timestamp}",
                timestamp=candle.timestamp,
                symbol=symbol,
                timeframe=timeframe,
                candle_timestamp=candle.timestamp,
            )
        )
        session.statistics.record_event()

        feature_set = self.feature_store.build_feature_set(
            symbol,
            timeframe,
            candle.timestamp,
            payload=candle.to_dict(),
        )
        session.statistics.record_feature(len(feature_set.features))
        events.append(
            FeatureUpdated(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"feature-updated-{candle.timestamp}",
                timestamp=candle.timestamp,
                symbol=symbol,
                timeframe=timeframe,
                feature_timestamp=candle.timestamp,
                feature_count=len(feature_set.features),
            )
        )
        session.statistics.record_event()

        window = session.window_for(symbol, timeframe)
        window.append(candle)
        context = MarketContext(
            clock=self._clock,
            id_generator=self._id_generator,
            symbol=symbol,
            timeframe=timeframe,
            timestamp=candle.timestamp,
            candles=tuple(window),
            metadata={"features": feature_set.to_dict()},
        )
        session.set_context(context)
        events.append(
            ContextUpdated(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"context-updated-{candle.timestamp}",
                timestamp=candle.timestamp,
                symbol=symbol,
                timeframe=timeframe,
                context_timestamp=candle.timestamp,
            )
        )
        session.statistics.record_event()

        session.clock.advance(candle.timestamp)
        if self.kernel is not None and len(window) >= max(1, session.config.warmup_bars):
            result = self.kernel.run(context)
            evidence_count = len(result.evidence)
            if evidence_count:
                session.statistics.record_event(evidence_count)

        events.append(
            CandleProcessed(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"candle-processed-{candle.timestamp}",
                timestamp=candle.timestamp,
                symbol=symbol,
                timeframe=timeframe,
                candle_timestamp=candle.timestamp,
            )
        )
        session.statistics.record_event()
        session.statistics.record_candle(perf_counter() - started)
