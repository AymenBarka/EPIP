"""Deterministic execution serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from epip.core.integrity import integrity_deserializer
from epip.execution.models import (
    ExecutionReason,
    ExecutionReport,
    ExecutionSnapshot,
    Order,
    OrderFill,
    OrderSide,
    OrderState,
    OrderType,
)


def to_dict(snapshot: ExecutionSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


@integrity_deserializer
def from_dict(data: dict[str, Any]) -> ExecutionSnapshot:
    report = data["report"]
    raw = report["order"]
    fills = tuple(OrderFill(**fill) for fill in raw["fills"])
    order = Order(
        raw["order_id"],
        raw["plan_id"],
        raw["symbol"],
        OrderSide(raw["side"]),
        OrderType(raw["order_type"]),
        raw["quantity"],
        raw["requested_price"],
        raw["limit_price"],
        raw["stop_price"],
        OrderState(raw["state"]),
        fills,
    )
    result = ExecutionReport(
        order,
        report["requested_quantity"],
        report["filled_quantity"],
        report["average_fill_price"],
        report["slippage"],
        report["commission"],
        report["completed"],
        tuple(ExecutionReason(**item) for item in report["reasons"]),
    )
    return ExecutionSnapshot(
        data["timestamp"],
        data["symbol"],
        data["version"],
        data["position_plan_id"],
        result,
        data.get("engine_version", "EPIP-014"),
    )


def to_json(snapshot: ExecutionSnapshot) -> str:
    return json.dumps(to_dict(snapshot), sort_keys=True, separators=(",", ":"))


@integrity_deserializer
def from_json(payload: str) -> ExecutionSnapshot:
    return from_dict(json.loads(payload))
