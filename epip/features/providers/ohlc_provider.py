"""OHLC-based feature provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from epip.core.types import Direction
from epip.features.feature import Feature
from epip.features.feature_set import FeatureSet
from epip.features.providers.base_provider import BaseFeatureProvider


class OHLCProvider(BaseFeatureProvider):
    """Builds OHLC-derived features from a candle payload."""

    name = "ohlc"
    priority = 10

    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        candle = self._coerce_payload(payload)
        open_price = float(candle.get("open", 0.0))
        high_price = float(candle.get("high", open_price))
        low_price = float(candle.get("low", open_price))
        close_price = float(candle.get("close", open_price))
        body = close_price - open_price
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price
        spread = high_price - low_price
        direction = self._direction(open_price, close_price)

        features = (
            Feature(
                id=f"{self.name}-open-{timestamp}",
                name="open",
                category="ohlc",
                value=open_price,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-high-{timestamp}",
                name="high",
                category="ohlc",
                value=high_price,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-low-{timestamp}",
                name="low",
                category="ohlc",
                value=low_price,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-close-{timestamp}",
                name="close",
                category="ohlc",
                value=close_price,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-body-{timestamp}",
                name="body",
                category="ohlc",
                value=body,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-upper-wick-{timestamp}",
                name="upper_wick",
                category="ohlc",
                value=upper_wick,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-lower-wick-{timestamp}",
                name="lower_wick",
                category="ohlc",
                value=lower_wick,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-spread-{timestamp}",
                name="spread",
                category="ohlc",
                value=spread,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
            Feature(
                id=f"{self.name}-direction-{timestamp}",
                name="direction",
                category="ohlc",
                value=direction,
                timestamp=timestamp,
                metadata={"symbol": symbol, "timeframe": timeframe},
                quality_score=1.0,
                source=self.name,
            ),
        )
        return FeatureSet(features)

    def _direction(self, open_price: float, close_price: float) -> str:
        if close_price > open_price:
            return Direction.BUY.value
        if close_price < open_price:
            return Direction.SELL.value
        return Direction.NEUTRAL.value

    def _coerce_payload(self, payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
        if payload is None:
            return {}
        return payload
