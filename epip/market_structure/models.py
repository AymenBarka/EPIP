"""Immutable models for EPIP-007 Market Structure Engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from epip.core.integrity import (
    RelationshipIntegrityError,
    integrity_deserializer,
    require_non_negative,
    require_text,
    require_unit_interval,
    require_version,
)
from epip.market_structure.serialization import (
    deterministic_json,
    load_json,
    swing_from_dict,
    swing_to_dict,
)
from epip.swing.models import Swing

ENGINE_VERSION = "EPIP-007"


class TrendDirection(StrEnum):
    """Direction state inferred from swing progression."""

    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    RANGE = "RANGE"
    UNKNOWN = "UNKNOWN"


class StructureState(StrEnum):
    """Explicit structure state-machine nodes."""

    UNKNOWN = "UNKNOWN"
    ACCUMULATION = "ACCUMULATION"
    UPTREND = "UPTREND"
    DISTRIBUTION = "DISTRIBUTION"
    DOWNTREND = "DOWNTREND"
    RANGE = "RANGE"
    # Backward-compatible aliases for EPIP-007 initial API.
    IDLE = "UNKNOWN"
    ACTIVE = "UPTREND"
    RANGING = "RANGE"
    RESET = "UNKNOWN"


class StructureQuality(StrEnum):
    """Quality tiers for structure reliability."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass(frozen=True, slots=True)
class Trend:
    """Trend snapshot for a stream."""

    direction: TrendDirection
    since_index: int
    since_timestamp: str
    last_updated_timestamp: str
    origin_swing: Swing | None = None
    destination_swing: Swing | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_swing": swing_to_dict(self.destination_swing),
            "direction": self.direction.value,
            "last_updated_timestamp": self.last_updated_timestamp,
            "origin_swing": swing_to_dict(self.origin_swing),
            "since_index": self.since_index,
            "since_timestamp": self.since_timestamp,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> Trend:
        return cls(
            direction=TrendDirection(str(payload["direction"])),
            since_index=int(payload["since_index"]),
            since_timestamp=str(payload["since_timestamp"]),
            last_updated_timestamp=str(payload["last_updated_timestamp"]),
            origin_swing=swing_from_dict(payload.get("origin_swing")),
            destination_swing=swing_from_dict(payload.get("destination_swing")),
        )

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> Trend:
        return cls.from_dict(load_json(payload))


@dataclass(frozen=True, slots=True)
class BreakOfStructure:
    """BOS event model."""

    symbol: str
    timeframe: str
    timestamp: str
    direction: TrendDirection
    reference_price: float
    break_price: float
    swing_index: int
    confirmed: bool
    origin_swing: Swing | None = None
    destination_swing: Swing | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "break_price": self.break_price,
            "confirmed": self.confirmed,
            "destination_swing": swing_to_dict(self.destination_swing),
            "direction": self.direction.value,
            "origin_swing": swing_to_dict(self.origin_swing),
            "reference_price": self.reference_price,
            "swing_index": self.swing_index,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> BreakOfStructure:
        return cls(
            symbol=str(payload["symbol"]),
            timeframe=str(payload["timeframe"]),
            timestamp=str(payload["timestamp"]),
            direction=TrendDirection(str(payload["direction"])),
            reference_price=float(payload["reference_price"]),
            break_price=float(payload["break_price"]),
            swing_index=int(payload["swing_index"]),
            confirmed=bool(payload["confirmed"]),
            origin_swing=swing_from_dict(payload.get("origin_swing")),
            destination_swing=swing_from_dict(payload.get("destination_swing")),
        )

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> BreakOfStructure:
        return cls.from_dict(load_json(payload))


@dataclass(frozen=True, slots=True)
class ChangeOfCharacter:
    """CHOCH event model."""

    symbol: str
    timeframe: str
    timestamp: str
    previous_trend: TrendDirection
    new_trend: TrendDirection
    trigger_price: float
    swing_index: int
    origin_swing: Swing | None = None
    destination_swing: Swing | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_swing": swing_to_dict(self.destination_swing),
            "new_trend": self.new_trend.value,
            "origin_swing": swing_to_dict(self.origin_swing),
            "previous_trend": self.previous_trend.value,
            "swing_index": self.swing_index,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "trigger_price": self.trigger_price,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> ChangeOfCharacter:
        return cls(
            symbol=str(payload["symbol"]),
            timeframe=str(payload["timeframe"]),
            timestamp=str(payload["timestamp"]),
            previous_trend=TrendDirection(str(payload["previous_trend"])),
            new_trend=TrendDirection(str(payload["new_trend"])),
            trigger_price=float(payload["trigger_price"]),
            swing_index=int(payload["swing_index"]),
            origin_swing=swing_from_dict(payload.get("origin_swing")),
            destination_swing=swing_from_dict(payload.get("destination_swing")),
        )

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> ChangeOfCharacter:
        return cls.from_dict(load_json(payload))


@dataclass(frozen=True, slots=True)
class Range:
    """Range regime model."""

    symbol: str
    timeframe: str
    start_index: int
    end_index: int
    range_high: float
    range_low: float
    touches_high: int
    touches_low: int
    active: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "end_index": self.end_index,
            "range_high": self.range_high,
            "range_low": self.range_low,
            "start_index": self.start_index,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "touches_high": self.touches_high,
            "touches_low": self.touches_low,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> Range:
        return cls(
            symbol=str(payload["symbol"]),
            timeframe=str(payload["timeframe"]),
            start_index=int(payload["start_index"]),
            end_index=int(payload["end_index"]),
            range_high=float(payload["range_high"]),
            range_low=float(payload["range_low"]),
            touches_high=int(payload["touches_high"]),
            touches_low=int(payload["touches_low"]),
            active=bool(payload["active"]),
        )

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> Range:
        return cls.from_dict(load_json(payload))


@dataclass(frozen=True, slots=True)
class MarketStructure:
    """Current inferred market structure state."""

    symbol: str
    timeframe: str
    trend: Trend
    state: StructureState
    last_bos: BreakOfStructure | None
    last_choch: ChangeOfCharacter | None
    active_range: Range | None
    processed_swings: int
    confidence: float = 0.0
    quality: StructureQuality = StructureQuality.LOW
    uuid: str = ""
    created_at: str = ""
    updated_at: str = ""
    engine_version: str = ENGINE_VERSION

    def __post_init__(self) -> None:
        created_at = self.created_at or self.trend.since_timestamp
        updated_at = self.updated_at or self.trend.last_updated_timestamp
        identity = self.uuid or str(
            uuid5(
                NAMESPACE_URL,
                f"epip:{self.symbol}:{self.timeframe}:{created_at}:{self.processed_swings}",
            )
        )
        object.__setattr__(self, "uuid", identity)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.symbol, "market_structure.symbol")
        require_text(self.timeframe, "market_structure.timeframe")
        require_non_negative(self.processed_swings, "market_structure.processed_swings")
        require_unit_interval(self.confidence, "market_structure.confidence")
        require_text(self.uuid, "market_structure.uuid")
        require_text(self.created_at, "market_structure.created_at")
        require_text(self.updated_at, "market_structure.updated_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_range": self.active_range.to_dict() if self.active_range else None,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "engine_version": self.engine_version,
            "last_bos": self.last_bos.to_dict() if self.last_bos else None,
            "last_choch": self.last_choch.to_dict() if self.last_choch else None,
            "processed_swings": self.processed_swings,
            "quality": self.quality.value,
            "state": self.state.value,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "trend": self.trend.to_dict(),
            "updated_at": self.updated_at,
            "uuid": self.uuid,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> MarketStructure:
        trend_payload = payload["trend"]
        if not isinstance(trend_payload, Mapping):
            raise TypeError("serialized trend must be a mapping")
        bos_payload, choch_payload, range_payload = (
            payload.get("last_bos"),
            payload.get("last_choch"),
            payload.get("active_range"),
        )
        return cls(
            symbol=str(payload["symbol"]),
            timeframe=str(payload["timeframe"]),
            trend=Trend.from_dict(trend_payload),
            state=StructureState(str(payload["state"])),
            last_bos=(
                BreakOfStructure.from_dict(bos_payload)
                if isinstance(bos_payload, Mapping)
                else None
            ),
            last_choch=(
                ChangeOfCharacter.from_dict(choch_payload)
                if isinstance(choch_payload, Mapping)
                else None
            ),
            active_range=(
                Range.from_dict(range_payload) if isinstance(range_payload, Mapping) else None
            ),
            processed_swings=int(payload["processed_swings"]),
            confidence=float(payload.get("confidence", 0.0)),
            quality=StructureQuality(str(payload.get("quality", StructureQuality.LOW.value))),
            uuid=str(payload.get("uuid", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            engine_version=str(payload.get("engine_version", ENGINE_VERSION)),
        )

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> MarketStructure:
        return cls.from_dict(load_json(payload))


@dataclass(frozen=True, slots=True)
class MarketStructureSnapshot:
    """Immutable published snapshot of full structure state."""

    timestamp: str
    structure: MarketStructure
    version: int = 1
    symbol: str = ""
    timeframe: str = ""
    trend: Trend | None = None
    confidence: float = 0.0
    quality: StructureQuality = StructureQuality.LOW
    current_bos: BreakOfStructure | None = None
    current_choch: ChangeOfCharacter | None = None
    current_range: Range | None = None
    created_at: str = ""
    engine_version: str = ENGINE_VERSION

    def __post_init__(self) -> None:
        symbol = self.symbol or self.structure.symbol
        timeframe = self.timeframe or self.structure.timeframe
        trend = self.trend or self.structure.trend
        confidence = self.confidence if self.confidence > 0.0 else self.structure.confidence
        quality = self.quality if self.quality != StructureQuality.LOW else self.structure.quality
        current_bos = self.current_bos if self.current_bos is not None else self.structure.last_bos
        current_choch = (
            self.current_choch if self.current_choch is not None else self.structure.last_choch
        )
        current_range = (
            self.current_range if self.current_range is not None else self.structure.active_range
        )
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "timeframe", timeframe)
        object.__setattr__(self, "trend", trend)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "quality", quality)
        object.__setattr__(self, "current_bos", current_bos)
        object.__setattr__(self, "current_choch", current_choch)
        object.__setattr__(self, "current_range", current_range)
        object.__setattr__(self, "created_at", self.created_at or self.timestamp)
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "market_structure_snapshot.timestamp")
        require_version(self.version, "market_structure_snapshot.version")
        require_text(self.symbol, "market_structure_snapshot.symbol")
        require_text(self.timeframe, "market_structure_snapshot.timeframe")
        require_unit_interval(self.confidence, "market_structure_snapshot.confidence")
        require_text(self.created_at, "market_structure_snapshot.created_at")
        require_text(self.engine_version, "market_structure_snapshot.engine_version")
        if self.symbol != self.structure.symbol or self.timeframe != self.structure.timeframe:
            raise RelationshipIntegrityError("snapshot and market structure streams differ")

    @property
    def structure_version(self) -> int:
        """Stable explicit alias used by persistence and graph consumers."""
        return self.version

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "created_at": self.created_at,
            "current_bos": self.current_bos.to_dict() if self.current_bos else None,
            "current_choch": self.current_choch.to_dict() if self.current_choch else None,
            "current_range": self.current_range.to_dict() if self.current_range else None,
            "engine_version": self.engine_version,
            "quality": self.quality.value,
            "structure": self.structure.to_dict(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "trend": self.trend.to_dict() if self.trend else None,
            "version": self.version,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, payload: Mapping[str, Any]) -> MarketStructureSnapshot:
        structure_payload = payload["structure"]
        if not isinstance(structure_payload, Mapping):
            raise TypeError("serialized structure must be a mapping")
        structure = MarketStructure.from_dict(structure_payload)
        trend_payload = payload.get("trend")
        bos_payload = payload.get("current_bos")
        choch_payload = payload.get("current_choch")
        range_payload = payload.get("current_range")
        return cls(
            timestamp=str(payload["timestamp"]),
            structure=structure,
            version=int(payload.get("version", 1)),
            symbol=str(payload.get("symbol", "")),
            timeframe=str(payload.get("timeframe", "")),
            trend=Trend.from_dict(trend_payload) if isinstance(trend_payload, Mapping) else None,
            confidence=float(payload.get("confidence", 0.0)),
            quality=StructureQuality(str(payload.get("quality", StructureQuality.LOW.value))),
            current_bos=(
                BreakOfStructure.from_dict(bos_payload)
                if isinstance(bos_payload, Mapping)
                else None
            ),
            current_choch=(
                ChangeOfCharacter.from_dict(choch_payload)
                if isinstance(choch_payload, Mapping)
                else None
            ),
            current_range=(
                Range.from_dict(range_payload) if isinstance(range_payload, Mapping) else None
            ),
            created_at=str(payload.get("created_at", "")),
            engine_version=str(payload.get("engine_version", ENGINE_VERSION)),
        )

    def to_json(self) -> str:
        return deterministic_json(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> MarketStructureSnapshot:
        return cls.from_dict(load_json(payload))


@dataclass(frozen=True, slots=True)
class StructureStatistics:
    """Aggregated processing counters."""

    number_of_bos: int
    number_of_choch: int
    trend_changes: int
    ranges: int
    processed_swings: int
    processing_time_seconds: float
    false_bos: int = 0
    false_choch: int = 0
    invalid_structures: int = 0
    duplicate_events: int = 0
    average_detection_time_seconds: float = 0.0
    maximum_detection_time_seconds: float = 0.0
