"""Composable swing filters."""

from __future__ import annotations

from dataclasses import dataclass

from epip.swing.config import SwingConfig
from epip.swing.models import Swing, SwingSequence
from epip.swing.protocols import SwingFilterProtocol
from epip.swing.types import SwingClassification


@dataclass(frozen=True, slots=True)
class DistanceFilter(SwingFilterProtocol):
    """Require a minimum candle distance from previous swing."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        if not sequence.swings:
            return True
        return candidate.distance_from_previous >= config.minimum_distance


@dataclass(frozen=True, slots=True)
class ATRFilter(SwingFilterProtocol):
    """Require move to exceed configured ATR floor proxy."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        if config.minimum_atr <= 0.0:
            return True
        return abs(candidate.price_move_from_previous) >= config.minimum_atr


@dataclass(frozen=True, slots=True)
class NoiseFilter(SwingFilterProtocol):
    """Reject tiny, ultra-short oscillations."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        if not sequence.swings:
            return True
        return not (
            candidate.distance_from_previous <= 1 and abs(candidate.price_move_from_previous) == 0.0
        )


@dataclass(frozen=True, slots=True)
class DuplicateFilter(SwingFilterProtocol):
    """Avoid exact duplicate swing timestamps."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        for swing in reversed(sequence.swings):
            if swing.point.timestamp == candidate.point.timestamp:
                return False
            if swing.point.index < candidate.point.index - 3:
                break
        return True


@dataclass(frozen=True, slots=True)
class TrendFilter(SwingFilterProtocol):
    """Optionally keep only swings aligned with desired trend bias."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        bias = config.trend_bias.upper()
        if bias == "NEUTRAL":
            return True
        if bias == "UP":
            return candidate.classification in (
                SwingClassification.HIGHER_HIGH,
                SwingClassification.HIGHER_LOW,
                SwingClassification.SWING_HIGH,
                SwingClassification.SWING_LOW,
            )
        if bias == "DOWN":
            return candidate.classification in (
                SwingClassification.LOWER_HIGH,
                SwingClassification.LOWER_LOW,
                SwingClassification.SWING_HIGH,
                SwingClassification.SWING_LOW,
            )
        return True


@dataclass(frozen=True, slots=True)
class MinimumMoveFilter(SwingFilterProtocol):
    """Require absolute move from previous swing above threshold."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        if not sequence.swings:
            return True
        return abs(candidate.price_move_from_previous) >= config.minimum_price_move


@dataclass(frozen=True, slots=True)
class CompositeSwingFilter(SwingFilterProtocol):
    """Combines multiple filters with logical AND."""

    filters: tuple[SwingFilterProtocol, ...]

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        return all(flt.allow(candidate, sequence, config) for flt in self.filters)


def build_default_filters() -> CompositeSwingFilter:
    """Default filter chain for EPIP-006 official pipeline."""

    return CompositeSwingFilter(
        filters=(
            DistanceFilter(),
            ATRFilter(),
            NoiseFilter(),
            DuplicateFilter(),
            TrendFilter(),
            MinimumMoveFilter(),
        )
    )
