"""Deterministic TradeDecision serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from epip.core.integrity import integrity_deserializer
from epip.decision.models import (
    DecisionAction,
    DecisionConfidence,
    DecisionProbability,
    DecisionQuality,
    DecisionReason,
    DecisionScore,
    DecisionSnapshot,
    EntryZone,
    ExecutionPriority,
    ExitZone,
    Invalidation,
    PriorityLevel,
    RiskLevel,
    RiskProfile,
    TradeDecision,
)


def to_dict(snapshot: DecisionSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


@integrity_deserializer
def from_dict(data: dict[str, Any]) -> DecisionSnapshot:
    raw = data["decision"]
    decision = TradeDecision(
        raw["decision_id"],
        DecisionAction(raw["action"]),
        DecisionScore(**raw["score"]),
        DecisionConfidence(**raw["confidence"]),
        DecisionProbability(**raw["probability"]),
        DecisionQuality(raw["quality"]),
        ExecutionPriority(PriorityLevel(raw["priority"]["level"]), raw["priority"]["rank"]),
        RiskProfile(
            RiskLevel(raw["risk_profile"]["level"]),
            raw["risk_profile"]["max_risk_fraction"],
            raw["risk_profile"]["risk_reward_ratio"],
        ),
        DecisionReason(
            tuple(raw["reasons"]["positive"]),
            tuple(raw["reasons"]["negative"]),
            tuple(raw["reasons"]["warnings"]),
            tuple(raw["reasons"]["blocked_conditions"]),
        ),
        Invalidation(**raw["invalidation"]),
        EntryZone(**raw["entry_zone"]) if raw["entry_zone"] is not None else None,
        ExitZone(**raw["exit_zone"]),
    )
    return DecisionSnapshot(
        data["timestamp"],
        data["symbol"],
        data["timeframe"],
        data["version"],
        data["context_version"],
        data["elliott_version"],
        decision,
        data.get("engine_version", "EPIP-012"),
    )


def to_json(snapshot: DecisionSnapshot) -> str:
    return json.dumps(to_dict(snapshot), sort_keys=True, separators=(",", ":"))


@integrity_deserializer
def from_json(payload: str) -> DecisionSnapshot:
    return from_dict(json.loads(payload))
