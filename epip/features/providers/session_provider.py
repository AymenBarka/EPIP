"""Session-based feature provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from epip.features.feature import Feature
from epip.features.feature_set import FeatureSet
from epip.features.providers.base_provider import BaseFeatureProvider


class SessionProvider(BaseFeatureProvider):
    """Adds session metadata for a candle."""

    name = "session"
    priority = 40

    def provide(
        self,
        *,
        symbol: str,
        timeframe: str,
        timestamp: str,
        payload: Mapping[str, Any] | None = None,
        feature_set: FeatureSet | None = None,
    ) -> FeatureSet:
        session_value = "regular"
        if payload is not None:
            session_value = str(payload.get("session", session_value))
        return FeatureSet(
            (
                Feature(
                    id=f"{self.name}-{timestamp}",
                    name="session",
                    category="session",
                    value=session_value,
                    timestamp=timestamp,
                    metadata={"symbol": symbol, "timeframe": timeframe},
                    quality_score=0.9,
                    source=self.name,
                ),
            )
        )
