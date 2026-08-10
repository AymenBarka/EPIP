"""Deterministic serialization for EPIP-008 extension objects."""

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, TypeVar, cast

from epip.core.integrity import integrity_deserializer, validate_object
from epip.liquidity.clusters import LiquidityCluster
from epip.liquidity.fvg import BearishFVG, BullishFVG, FairValueGap
from epip.liquidity.models import LiquidityScope, LiquiditySnapshot
from epip.liquidity.ranking import LiquidityRanking
from epip.liquidity.strength import LiquidityStrength
from epip.liquidity.tree import LiquidityTreeNode, MultiTimeFrameLiquidityTree
from epip.liquidity.voids import LiquidityVoid

T = TypeVar("T")


def _encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: _encode(v) for k, v in asdict(cast(Any, value)).items()}
    if isinstance(value, (tuple, list)):
        return [_encode(x) for x in value]
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    return value


def to_dict(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], _encode(value))


def to_json(value: object) -> str:
    return json.dumps(to_dict(value), sort_keys=True, separators=(",", ":"))


@integrity_deserializer
def from_dict(cls: type[T], data: dict[str, Any]) -> T:  # noqa: UP047
    if cls is LiquidityStrength:
        data = {**data, "strength_level": LiquidityRanking(data["strength_level"])}
    elif cls in (FairValueGap, BullishFVG, BearishFVG, LiquidityVoid):
        data = {**data, "scope": LiquidityScope(data["scope"])}
    elif cls is MultiTimeFrameLiquidityTree:
        nodes = tuple(
            LiquidityTreeNode(
                x["node_id"],
                x["timeframe"],
                LiquiditySnapshot.from_dict(x["snapshot"]),
                x.get("parent_id"),
            )
            for x in data["nodes"]
        )
        return cast(T, MultiTimeFrameLiquidityTree(nodes))
    elif cls is LiquidityCluster:
        data = {
            **data,
            "equal_highs": tuple(data.get("equal_highs", ())),
            "equal_lows": tuple(data.get("equal_lows", ())),
            "pools": tuple(data.get("pools", ())),
            "fair_value_gaps": tuple(data.get("fair_value_gaps", ())),
            "voids": tuple(data.get("voids", ())),
        }
    result = cls(**data)
    validate_object(result, cls.__name__)
    return result


@integrity_deserializer
def from_json(cls: type[T], payload: str) -> T:  # noqa: UP047
    return from_dict(cls, json.loads(payload))
