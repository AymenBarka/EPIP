"""Immutable, versioned research dataset contracts (P04-R01-D00).

Research-only. Nothing under ``epip/`` imports this package.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

MANIFEST_SCHEMA_VERSION = 1
SUPPORTED_MANIFEST_SCHEMA_VERSIONS = frozenset({MANIFEST_SCHEMA_VERSION})
TICK_NORMALIZATION_VERSION = "epip-research-ticks-csv/1"
BAR_NORMALIZATION_VERSION = "epip-research-bars-csv/1"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SYMBOL = re.compile(r"^[A-Z0-9]{3,16}$")
MS_PER_HOUR = 3_600_000


class DatasetIntegrityError(ValueError):
    """Raised when research data or metadata violates a fail-closed rule."""


class Provider(StrEnum):
    DUKASCOPY = "DUKASCOPY"
    MT5 = "MT5"


class PriceSide(StrEnum):
    BID = "BID"
    ASK = "ASK"


class Granularity(StrEnum):
    TICK = "TICK"
    H1 = "H1"
    H4 = "H4"


class SourceFormat(StrEnum):
    DUKASCOPY_TICKS_BI5 = "DUKASCOPY_TICKS_BI5"
    DUKASCOPY_CANDLES_H1_BI5 = "DUKASCOPY_CANDLES_H1_BI5"
    MT5_BARS_CSV = "MT5_BARS_CSV"
    MT5_TICKS_CSV = "MT5_TICKS_CSV"
    DERIVED_FROM_TICKS = "DERIVED_FROM_TICKS"


class HourStatus(StrEnum):
    """Classification of one provider source hour."""

    POPULATED = "POPULATED"
    EXPECTED_CLOSURE = "EXPECTED_CLOSURE"
    EMPTY_UNEXPLAINED = "EMPTY_UNEXPLAINED"
    MISSING = "MISSING"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    THROTTLED = "THROTTLED"
    CORRUPTED = "CORRUPTED"
    PARTIAL = "PARTIAL"
    NOT_ACQUIRED = "NOT_ACQUIRED"


COMPLETE_HOUR_STATUSES = frozenset({HourStatus.POPULATED, HourStatus.EXPECTED_CLOSURE})


class BarCoverage(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class OOSStatus(StrEnum):
    """Consultation status of an instrument/period (G00 section 10)."""

    CONSULTED = "CONSULTED"
    UNVERIFIED_NOT_ATTESTED_VIRGIN = "UNVERIFIED — NOT ATTESTED VIRGIN"
    ATTESTED_VIRGIN = "ATTESTED_VIRGIN"


class Partition(StrEnum):
    TECHNICAL = "TECHNICAL"
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    FINAL_OOS = "FINAL_OOS"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetIntegrityError(message)


def require_sha256(value: object, name: str) -> None:
    require(type(value) is str and bool(_SHA256.match(value)), f"{name} must be a SHA-256 hex")


def require_text(value: object, name: str) -> None:
    require(type(value) is str and bool(value) and value == value.strip(), f"{name} invalid")


def require_int(value: object, name: str, *, minimum: int = 0) -> None:
    require(type(value) is int and value >= minimum, f"{name} must be an int >= {minimum}")


@dataclass(frozen=True, slots=True)
class InstrumentSpec:
    """Provider-specific instrument definition with an explicit price scale."""

    symbol: str
    provider: Provider
    provider_symbol: str
    price_decimals: int

    def __post_init__(self) -> None:
        require(type(self.symbol) is str and bool(_SYMBOL.match(self.symbol)), "symbol invalid")
        require(type(self.provider) is Provider, "provider invalid")
        require_text(self.provider_symbol, "provider_symbol")
        require(type(self.price_decimals) is int, "price_decimals must be int")
        require(1 <= self.price_decimals <= 8, "price_decimals out of range")

    @property
    def scale(self) -> int:
        return int(10**self.price_decimals)


@dataclass(frozen=True, slots=True)
class Tick:
    """One quote record. Prices are integer points; volumes are quoted liquidity."""

    timestamp_ms: int
    bid_points: int
    ask_points: int
    bid_volume_micro: int
    ask_volume_micro: int

    def __post_init__(self) -> None:
        require_int(self.timestamp_ms, "timestamp_ms")
        require_int(self.bid_points, "bid_points", minimum=1)
        require_int(self.ask_points, "ask_points", minimum=1)
        require(self.ask_points >= self.bid_points, "ask must not be below bid")
        require_int(self.bid_volume_micro, "bid_volume_micro")
        require_int(self.ask_volume_micro, "ask_volume_micro")


@dataclass(frozen=True, slots=True)
class Bar:
    """OHLC bar of one price side over the half-open UTC interval [start, end)."""

    start_ms: int
    end_ms: int
    side: PriceSide
    open_points: int
    high_points: int
    low_points: int
    close_points: int
    tick_count: int
    coverage: BarCoverage

    def __post_init__(self) -> None:
        require_int(self.start_ms, "start_ms")
        require(type(self.end_ms) is int and self.end_ms > self.start_ms, "end_ms invalid")
        require(type(self.side) is PriceSide, "side invalid")
        for name in ("open_points", "high_points", "low_points", "close_points"):
            require_int(getattr(self, name), name, minimum=1)
        require(
            self.low_points <= min(self.open_points, self.close_points)
            and self.high_points >= max(self.open_points, self.close_points),
            "OHLC relationship invalid",
        )
        require_int(self.tick_count, "tick_count")
        require(type(self.coverage) is BarCoverage, "coverage invalid")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    location: str

    def __post_init__(self) -> None:
        require_text(self.code, "diagnostic.code")
        require(type(self.severity) is Severity, "diagnostic.severity invalid")
        require(type(self.message) is str, "diagnostic.message invalid")
        require(type(self.location) is str, "diagnostic.location invalid")


@dataclass(frozen=True, slots=True)
class RawArtifact:
    """Identity of one immutable raw provider file, relative to the data root."""

    relative_path: str
    source_format: SourceFormat
    size_bytes: int
    raw_sha256: str
    hour_status: HourStatus

    def __post_init__(self) -> None:
        require_text(self.relative_path, "relative_path")
        require("\\" not in self.relative_path, "relative_path must use '/' separators")
        require(not self.relative_path.startswith("/"), "relative_path must be relative")
        require(".." not in self.relative_path.split("/"), "relative_path must not escape root")
        require(type(self.source_format) is SourceFormat, "source_format invalid")
        require_int(self.size_bytes, "size_bytes")
        require_sha256(self.raw_sha256, "raw_sha256")
        require(type(self.hour_status) is HourStatus, "hour_status invalid")


@dataclass(frozen=True, slots=True)
class ContentIdentity:
    """Canonical content identity: uncompressed SHA-256 is authoritative."""

    relative_path: str
    canonical_sha256: str
    compressed_sha256: str
    row_count: int

    def __post_init__(self) -> None:
        require_text(self.relative_path, "content.relative_path")
        require_sha256(self.canonical_sha256, "canonical_sha256")
        require_sha256(self.compressed_sha256, "compressed_sha256")
        require_int(self.row_count, "row_count")


@dataclass(frozen=True, slots=True)
class Coverage:
    start_ms: int
    end_ms: int
    hours_expected: int
    hours_populated: int
    hours_expected_closure: int
    hours_unexplained_or_failed: int

    def __post_init__(self) -> None:
        require_int(self.start_ms, "coverage.start_ms")
        require(type(self.end_ms) is int and self.end_ms > self.start_ms, "coverage.end_ms")
        for name in (
            "hours_expected",
            "hours_populated",
            "hours_expected_closure",
            "hours_unexplained_or_failed",
        ):
            require_int(getattr(self, name), f"coverage.{name}")
        require(
            self.hours_populated + self.hours_expected_closure + self.hours_unexplained_or_failed
            == self.hours_expected,
            "coverage hour counts do not add up",
        )


def finite_non_negative(value: float, name: str) -> None:
    require(math.isfinite(value) and value >= 0.0, f"{name} must be finite and non-negative")
