"""Common swing-domain enumerations and aliases."""

from __future__ import annotations

from enum import StrEnum
from typing import TypeAlias


class PivotType(StrEnum):
    """Pivot polarity."""

    HIGH = "HIGH"
    LOW = "LOW"


class SwingClassification(StrEnum):
    """Swing semantic labels consumed by downstream engines."""

    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"
    HIGHER_HIGH = "HIGHER_HIGH"
    HIGHER_LOW = "HIGHER_LOW"
    LOWER_HIGH = "LOWER_HIGH"
    LOWER_LOW = "LOWER_LOW"
    EQUAL_HIGH = "EQUAL_HIGH"
    EQUAL_LOW = "EQUAL_LOW"


class SwingScope(StrEnum):
    """Swing hierarchy level."""

    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class TrendBias(StrEnum):
    """Optional trend filter direction."""

    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


SwingKey: TypeAlias = tuple[str, str]
Price: TypeAlias = float
