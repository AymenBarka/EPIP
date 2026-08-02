"""Structure analyzer orchestrating trend, BOS, CHOCH and range detection."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from epip.market_structure.bos_detector import BOSDetector
from epip.market_structure.choch_detector import CHOCHDetector
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.exceptions import IllegalStructureTransitionError
from epip.market_structure.models import (
    BreakOfStructure,
    ChangeOfCharacter,
    MarketStructure,
    Range,
    StructureQuality,
    StructureState,
    Trend,
    TrendDirection,
)
from epip.market_structure.range_detector import RangeDetector
from epip.market_structure.state_machine import StructureStateMachine
from epip.market_structure.statistics import MarketStructureStatistics
from epip.market_structure.trend_detector import TrendDetector
from epip.market_structure.validators import BOSValidator, CHOCHValidator, TrendValidator
from epip.swing.models import SwingSequence
from epip.swing.types import SwingClassification


@dataclass(frozen=True, slots=True)
class AnalyzerResult:
    structure: MarketStructure
    bos: BreakOfStructure | None
    choch: ChangeOfCharacter | None
    range_regime: Range | None
    previous_trend: TrendDirection
    previous_state: StructureState


class MarketStructureAnalyzer:
    """Deterministic analyzer for one swing sequence snapshot."""

    def __init__(self, config: MarketStructureConfig) -> None:
        self._config = config
        self._trend_detector = TrendDetector()
        self._bos_detector = BOSDetector()
        self._choch_detector = CHOCHDetector()
        self._range_detector = RangeDetector()
        self._trend_validator = TrendValidator()
        self._bos_validator = BOSValidator()
        self._choch_validator = CHOCHValidator()
        self._state_machine = StructureStateMachine()

    def analyze(
        self,
        sequence: SwingSequence,
        *,
        current_trend: Trend,
        current_state: StructureState,
        statistics: MarketStructureStatistics,
    ) -> AnalyzerResult:
        previous_direction = current_trend.direction
        previous_state = current_state
        detected_direction = self._trend_detector.detect(sequence)
        if detected_direction == TrendDirection.UNKNOWN:
            detected_direction = previous_direction

        origin_swing = sequence.swings[-2] if len(sequence.swings) >= 2 else None
        destination_swing = sequence.swings[-1] if sequence.swings else None

        trend = Trend(
            direction=detected_direction,
            since_index=(
                sequence.swings[-1].point.index if sequence.swings else current_trend.since_index
            ),
            since_timestamp=(
                sequence.swings[-1].point.timestamp
                if sequence.swings
                else current_trend.since_timestamp
            ),
            last_updated_timestamp=(
                sequence.swings[-1].point.timestamp
                if sequence.swings
                else current_trend.last_updated_timestamp
            ),
            origin_swing=origin_swing,
            destination_swing=destination_swing,
        )
        if not self._trend_validator.validate(trend):
            trend = current_trend

        bos_start = perf_counter()
        bos = self._bos_detector.detect(sequence, trend=trend.direction, config=self._config)
        statistics.record_detection_time(perf_counter() - bos_start)
        if bos is not None and self._bos_validator.validate(bos):
            statistics.record_bos(perf_counter() - bos_start)
        else:
            if self._bos_detector.last_duplicate:
                statistics.record_duplicate_event()
            elif bos is not None:
                statistics.record_false_bos()
            bos = None

        choch_start = perf_counter()
        choch = self._choch_detector.detect(
            sequence,
            previous_trend=previous_direction,
            config=self._config,
        )
        statistics.record_detection_time(perf_counter() - choch_start)
        if choch is not None and self._choch_validator.validate(choch):
            statistics.record_choch(perf_counter() - choch_start)
            if choch.new_trend != trend.direction:
                trend = Trend(
                    direction=choch.new_trend,
                    since_index=choch.swing_index,
                    since_timestamp=choch.timestamp,
                    last_updated_timestamp=choch.timestamp,
                    origin_swing=choch.origin_swing,
                    destination_swing=choch.destination_swing,
                )
        else:
            if self._choch_detector.last_duplicate:
                statistics.record_duplicate_event()
            elif choch is not None:
                statistics.record_false_choch()
            choch = None

        range_regime = self._range_detector.detect(sequence, self._config)
        if range_regime is not None:
            statistics.record_range()

        desired_state = self._desired_state(
            current_state=current_state,
            trend=trend.direction,
            choch=choch,
            has_range=(range_regime is not None),
        )
        try:
            state = self._state_machine.transition(current_state, desired_state)
        except IllegalStructureTransitionError:
            statistics.record_invalid_structure()
            raise

        confidence = self._compute_confidence(sequence, trend.direction, bos, choch, range_regime)
        quality = self._quality_from_confidence(confidence)

        structure = MarketStructure(
            symbol=sequence.symbol,
            timeframe=sequence.timeframe,
            trend=trend,
            state=state,
            last_bos=bos,
            last_choch=choch,
            active_range=range_regime,
            processed_swings=len(sequence.swings),
            confidence=confidence,
            quality=quality,
        )

        return AnalyzerResult(
            structure=structure,
            bos=bos,
            choch=choch,
            range_regime=range_regime,
            previous_trend=previous_direction,
            previous_state=previous_state,
        )

    def _desired_state(
        self,
        *,
        current_state: StructureState,
        trend: TrendDirection,
        choch: ChangeOfCharacter | None,
        has_range: bool,
    ) -> StructureState:
        if has_range or trend == TrendDirection.RANGE:
            return StructureState.RANGE
        if choch is not None:
            if (
                choch.new_trend == TrendDirection.UPTREND
                and current_state == StructureState.DOWNTREND
            ):
                return StructureState.ACCUMULATION
            if (
                choch.new_trend == TrendDirection.DOWNTREND
                and current_state == StructureState.UPTREND
            ):
                return StructureState.DISTRIBUTION
        if trend == TrendDirection.UPTREND:
            if current_state in (StructureState.UNKNOWN, StructureState.RANGE):
                return StructureState.ACCUMULATION
            if current_state == StructureState.ACCUMULATION:
                return StructureState.UPTREND
            return StructureState.UPTREND
        if trend == TrendDirection.DOWNTREND:
            if current_state in (StructureState.UNKNOWN, StructureState.RANGE):
                return StructureState.DISTRIBUTION
            if current_state == StructureState.DISTRIBUTION:
                return StructureState.DOWNTREND
            return StructureState.DOWNTREND
        return StructureState.UNKNOWN

    def _compute_confidence(
        self,
        sequence: SwingSequence,
        trend: TrendDirection,
        bos: BreakOfStructure | None,
        choch: ChangeOfCharacter | None,
        range_regime: Range | None,
    ) -> float:
        swings = sequence.swings
        confirmations = 0
        if bos is not None:
            confirmations += 1
        if choch is not None:
            confirmations += 1
        if range_regime is not None:
            confirmations += 1
        confirmation_score = min(1.0, confirmations / 3.0)

        if not swings:
            return 0.0

        average_distance = sum(item.distance_from_previous for item in swings[-5:]) / min(
            5, len(swings)
        )
        distance_score = min(1.0, average_distance / max(1.0, float(self._config.minimum_swings)))

        relevant: tuple[SwingClassification, ...]
        if trend == TrendDirection.UPTREND:
            relevant = (SwingClassification.HIGHER_HIGH, SwingClassification.HIGHER_LOW)
        elif trend == TrendDirection.DOWNTREND:
            relevant = (SwingClassification.LOWER_HIGH, SwingClassification.LOWER_LOW)
        elif trend == TrendDirection.RANGE:
            relevant = (SwingClassification.EQUAL_HIGH, SwingClassification.EQUAL_LOW)
        else:
            relevant = ()
        consistency_hits = sum(1 for item in swings[-6:] if item.classification in relevant)
        consistency_score = consistency_hits / min(6, len(swings)) if swings else 0.0

        equals = sum(
            1
            for item in swings[-6:]
            if item.classification
            in (SwingClassification.EQUAL_HIGH, SwingClassification.EQUAL_LOW)
        )
        equal_ratio = equals / min(6, len(swings))
        equal_component = 1.0 - equal_ratio

        confidence = (
            0.35 * confirmation_score
            + 0.25 * distance_score
            + 0.30 * consistency_score
            + 0.10 * equal_component
        )
        return max(0.0, min(1.0, confidence))

    def _quality_from_confidence(self, confidence: float) -> StructureQuality:
        if confidence < 0.35:
            return StructureQuality.LOW
        if confidence < 0.60:
            return StructureQuality.MEDIUM
        if confidence < 0.80:
            return StructureQuality.HIGH
        return StructureQuality.VERY_HIGH
