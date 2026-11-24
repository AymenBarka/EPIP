"""Immutable research contracts of the causal Elliott prototype (P04-R01-E00).

Every fact carries the bar index and UTC instant at which it becomes known
(``available_index`` / ``available_ms``). A bar is known at its close
(``end_ms``); nothing is ever stamped earlier than the close of the bar whose
data confirmed it.

Scores are **uncalibrated research scores**. They rank candidates inside one
search and are never probabilities.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class ResearchContractError(ValueError):
    """A research input or output violates its contract (fail closed)."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ResearchContractError(message)


def _finite_positive(value: float, name: str) -> None:
    require(type(value) is float and math.isfinite(value) and value > 0.0, f"{name} invalid")


class Direction(StrEnum):
    UP = "UP"
    DOWN = "DOWN"


class PivotKind(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"


class RejectionReason(StrEnum):
    """Why an enumerated (W1 start, W1 end, W2 end) triple is not a count."""

    W1_NOT_DIRECTIONAL = "W1_NOT_DIRECTIONAL"
    W1_START_NOT_EXTREME = "W1_START_NOT_EXTREME"
    W1_END_NOT_EXTREME = "W1_END_NOT_EXTREME"
    W2_END_NOT_EXTREME = "W2_END_NOT_EXTREME"
    W2_BEYOND_W1_ORIGIN = "W2_BEYOND_W1_ORIGIN"
    DEGREE_INCONSISTENT = "DEGREE_INCONSISTENT"


class InvalidationReason(StrEnum):
    W1_ORIGIN_BREACHED = "W1_ORIGIN_BREACHED"


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """Pre-declared research parameters (never optimized on market data)."""

    atr_period: int = 14
    threshold_atr: float = 3.0
    window_pivots: int = 12
    max_alternates: int = 4
    max_degree_gap: int = 1

    def __post_init__(self) -> None:
        require(type(self.atr_period) is int and self.atr_period >= 2, "atr_period invalid")
        _finite_positive(self.threshold_atr, "threshold_atr")
        require(
            type(self.window_pivots) is int and 3 <= self.window_pivots <= 64,
            "window_pivots must be within 3..64",
        )
        require(
            type(self.max_alternates) is int and 0 <= self.max_alternates <= 16,
            "max_alternates must be within 0..16",
        )
        require(
            type(self.max_degree_gap) is int and self.max_degree_gap >= 0, "max_degree_gap invalid"
        )


@dataclass(frozen=True, slots=True)
class PriceBar:
    """One closed bar over the half-open UTC interval [start_ms, end_ms)."""

    index: int
    start_ms: int
    end_ms: int
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        require(type(self.index) is int and self.index >= 0, "bar index invalid")
        require(
            type(self.start_ms) is int and type(self.end_ms) is int and self.start_ms < self.end_ms,
            "bar interval invalid",
        )
        for name in ("open", "high", "low", "close"):
            _finite_positive(getattr(self, name), f"bar {name}")
        require(
            self.low <= min(self.open, self.close) and self.high >= max(self.open, self.close),
            "bar OHLC inconsistent",
        )


@dataclass(frozen=True, slots=True)
class Pivot:
    """A confirmed swing extreme.

    ``extreme_*`` locate the extreme; ``available_*`` locate the close of the
    bar whose data confirmed it. ``available_index > extreme_index`` always.
    """

    sequence: int
    kind: PivotKind
    price: float
    extreme_index: int
    extreme_start_ms: int
    available_index: int
    available_ms: int
    atr: float

    def __post_init__(self) -> None:
        require(type(self.sequence) is int and self.sequence >= 0, "pivot sequence invalid")
        require(type(self.kind) is PivotKind, "pivot kind invalid")
        _finite_positive(self.price, "pivot price")
        _finite_positive(self.atr, "pivot atr")
        require(
            0 <= self.extreme_index < self.available_index,
            "a pivot is never available on its extreme bar",
        )
        require(self.extreme_start_ms < self.available_ms, "pivot instants invalid")

    @property
    def latency_bars(self) -> int:
        return self.available_index - self.extreme_index


@dataclass(frozen=True, slots=True)
class CountCandidate:
    """An eligible W1/W2 count. W1 = start -> end; W2 = end -> w2_end."""

    count_id: str
    direction: Direction
    w1_start: Pivot
    w1_end: Pivot
    w2_end: Pivot
    retracement: float
    w1_atr_multiple: float
    w2_atr_multiple: float
    w1_scale: int
    w2_scale: int
    research_score: float

    def __post_init__(self) -> None:
        require(type(self.direction) is Direction, "count direction invalid")
        require(
            self.w1_start.sequence < self.w1_end.sequence < self.w2_end.sequence,
            "count pivots out of order",
        )
        require(0.0 < self.retracement < 1.0, "W2 retracement must lie strictly inside (0, 1)")
        require(0.0 <= self.research_score <= 1.0, "research score invalid")


@dataclass(frozen=True, slots=True)
class PivotConfirmed:
    available_index: int
    available_ms: int
    pivot: Pivot


@dataclass(frozen=True, slots=True)
class CountSearch:
    """Result of one bounded W1/W2 search, run when a W2-ending pivot confirms.

    ``primary`` is None when nothing is eligible (a published zero-count
    outcome, not an absence of output).
    """

    available_index: int
    available_ms: int
    direction: Direction
    w2_end_sequence: int
    window_sequences: tuple[int, ...]
    enumerated: int
    rejections: tuple[tuple[RejectionReason, int], ...]
    primary: CountCandidate | None
    alternates: tuple[CountCandidate, ...]
    eligible: int


@dataclass(frozen=True, slots=True)
class CountInvalidated:
    available_index: int
    available_ms: int
    count_id: str
    reason: InvalidationReason


Event = PivotConfirmed | CountSearch | CountInvalidated
