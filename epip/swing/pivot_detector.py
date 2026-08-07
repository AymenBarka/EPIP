"""Strategy declarations for pivot detection."""

from __future__ import annotations

from epip.core.candle import Candle
from epip.swing.config import SwingConfig
from epip.swing.models import SwingPoint
from epip.swing.pivot_window_detector import PivotWindowStrategy


class FractalStrategy:
    """Placeholder strategy for fractal-based pivots."""

    def __init__(self, config: SwingConfig) -> None:
        self._config = config

    def on_candle(self, candle: Candle) -> tuple[SwingPoint, ...]:
        raise NotImplementedError("FractalStrategy is not implemented yet")


class ATRAdaptiveStrategy:
    """Placeholder strategy for ATR-adaptive pivots."""

    def __init__(self, config: SwingConfig) -> None:
        self._config = config

    def on_candle(self, candle: Candle) -> tuple[SwingPoint, ...]:
        raise NotImplementedError("ATRAdaptiveStrategy is not implemented yet")


class ZigZagStrategy:
    """Placeholder strategy for zigzag pivots."""

    def __init__(self, config: SwingConfig) -> None:
        self._config = config

    def on_candle(self, candle: Candle) -> tuple[SwingPoint, ...]:
        raise NotImplementedError("ZigZagStrategy is not implemented yet")


class HybridStrategy:
    """Placeholder strategy for combined pivot confirmation."""

    def __init__(self, config: SwingConfig) -> None:
        self._config = config

    def on_candle(self, candle: Candle) -> tuple[SwingPoint, ...]:
        raise NotImplementedError("HybridStrategy is not implemented yet")


def create_default_strategy(config: SwingConfig) -> PivotWindowStrategy:
    """Factory for the official EPIP-006 default strategy."""

    return PivotWindowStrategy(config)
