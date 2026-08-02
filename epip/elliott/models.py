"""Immutable EPIP-011 Elliott Wave domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class WaveDegree(StrEnum):
    GRAND_SUPERCYCLE = "GRAND_SUPERCYCLE"
    SUPERCYCLE = "SUPERCYCLE"
    CYCLE = "CYCLE"
    PRIMARY = "PRIMARY"
    INTERMEDIATE = "INTERMEDIATE"
    MINOR = "MINOR"
    MINUTE = "MINUTE"
    MINUETTE = "MINUETTE"
    SUBMINUETTE = "SUBMINUETTE"


class WaveLabel(StrEnum):
    IMPULSE = "IMPULSE"
    WAVE_1 = "1"
    WAVE_2 = "2"
    WAVE_3 = "3"
    WAVE_4 = "4"
    WAVE_5 = "5"
    CORRECTIVE = "CORRECTIVE"
    A = "A"
    B = "B"
    C = "C"
    DIAGONAL = "DIAGONAL"
    LEADING = "LEADING"
    ENDING = "ENDING"
    TRIANGLE = "TRIANGLE"
    FLAT = "FLAT"
    ZIGZAG = "ZIGZAG"
    COMBINATION = "COMBINATION"


class WavePattern(StrEnum):
    IMPULSE = "IMPULSE"
    ABC = "ABC"
    FLAT = "FLAT"
    ZIGZAG = "ZIGZAG"
    TRIANGLE = "TRIANGLE"
    DIAGONAL = "DIAGONAL"
    COMBINATION = "COMBINATION"
    UNKNOWN = "UNKNOWN"


class WaveQuality(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class CountStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    ALTERNATE = "ALTERNATE"


@dataclass(frozen=True, slots=True)
class Wave:
    label: WaveLabel
    degree: WaveDegree
    start_index: int
    end_index: int
    start_timestamp: str
    end_timestamp: str
    start_price: float
    end_price: float
    direction: str

    @property
    def length(self) -> float:
        return abs(self.end_price - self.start_price)


@dataclass(frozen=True, slots=True)
class WaveSequence:
    waves: tuple[Wave, ...]
    pattern: WavePattern
    degree: WaveDegree


@dataclass(frozen=True, slots=True)
class WaveViolation:
    rule_id: str
    message: str
    wave_label: WaveLabel | None = None


@dataclass(frozen=True, slots=True)
class WaveRule:
    rule_id: str
    description: str
    configurable: bool = False


@dataclass(frozen=True, slots=True)
class WaveTarget:
    label: WaveLabel
    price: float
    low: float
    high: float
    probability: float


@dataclass(frozen=True, slots=True)
class WaveProjection:
    next_wave: WaveLabel
    expected_retracement: float
    targets: tuple[WaveTarget, ...]
    confluence: float


@dataclass(frozen=True, slots=True)
class WaveCount:
    count_id: str
    sequence: WaveSequence
    violations: tuple[WaveViolation, ...]
    confidence: float
    probability: float
    quality: WaveQuality
    confluence: float
    status: CountStatus


@dataclass(frozen=True, slots=True)
class AlternateCount:
    count: WaveCount
    rationale: str


@dataclass(frozen=True, slots=True)
class ElliottAnalysis:
    primary: WaveCount
    alternates: tuple[AlternateCount, ...]
    projection: WaveProjection | None


@dataclass(frozen=True, slots=True)
class WaveSnapshot:
    timestamp: str
    symbol: str
    timeframe: str
    version: int
    context_version: int
    analysis: ElliottAnalysis
    engine_version: str = "EPIP-011"

    def to_dict(self) -> dict[str, Any]:
        from epip.elliott.serialization import to_dict

        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaveSnapshot:
        from epip.elliott.serialization import from_dict

        return from_dict(data)

    def to_json(self) -> str:
        from epip.elliott.serialization import to_json

        return to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> WaveSnapshot:
        from epip.elliott.serialization import from_json

        return from_json(payload)
