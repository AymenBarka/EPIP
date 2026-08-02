"""Validation layer for EPIP-007 market structure inputs and outputs."""

from __future__ import annotations

from epip.market_structure.models import BreakOfStructure, ChangeOfCharacter, Trend, TrendDirection
from epip.swing.models import SwingSequence


class SwingSequenceValidator:
    """Ensures a swing sequence is processable."""

    def validate(self, sequence: SwingSequence, minimum_swings: int) -> bool:
        if not sequence.symbol or not sequence.timeframe:
            return False
        return not len(sequence.swings) < minimum_swings


class TrendValidator:
    """Ensures trend objects remain coherent."""

    def validate(self, trend: Trend) -> bool:
        if trend.direction not in (
            TrendDirection.UPTREND,
            TrendDirection.DOWNTREND,
            TrendDirection.RANGE,
            TrendDirection.UNKNOWN,
        ):
            return False
        return trend.since_index >= 0


class BOSValidator:
    """Ensures BOS objects are structurally valid."""

    def validate(self, bos: BreakOfStructure) -> bool:
        if bos.swing_index < 0:
            return False
        if bos.direction not in (TrendDirection.UPTREND, TrendDirection.DOWNTREND):
            return False
        return bos.break_price != bos.reference_price


class CHOCHValidator:
    """Ensures CHOCH objects are structurally valid."""

    def validate(self, choch: ChangeOfCharacter) -> bool:
        if choch.swing_index < 0:
            return False
        if choch.previous_trend == choch.new_trend:
            return False
        if choch.previous_trend == TrendDirection.UNKNOWN:
            return False
        return choch.new_trend in (TrendDirection.UPTREND, TrendDirection.DOWNTREND)
