"""Swing Engine orchestrating streaming detection and event publication."""

from __future__ import annotations

import logging
import tracemalloc
from collections.abc import Iterable
from threading import RLock

from epip.core.candle import Candle
from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import integrity_boundary
from epip.swing.config import SwingConfig
from epip.swing.detector import SwingDetector
from epip.swing.events import SwingConfirmed, SwingDetected, SwingUpdated
from epip.swing.metrics import SwingMetrics
from epip.swing.models import Swing
from epip.swing.statistics import SwingStatisticsCollector
from epip.swing.types import SwingClassification


class SwingEngine:
    """Official EPIP-006 source of swings for all downstream engines."""

    def __init__(
        self,
        *,
        config: SwingConfig,
        event_bus: EventBus,
        detector: SwingDetector | None = None,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self._config = config
        self._event_bus = event_bus
        self._detector = detector or SwingDetector(config=config)
        self._logger = logger or logging.getLogger("epip.swing.engine")
        self._statistics = SwingStatisticsCollector()
        self._lock = RLock()
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    @integrity_boundary
    def process_candle(self, candle: Candle) -> tuple[Swing, ...]:
        """Process one candle and emit swing events."""
        with self._lock:
            checkpoint = self._detector._checkpoint()
            try:
                swings = self._detector.process(candle)
                for swing in swings:
                    self._statistics.record_swing(
                        classification=swing.classification,
                        distance_from_previous=swing.distance_from_previous,
                        duration_bars=swing.distance_from_previous,
                        detection_latency_bars=swing.detection_latency_bars,
                    )
            except BaseException:
                self._detector._restore(checkpoint)
                raise
        for swing in swings:
            self._publish_swing_events(swing)
        return swings

    def run(self, candles: Iterable[Candle]) -> SwingMetrics:
        """Run full swing detection on a candle stream."""
        self._statistics.mark_started()
        tracemalloc.start()
        try:
            for candle in candles:
                self.process_candle(candle)
        finally:
            peak_memory = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            self._statistics.observe_peak_memory(peak_memory)
            self._statistics.mark_finished()
        metrics = self._statistics.snapshot_metrics()
        self._logger.info(
            "swing-run complete swings=%d rate=%.2f/s",
            metrics.swings_count,
            metrics.swings_per_second,
        )
        return metrics

    def sequence(self, symbol: str, timeframe: str) -> tuple[Swing, ...]:
        return self._detector.sequence(symbol, timeframe).swings

    def _publish_swing_events(self, swing: Swing) -> None:
        self._event_bus.publish(
            SwingDetected(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"swing-detected-{swing.point.timestamp}",
                timestamp=swing.point.timestamp,
                symbol=swing.point.symbol,
                timeframe=swing.point.timeframe,
                swing_timestamp=swing.point.timestamp,
                classification=swing.classification,
                scope=swing.scope,
                price=swing.point.price,
            )
        )
        if swing.classification in (SwingClassification.EQUAL_HIGH, SwingClassification.EQUAL_LOW):
            self._event_bus.publish(
                SwingUpdated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"swing-updated-{swing.point.timestamp}",
                    timestamp=swing.point.timestamp,
                    symbol=swing.point.symbol,
                    timeframe=swing.point.timeframe,
                    swing_timestamp=swing.point.timestamp,
                    classification=swing.classification,
                    price=swing.point.price,
                )
            )
        self._event_bus.publish(
            SwingConfirmed(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"swing-confirmed-{swing.point.timestamp}",
                timestamp=swing.point.timestamp,
                symbol=swing.point.symbol,
                timeframe=swing.point.timeframe,
                swing_timestamp=swing.point.timestamp,
                classification=swing.classification,
            )
        )
