"""Deterministic serialization helpers for market-structure domain objects."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from epip.swing.models import Swing, SwingPoint
from epip.swing.types import PivotType, SwingClassification, SwingScope


def deterministic_json(payload: Mapping[str, Any]) -> str:
    """Serialize a mapping with a stable key order and compact representation."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def swing_to_dict(swing: Swing | None) -> dict[str, Any] | None:
    if swing is None:
        return None
    payload = asdict(swing)
    payload["point"]["pivot_type"] = swing.point.pivot_type.value
    payload["classification"] = swing.classification.value
    payload["scope"] = swing.scope.value
    return payload


def swing_from_dict(payload: object) -> Swing | None:
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise TypeError("serialized swing must be a mapping or null")
    point_payload = payload["point"]
    if not isinstance(point_payload, Mapping):
        raise TypeError("serialized swing point must be a mapping")
    point = SwingPoint(
        symbol=str(point_payload["symbol"]),
        timeframe=str(point_payload["timeframe"]),
        index=int(point_payload["index"]),
        timestamp=str(point_payload["timestamp"]),
        price=float(point_payload["price"]),
        pivot_type=PivotType(str(point_payload["pivot_type"])),
        left_bars=int(point_payload["left_bars"]),
        right_bars=int(point_payload["right_bars"]),
        confirmed=bool(point_payload.get("confirmed", True)),
    )
    return Swing(
        point=point,
        classification=SwingClassification(str(payload["classification"])),
        scope=SwingScope(str(payload["scope"])),
        distance_from_previous=int(payload["distance_from_previous"]),
        price_move_from_previous=float(payload["price_move_from_previous"]),
        detection_latency_bars=int(payload["detection_latency_bars"]),
    )


def load_json(payload: str) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise TypeError("serialized domain object must contain a JSON object")
    return value
