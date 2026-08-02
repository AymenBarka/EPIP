"""Public protocol for Market Structure Engine."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from epip.market_structure.history import StructureHistory
from epip.market_structure.metrics import MarketStructureMetrics
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence

InputT = TypeVar("InputT", contravariant=True)  # noqa: PLC0105 - public compatibility
OutputT = TypeVar("OutputT", covariant=True)  # noqa: PLC0105 - public compatibility


@runtime_checkable
class StructureDetectorProtocol(Protocol[InputT, OutputT]):
    """Pluggable detector protocol for EPIP-007 and future modules."""

    def detect(self, data: InputT, *args: object, **kwargs: object) -> OutputT:
        """Analyze input payload and return detector-specific result."""


class MarketStructureProtocol(Protocol):
    """Stable public API for structure inference."""

    def process_sequence(self, sequence: SwingSequence) -> MarketStructureSnapshot:
        """Process one full swing sequence and return latest snapshot."""

    def snapshot(self, symbol: str, timeframe: str) -> MarketStructureSnapshot | None:
        """Get latest structure snapshot for one stream."""

    def metrics(self) -> MarketStructureMetrics:
        """Get runtime metrics."""

    def history(self, symbol: str, timeframe: str) -> StructureHistory:
        """Get immutable chronological history for one stream."""

    def reset(self, symbol: str, timeframe: str) -> None:
        """Reset structure state for one stream."""
