"""Concrete pivot-window strategy for streaming swing detection."""

from __future__ import annotations

from collections import deque

from epip.core.candle import Candle
from epip.swing.config import SwingConfig
from epip.swing.models import SwingPoint
from epip.swing.types import PivotType


class PivotWindowStrategy:
    """Confirms pivots after `right_bars` candles in a rolling window."""

    def __init__(self, config: SwingConfig) -> None:
        self._config = config
        self._candles: deque[Candle] = deque()
        self._index_of_first = 0
        self._current_index = -1

    def on_candle(self, candle: Candle) -> tuple[SwingPoint, ...]:
        self._candles.append(candle)
        self._current_index += 1

        left, right = self._effective_window()
        size = left + right + 1
        if len(self._candles) < size:
            return ()

        center_pos = len(self._candles) - 1 - right
        if center_pos < left:
            return ()

        local_window = list(self._candles)[center_pos - left : center_pos + right + 1]
        center = local_window[left]
        center_high = float(center.high)
        center_low = float(center.low)

        highs = [float(item.high) for item in local_window]
        lows = [float(item.low) for item in local_window]

        result: list[SwingPoint] = []
        absolute_index = self._index_of_first + center_pos

        if center_high >= max(highs):
            result.append(
                SwingPoint(
                    symbol=center.symbol,
                    timeframe=center.timeframe,
                    index=absolute_index,
                    timestamp=center.timestamp,
                    price=center_high,
                    pivot_type=PivotType.HIGH,
                    left_bars=left,
                    right_bars=right,
                    confirmed=True,
                )
            )

        if center_low <= min(lows):
            result.append(
                SwingPoint(
                    symbol=center.symbol,
                    timeframe=center.timeframe,
                    index=absolute_index,
                    timestamp=center.timestamp,
                    price=center_low,
                    pivot_type=PivotType.LOW,
                    left_bars=left,
                    right_bars=right,
                    confirmed=True,
                )
            )

        self._shrink_buffer(left, right)
        return tuple(result)

    def _effective_window(self) -> tuple[int, int]:
        if not self._config.adaptive_window or len(self._candles) < self._config.atr_period:
            return (self._config.left_bars, self._config.right_bars)

        recent = list(self._candles)[-self._config.atr_period :]
        average_range = sum(float(item.high) - float(item.low) for item in recent) / len(recent)
        if average_range <= self._config.minimum_atr:
            return (self._config.left_bars, self._config.right_bars)

        return (self._config.left_bars + 1, self._config.right_bars + 1)

    def _shrink_buffer(self, left: int, right: int) -> None:
        max_size = (left + right + 1) * 4
        while len(self._candles) > max_size:
            self._candles.popleft()
            self._index_of_first += 1
