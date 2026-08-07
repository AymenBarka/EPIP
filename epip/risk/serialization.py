"""Deterministic risk serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from epip.risk.models import (
    Exposure,
    Leverage,
    Margin,
    PositionPlan,
    PositionSize,
    RiskLevel,
    RiskQuality,
    RiskReason,
    RiskScore,
    RiskSnapshot,
    SizingMethod,
    StopLoss,
    TakeProfit,
)


def to_dict(snapshot: RiskSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


def from_dict(data: dict[str, Any]) -> RiskSnapshot:
    raw = data["plan"]
    size = raw["position_size"]
    score = raw["score"]
    plan = PositionPlan(
        raw["plan_id"],
        raw["decision_id"],
        raw["symbol"],
        raw["action"],
        raw["entry_price"],
        PositionSize(
            size["quantity"], size["notional"], size["risk_amount"], SizingMethod(size["method"])
        ),
        StopLoss(**raw["stop_loss"]),
        tuple(TakeProfit(**item) for item in raw["take_profits"]),
        Exposure(**raw["exposure"]),
        Leverage(**raw["leverage"]),
        Margin(**raw["margin"]),
        RiskScore(
            score["value"],
            RiskQuality(score["quality"]),
            RiskLevel(score["level"]),
            score["probability"],
        ),
        raw["accepted"],
        tuple(RiskReason(**item) for item in raw["reasons"]),
    )
    return RiskSnapshot(
        data["timestamp"],
        data["symbol"],
        data["timeframe"],
        data["version"],
        data["decision_version"],
        plan,
        data.get("engine_version", "EPIP-013"),
    )


def to_json(snapshot: RiskSnapshot) -> str:
    return json.dumps(to_dict(snapshot), sort_keys=True, separators=(",", ":"))


def from_json(payload: str) -> RiskSnapshot:
    return from_dict(json.loads(payload))
