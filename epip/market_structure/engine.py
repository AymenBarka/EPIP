"""Thread-safe Market Structure Engine consuming swing sequences only."""

from __future__ import annotations

import logging
import tracemalloc
from threading import RLock

from epip.core.event_bus import EventBus
from epip.market_structure.analyzer import AnalyzerResult, MarketStructureAnalyzer
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.events import (
    BOSDetected,
    CHOCHDetected,
    RangeDetected,
    StructureDetected,
    StructureReset,
    TrendChanged,
)
from epip.market_structure.exceptions import InvalidStructureInputError
from epip.market_structure.history import StructureHistory
from epip.market_structure.metrics import MarketStructureMetrics
from epip.market_structure.models import (
    MarketStructureSnapshot,
    StructureState,
    Trend,
    TrendDirection,
)
from epip.market_structure.observers import ObserverRegistry
from epip.market_structure.statistics import MarketStructureStatistics
from epip.market_structure.validators import SwingSequenceValidator
from epip.swing.models import SwingSequence


class MarketStructureEngine:
    """Official EPIP-007 source for trend/BOS/CHOCH/range structure states."""

    def __init__(
        self,
        *,
        config: MarketStructureConfig,
        event_bus: EventBus,
        logger: logging.Logger | None = None,
        observer_registry: ObserverRegistry | None = None,
    ) -> None:
        self._config = config
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger("epip.market_structure.engine")
        self._validator = SwingSequenceValidator()
        self._analyzer = MarketStructureAnalyzer(config)
        self._statistics = MarketStructureStatistics()
        self._observer_registry = observer_registry
        self._structures: dict[tuple[str, str], MarketStructureSnapshot] = {}
        self._histories: dict[tuple[str, str], StructureHistory] = {}
        self._emitted_event_ids: set[str] = set()
        self._lock = RLock()

    def process_sequence(self, sequence: SwingSequence) -> MarketStructureSnapshot:
        """Process one swing sequence deterministically and publish structure events."""
        if not self._validator.validate(sequence, self._config.minimum_swings):
            self._statistics.record_invalid_structure()
            raise InvalidStructureInputError("invalid or insufficient swing sequence")

        key = (sequence.symbol, sequence.timeframe)
        with self._lock:
            previous = self._structures.get(key)
            current_trend = (
                previous.structure.trend
                if previous is not None
                else Trend(
                    direction=TrendDirection.UNKNOWN,
                    since_index=0,
                    since_timestamp=(
                        sequence.swings[0].point.timestamp
                        if sequence.swings
                        else "market-structure-init"
                    ),
                    last_updated_timestamp=(
                        sequence.swings[0].point.timestamp
                        if sequence.swings
                        else "market-structure-init"
                    ),
                )
            )
            current_state = (
                previous.structure.state if previous is not None else StructureState.UNKNOWN
            )

            self._statistics.mark_started()
            tracemalloc.start()
            try:
                result = self._analyzer.analyze(
                    sequence,
                    current_trend=current_trend,
                    current_state=current_state,
                    statistics=self._statistics,
                )
            finally:
                peak_memory = tracemalloc.get_traced_memory()[1]
                tracemalloc.stop()
                self._statistics.observe_peak_memory(peak_memory)
                self._statistics.record_processed_swings(len(sequence.swings))
                self._statistics.mark_finished()

            if result.previous_trend != result.structure.trend.direction:
                self._statistics.record_trend_change()

            snapshot = MarketStructureSnapshot(
                timestamp=sequence.swings[-1].point.timestamp,
                structure=result.structure,
                version=previous.version + 1 if previous is not None else 1,
                symbol=sequence.symbol,
                timeframe=sequence.timeframe,
                trend=result.structure.trend,
                confidence=result.structure.confidence,
                quality=result.structure.quality,
                current_bos=result.bos,
                current_choch=result.choch,
                current_range=result.range_regime,
            )
            self._structures[key] = snapshot
            history = self._histories.get(key, StructureHistory()).append(snapshot)
            self._histories[key] = history
            self._publish(result=result, snapshot=snapshot)
            if self._observer_registry is not None:
                self._observer_registry.notify(snapshot)
            return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> MarketStructureSnapshot | None:
        key = (symbol, timeframe)
        with self._lock:
            return self._structures.get(key)

    def metrics(self) -> MarketStructureMetrics:
        return self._statistics.snapshot_metrics()

    def history(self, symbol: str, timeframe: str) -> StructureHistory:
        """Return an immutable chronological history for one stream."""
        key = (symbol, timeframe)
        with self._lock:
            return self._histories.get(key, StructureHistory())

    def reset(self, symbol: str, timeframe: str) -> None:
        key = (symbol, timeframe)
        with self._lock:
            self._structures.pop(key, None)
            self._histories.pop(key, None)
        self._emit_once(
            StructureReset(
                id=f"structure-reset-{symbol}-{timeframe}",
                timestamp="structure-reset",
                symbol=symbol,
                timeframe=timeframe,
            )
        )

    def _publish(self, *, result: AnalyzerResult, snapshot: MarketStructureSnapshot) -> None:
        structure = snapshot.structure
        self._emit_once(
            StructureDetected(
                id=f"structure-detected-{structure.symbol}-{structure.timeframe}-{snapshot.timestamp}",
                timestamp=snapshot.timestamp,
                symbol=structure.symbol,
                timeframe=structure.timeframe,
                trend=structure.trend.direction,
                state=structure.state,
            )
        )

        if result.bos is not None:
            bos = result.bos
            self._emit_once(
                BOSDetected(
                    id=f"bos-detected-{bos.symbol}-{bos.timeframe}-{bos.timestamp}",
                    timestamp=bos.timestamp,
                    symbol=bos.symbol,
                    timeframe=bos.timeframe,
                    direction=bos.direction,
                    break_price=bos.break_price,
                    reference_price=bos.reference_price,
                )
            )

        if result.choch is not None:
            choch = result.choch
            self._emit_once(
                CHOCHDetected(
                    id=f"choch-detected-{choch.symbol}-{choch.timeframe}-{choch.timestamp}",
                    timestamp=choch.timestamp,
                    symbol=choch.symbol,
                    timeframe=choch.timeframe,
                    previous_trend=choch.previous_trend,
                    new_trend=choch.new_trend,
                )
            )

        if result.range_regime is not None:
            range_regime = result.range_regime
            self._emit_once(
                RangeDetected(
                    id=(
                        f"range-detected-{range_regime.symbol}-"
                        f"{range_regime.timeframe}-{snapshot.timestamp}"
                    ),
                    timestamp=snapshot.timestamp,
                    symbol=range_regime.symbol,
                    timeframe=range_regime.timeframe,
                    range_high=range_regime.range_high,
                    range_low=range_regime.range_low,
                    touches_high=range_regime.touches_high,
                    touches_low=range_regime.touches_low,
                )
            )

        previous_trend = result.previous_trend
        if previous_trend != structure.trend.direction:
            self._emit_once(
                TrendChanged(
                    id=(
                        f"trend-changed-{structure.symbol}-"
                        f"{structure.timeframe}-{snapshot.timestamp}"
                    ),
                    timestamp=snapshot.timestamp,
                    symbol=structure.symbol,
                    timeframe=structure.timeframe,
                    previous_trend=previous_trend,
                    new_trend=structure.trend.direction,
                )
            )

        self._logger.debug(
            "structure processed symbol=%s timeframe=%s trend=%s state=%s",
            structure.symbol,
            structure.timeframe,
            structure.trend.direction,
            structure.state,
        )

    def _emit_once(self, event: object) -> None:
        event_id = getattr(event, "id", "")
        if isinstance(event_id, str) and event_id:
            if event_id in self._emitted_event_ids:
                self._statistics.record_duplicate_event()
                return
            self._emitted_event_ids.add(event_id)
        self._event_bus.publish(event)
