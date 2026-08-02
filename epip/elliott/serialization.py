"""Deterministic Elliott snapshot serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from epip.elliott.models import (
    AlternateCount,
    CountStatus,
    ElliottAnalysis,
    Wave,
    WaveCount,
    WaveDegree,
    WaveLabel,
    WavePattern,
    WaveProjection,
    WaveQuality,
    WaveSequence,
    WaveSnapshot,
    WaveTarget,
    WaveViolation,
)


def to_dict(snapshot: WaveSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


def _wave(data: dict[str, Any]) -> Wave:
    return Wave(
        WaveLabel(data["label"]),
        WaveDegree(data["degree"]),
        data["start_index"],
        data["end_index"],
        data["start_timestamp"],
        data["end_timestamp"],
        data["start_price"],
        data["end_price"],
        data["direction"],
    )


def _sequence(data: dict[str, Any]) -> WaveSequence:
    return WaveSequence(
        tuple(_wave(wave) for wave in data["waves"]),
        WavePattern(data["pattern"]),
        WaveDegree(data["degree"]),
    )


def _violation(data: dict[str, Any]) -> WaveViolation:
    label = data.get("wave_label")
    return WaveViolation(
        data["rule_id"], data["message"], WaveLabel(label) if label is not None else None
    )


def _count(data: dict[str, Any]) -> WaveCount:
    return WaveCount(
        data["count_id"],
        _sequence(data["sequence"]),
        tuple(_violation(item) for item in data["violations"]),
        data["confidence"],
        data["probability"],
        WaveQuality(data["quality"]),
        data["confluence"],
        CountStatus(data["status"]),
    )


def _projection(data: dict[str, Any] | None) -> WaveProjection | None:
    if data is None:
        return None
    targets = tuple(
        WaveTarget(
            WaveLabel(target["label"]),
            target["price"],
            target["low"],
            target["high"],
            target["probability"],
        )
        for target in data["targets"]
    )
    return WaveProjection(
        WaveLabel(data["next_wave"]), data["expected_retracement"], targets, data["confluence"]
    )


def from_dict(data: dict[str, Any]) -> WaveSnapshot:
    analysis = data["analysis"]
    return WaveSnapshot(
        data["timestamp"],
        data["symbol"],
        data["timeframe"],
        data["version"],
        data["context_version"],
        ElliottAnalysis(
            _count(analysis["primary"]),
            tuple(
                AlternateCount(_count(item["count"]), item["rationale"])
                for item in analysis["alternates"]
            ),
            _projection(analysis["projection"]),
        ),
        data.get("engine_version", "EPIP-011"),
    )


def to_json(snapshot: WaveSnapshot) -> str:
    return json.dumps(to_dict(snapshot), sort_keys=True, separators=(",", ":"))


def from_json(payload: str) -> WaveSnapshot:
    return from_dict(json.loads(payload))
