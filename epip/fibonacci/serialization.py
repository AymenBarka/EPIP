"""Deterministic serialization for Fibonacci domain objects."""

import json
from dataclasses import asdict
from typing import Any, TypeVar, cast

from epip.core.integrity import integrity_deserializer
from epip.fibonacci.alignment import MultiTimeFrameAlignment
from epip.fibonacci.clusters import FibonacciCluster
from epip.fibonacci.institutional import InstitutionalEntryZone
from epip.fibonacci.models import (
    DiscountZone,
    FibonacciDirection,
    FibonacciExtension,
    FibonacciLevel,
    FibonacciRetracement,
    FibonacciSnapshot,
    GoldenZone,
    OTEZone,
    PremiumZone,
)
from epip.fibonacci.projections import ProjectionLabel, ProjectionTarget
from epip.fibonacci.strength import FibonacciQuality, FibonacciStrength

T = TypeVar("T")


def to_dict(value: FibonacciSnapshot) -> dict[str, object]:
    return value.to_dict()


@integrity_deserializer
def from_dict(data: dict[str, object]) -> FibonacciSnapshot:
    return FibonacciSnapshot.from_dict(cast(dict[str, Any], data))


def to_json(value: FibonacciSnapshot) -> str:
    return value.to_json()


@integrity_deserializer
def from_json(payload: str) -> FibonacciSnapshot:
    return FibonacciSnapshot.from_json(payload)


def object_to_json(value: object) -> str:
    return json.dumps(asdict(cast(Any, value)), sort_keys=True, separators=(",", ":"))


def _level(data: dict[str, Any]) -> FibonacciLevel:
    return FibonacciLevel(**data)


def _retracement(data: dict[str, Any]) -> FibonacciRetracement:
    return FibonacciRetracement(
        data["start_price"],
        data["end_price"],
        FibonacciDirection(data["direction"]),
        tuple(_level(item) for item in data["levels"]),
        data.get("confluence_score", 0.0),
    )


def _extension(data: dict[str, Any]) -> FibonacciExtension:
    return FibonacciExtension(
        data["start_price"],
        data["end_price"],
        tuple(_level(item) for item in data["levels"]),
        data.get("confluence_score", 0.0),
    )


def _cluster(data: dict[str, Any]) -> FibonacciCluster:
    return FibonacciCluster(
        data["cluster_id"],
        _retracement(data["retracement"]),
        _extension(data["extension"]),
        OTEZone(**data["ote"]),
        GoldenZone(**data["golden_zone"]),
        PremiumZone(**data["premium"]),
        DiscountZone(**data["discount"]),
        data.get("confluence_score", 0.0),
        data.get("probability", 0.0),
    )


def _institutional(data: dict[str, Any]) -> InstitutionalEntryZone:
    return InstitutionalEntryZone(
        data["symbol"],
        data["timeframe"],
        data["low"],
        data["high"],
        FibonacciDirection(data["direction"]),
        OTEZone(**data["ote"]),
        GoldenZone(**data["golden_zone"]),
        data["liquidity_score"],
        data["structure_score"],
        data.get("confluence_score", 0.0),
        data.get("probability", 0.0),
    )


@integrity_deserializer
def object_from_json(cls: type[T], payload: str) -> T:  # noqa: UP047
    data: dict[str, Any] = json.loads(payload)
    result: object
    if cls is FibonacciStrength:
        data["quality"] = FibonacciQuality(data["quality"])
        result = FibonacciStrength(**data)
    elif cls is ProjectionTarget:
        data["label"] = ProjectionLabel(data["label"])
        result = ProjectionTarget(**data)
    elif cls is MultiTimeFrameAlignment:
        directions = tuple(
            (str(timeframe), FibonacciDirection(direction))
            for timeframe, direction in data["directions"]
        )
        result = MultiTimeFrameAlignment(directions, data["alignment_score"])
    elif cls is FibonacciCluster:
        result = _cluster(data)
    elif cls is InstitutionalEntryZone:
        result = _institutional(data)
    else:
        raise TypeError(f"unsupported Fibonacci domain type: {cls.__name__}")
    return cast(T, result)
