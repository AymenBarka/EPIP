"""Deterministic portfolio serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from epip.core.integrity import integrity_deserializer
from epip.portfolio.models import (
    PortfolioAllocation,
    PortfolioEquity,
    PortfolioExposure,
    PortfolioPnL,
    PortfolioPosition,
    PortfolioSnapshot,
    PortfolioState,
    PositionDirection,
)


def to_dict(snapshot: PortfolioSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


@integrity_deserializer
def from_dict(data: dict[str, Any]) -> PortfolioSnapshot:
    raw = data["state"]
    positions = tuple(
        PortfolioPosition(
            item["symbol"],
            item["quantity"],
            PositionDirection(item["direction"]),
            item["average_price"],
            item["market_price"],
            item.get("realized_pnl", 0.0),
            item.get("unrealized_pnl", 0.0),
        )
        for item in raw["positions"]
    )
    state = PortfolioState(
        positions,
        PortfolioExposure(**raw["exposure"]),
        tuple(PortfolioAllocation(**item) for item in raw["allocations"]),
        PortfolioPnL(**raw["pnl"]),
        PortfolioEquity(**raw["equity"]),
        tuple((str(name), float(value)) for name, value in raw["correlation_exposure"]),
        tuple(raw.get("limit_reasons", ())),
    )
    return PortfolioSnapshot(
        data["timestamp"],
        data["version"],
        data["execution_version"],
        data["execution_plan_id"],
        state,
        data.get("engine_version", "EPIP-015"),
    )


def to_json(snapshot: PortfolioSnapshot) -> str:
    return json.dumps(to_dict(snapshot), sort_keys=True, separators=(",", ":"))


@integrity_deserializer
def from_json(payload: str) -> PortfolioSnapshot:
    return from_dict(json.loads(payload))
