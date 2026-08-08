"""Read-only market context objects for the core domain."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import InitVar, dataclass, field
from types import MappingProxyType
from typing import Any

from epip.core.candle import Candle
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)


@dataclass(frozen=True, slots=True)
class MarketContext:
    """An immutable market context snapshot.

    Args:
        symbol: Market symbol.
        timeframe: Context timeframe.
        timestamp: Context creation timestamp.
        candles: Candles attached to the context.
        metadata: Additional metadata.
        plugin_cache: Cache of plugin-specific state.
    """

    symbol: str
    timeframe: str
    timestamp: str
    candles: tuple[Candle, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False)
    plugin_cache: Mapping[str, Any] = field(default_factory=dict, compare=False)
    swings: tuple[str, ...] = field(default_factory=tuple)
    market_structure: str = ""
    regime: str = ""
    liquidity: str = ""
    indicators: Mapping[str, Any] = field(default_factory=dict, compare=False)
    plugin_outputs: Mapping[str, Any] = field(default_factory=dict, compare=False)
    schema_version: int = field(default=1, compare=False)
    created_at: str = field(default="", compare=False)
    uuid: str = field(default="", compare=False)
    clock: InitVar[ClockProtocol | None] = None
    id_generator: InitVar[IdGeneratorProtocol | None] = None

    def __post_init__(
        self, clock: ClockProtocol | None, id_generator: IdGeneratorProtocol | None
    ) -> None:
        """Normalize container values into immutable structures."""
        object.__setattr__(self, "candles", tuple(self.candles))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        object.__setattr__(self, "plugin_cache", MappingProxyType(dict(self.plugin_cache)))
        object.__setattr__(self, "swings", tuple(self.swings))
        object.__setattr__(self, "indicators", MappingProxyType(dict(self.indicators)))
        object.__setattr__(self, "plugin_outputs", MappingProxyType(dict(self.plugin_outputs)))
        object.__setattr__(self, "created_at", self.created_at or resolve_clock(clock).now())
        object.__setattr__(
            self,
            "uuid",
            self.uuid
            or resolve_id_generator(id_generator).generate(
                "market-context", self.symbol, self.timeframe, self.timestamp
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the context to a dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "candles": [candle.to_dict() for candle in self.candles],
            "metadata": dict(self.metadata),
            "plugin_cache": dict(self.plugin_cache),
            "swings": list(self.swings),
            "market_structure": self.market_structure,
            "regime": self.regime,
            "liquidity": self.liquidity,
            "indicators": dict(self.indicators),
            "plugin_outputs": dict(self.plugin_outputs),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketContext:
        """Deserialize the context from a dictionary."""
        return cls(
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            timestamp=data["timestamp"],
            candles=tuple(Candle.from_dict(item) for item in data.get("candles", [])),
            metadata=data.get("metadata", {}),
            plugin_cache=data.get("plugin_cache", {}),
            swings=tuple(data.get("swings", [])),
            market_structure=data.get("market_structure", ""),
            regime=data.get("regime", ""),
            liquidity=data.get("liquidity", ""),
            indicators=data.get("indicators", {}),
            plugin_outputs=data.get("plugin_outputs", {}),
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
            uuid=data.get("uuid", ""),
        )

    def to_json(self) -> str:
        """Serialize the context to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> MarketContext:
        """Deserialize the context from JSON."""
        return cls.from_dict(json.loads(payload))
