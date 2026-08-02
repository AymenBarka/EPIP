"""
EPIP Core Types

Author : EPIP Project
License : MIT

This module defines every common enumeration and type shared by the
whole EPIP framework.

No business logic must exist here.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, TypeAlias

###############################################################################
# CONSTANTS
###############################################################################

FRAMEWORK_NAME: Final[str] = "EPIP"

FRAMEWORK_VERSION: Final[str] = "0.1.0-alpha"

###############################################################################
# ENUMS
###############################################################################


class Direction(StrEnum):
    """
    Trading direction.
    """

    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class DecisionType(StrEnum):
    """
    Final decision produced by the Decision Engine.
    """

    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


class EvidenceStrength(StrEnum):
    """
    Qualitative confidence.
    """

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ScenarioType(StrEnum):
    """
    Market scenario.
    """

    CONTINUATION = "CONTINUATION"
    REVERSAL = "REVERSAL"
    BREAKOUT = "BREAKOUT"
    RANGE = "RANGE"
    UNKNOWN = "UNKNOWN"


class MarketRegime(StrEnum):
    """
    Market environment.
    """

    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


class Timeframe(StrEnum):
    """
    Supported market timeframes.
    """

    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"

    H1 = "H1"
    H4 = "H4"

    D1 = "D1"

    W1 = "W1"


class DataSource(StrEnum):
    """
    Candle providers.
    """

    TWELVE_DATA = "TWELVE_DATA"
    CSV = "CSV"
    MT5 = "MT5"


class PluginState(StrEnum):
    """
    Plugin execution status.
    """

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


###############################################################################
# TYPE ALIASES
###############################################################################

Price: TypeAlias = float

Volume: TypeAlias = float

Confidence: TypeAlias = float

Probability: TypeAlias = float

Symbol: TypeAlias = str

Timestamp: TypeAlias = str
