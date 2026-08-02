"""Protocols defining swing strategy and filter extension points."""

from __future__ import annotations

from typing import Protocol

from epip.core.candle import Candle
from epip.swing.config import SwingConfig
from epip.swing.models import Swing, SwingPoint, SwingSequence


class PivotStrategyProtocol(Protocol):
    """Streaming strategy producing confirmed pivot candidates."""

    def on_candle(self, candle: Candle) -> tuple[SwingPoint, ...]:
        """Push one candle and return zero-to-many newly confirmed pivots."""


class SwingFilterProtocol(Protocol):
    """Filter that decides whether a swing candidate is accepted."""

    def allow(self, candidate: Swing, sequence: SwingSequence, config: SwingConfig) -> bool:
        """Return True if candidate should be kept."""
