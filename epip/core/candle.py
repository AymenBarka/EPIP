"""Immutable candle value objects for the core domain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from epip.core.value_objects import Price


@dataclass(frozen=True, slots=True)
class Candle:
    """Representation of a single market candle.

    Args:
        timestamp: Candle close time as an ISO-8601 string.
        symbol: Market symbol.
        timeframe: Candle timeframe identifier.
        open: Opening price.
        high: Highest price.
        low: Lowest price.
        close: Closing price.
        volume: Trading volume.
    """

    timestamp: str
    symbol: str
    timeframe: str
    open: Price | float
    high: Price | float
    low: Price | float
    close: Price | float
    volume: float
    schema_version: int = 1
    created_at: str = ""
    uuid: str = ""

    def __post_init__(self) -> None:
        """Validate the candle values after initialization."""
        object.__setattr__(self, "open", Price(self.open))
        object.__setattr__(self, "high", Price(self.high))
        object.__setattr__(self, "low", Price(self.low))
        object.__setattr__(self, "close", Price(self.close))
        object.__setattr__(self, "created_at", self.created_at or datetime.now(UTC).isoformat())
        object.__setattr__(self, "uuid", self.uuid or uuid4().hex)

        if self.high < self.open or self.high < self.close or self.high < self.low:
            raise ValueError("high must be greater than or equal to open, close, and low")
        if self.low > self.open or self.low > self.close:
            raise ValueError("low must be less than or equal to open and close")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")

    def body_size(self) -> float:
        """Return the candle body size in price points."""
        return abs(float(self.close) - float(self.open))

    def range(self) -> float:
        """Return the candle range in price points."""
        return float(self.high) - float(self.low)

    def body(self) -> tuple[float, float]:
        """Return the candle body as an open/close tuple."""
        return (float(self.open), float(self.close))

    def upper_wick(self) -> float:
        """Return the upper wick size."""
        return float(self.high) - max(float(self.open), float(self.close))

    def lower_wick(self) -> float:
        """Return the lower wick size."""
        return min(float(self.open), float(self.close)) - float(self.low)

    def is_inside_bar(self, previous: Candle) -> bool:
        """Return True when the candle is contained by the previous candle."""
        return previous.high >= self.high and previous.low <= self.low

    def is_outside_bar(self, previous: Candle) -> bool:
        """Return True when the candle breaks outside the previous candle range."""
        return self.high > previous.high and self.low < previous.low

    def is_engulfing(self, previous: Candle) -> bool:
        """Return True when the current candle engulfs the previous one."""
        if previous.body_size() == 0.0 or self.body_size() == 0.0:
            return False
        return (
            previous.bearish
            and self.bullish
            and float(self.open) <= float(previous.close)
            and float(self.close) >= float(previous.open)
        )

    def spread(self) -> float:
        """Return the candle spread as the range between high and low."""
        return self.range()

    def strength(self) -> float:
        """Return the candle body strength relative to its full range."""
        candle_range = self.range()
        if candle_range == 0.0:
            return 0.0
        return self.body_size() / candle_range

    @property
    def bullish(self) -> bool:
        """Return True when the candle closes above its open."""
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        """Return True when the candle closes below its open."""
        return self.close < self.open

    def is_doji(self) -> bool:
        """Return True when the candle body is empty."""
        return self.open == self.close

    def mid_price(self) -> float:
        """Return the midpoint of the candle range."""
        return (float(self.high) + float(self.low)) / 2.0

    def typical_price(self) -> float:
        """Return the typical price of the candle."""
        return (float(self.high) + float(self.low) + float(self.close)) / 3.0

    def weighted_price(self) -> float:
        """Return the weighted close price of the candle."""
        return (float(self.high) + float(self.low) + (2 * float(self.close))) / 4.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the candle to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "volume": self.volume,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Candle:
        """Deserialize the candle from a dictionary."""
        return cls(
            timestamp=data["timestamp"],
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
            uuid=data.get("uuid", ""),
        )

    def to_json(self) -> str:
        """Serialize the candle to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Candle:
        """Deserialize the candle from JSON."""
        return cls.from_dict(json.loads(payload))
