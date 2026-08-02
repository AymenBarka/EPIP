"""Deterministic Market Context serialization."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from epip.context.snapshot import (
    BiasContext,
    ConfluenceContext,
    InstitutionalBias,
    MarketContext,
    MarketContextSnapshot,
    MarketContextVersion,
    MarketPhase,
    TrendContext,
)
from epip.fibonacci.models import (
    DiscountZone,
    FibonacciSnapshot,
    FibonacciZone,
    GoldenZone,
    OTEZone,
    PremiumZone,
)
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot, TrendDirection
from epip.market_structure.serialization import swing_from_dict, swing_to_dict
from epip.swing.models import SwingSequence


def to_dict(snapshot: MarketContextSnapshot) -> dict[str, Any]:
    context = snapshot.context
    return {
        "timestamp": snapshot.timestamp,
        "version": {
            "context": snapshot.version.context,
            "structure": snapshot.version.structure,
            "liquidity": snapshot.version.liquidity,
            "fibonacci": snapshot.version.fibonacci,
        },
        "engine_version": snapshot.engine_version,
        "context": {
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "swings": [swing_to_dict(swing) for swing in context.swing_snapshot.swings],
            "structure": context.structure_snapshot.to_dict(),
            "liquidity": context.liquidity_snapshot.to_dict(),
            "fibonacci": context.fibonacci_snapshot.to_dict(),
            "trend": {
                "direction": context.trend.direction.value,
                "confidence": context.trend.confidence,
            },
            "phase": context.phase.value,
            "bias": {"bias": context.bias.bias.value, "score": context.bias.score},
            "confluence": {
                "score": context.confluence.score,
                "structure_score": context.confluence.structure_score,
                "liquidity_score": context.confluence.liquidity_score,
                "fibonacci_score": context.confluence.fibonacci_score,
            },
        },
    }


def from_dict(data: dict[str, Any]) -> MarketContextSnapshot:
    raw = data["context"]
    structure = MarketStructureSnapshot.from_dict(raw["structure"])
    liquidity = LiquiditySnapshot.from_dict(raw["liquidity"])
    fibonacci = _fibonacci(raw["fibonacci"])
    swings = SwingSequence(
        raw["symbol"],
        raw["timeframe"],
        tuple(swing for item in raw["swings"] if (swing := swing_from_dict(item)) is not None),
    )
    zones = {zone.name: zone for zone in fibonacci.zones}
    context = MarketContext(
        symbol=raw["symbol"],
        timeframe=raw["timeframe"],
        swing_snapshot=swings,
        structure_snapshot=structure,
        liquidity_snapshot=liquidity,
        fibonacci_snapshot=fibonacci,
        trend=TrendContext(
            TrendDirection(raw["trend"]["direction"]), float(raw["trend"]["confidence"])
        ),
        phase=MarketPhase(raw["phase"]),
        bias=BiasContext(InstitutionalBias(raw["bias"]["bias"]), float(raw["bias"]["score"])),
        confluence=ConfluenceContext(**raw["confluence"]),
        premium=_zone(zones.get("PREMIUM")),
        discount=_zone(zones.get("DISCOUNT")),
        ote=_zone(zones.get("OTE")),
        golden_zone=_zone(zones.get("GOLDEN")),
        current_liquidity_pools=tuple(pool for pool in liquidity.pools if pool.resting),
        current_bos=structure.current_bos,
        current_choch=structure.current_choch,
    )
    return MarketContextSnapshot(
        data["timestamp"], MarketContextVersion(**data["version"]), context, data["engine_version"]
    )


def _zone(zone: FibonacciZone | None) -> FibonacciZone | None:
    return zone


def _fibonacci(data: dict[str, Any]) -> FibonacciSnapshot:
    snapshot = FibonacciSnapshot.from_dict(data)
    zone_types = {
        "PREMIUM": PremiumZone,
        "DISCOUNT": DiscountZone,
        "OTE": OTEZone,
        "GOLDEN": GoldenZone,
    }
    zones = tuple(
        zone_types.get(zone.name, FibonacciZone)(
            zone.low, zone.high, zone.name, zone.confluence_score
        )
        for zone in snapshot.zones
    )
    return replace(snapshot, zones=zones)


def to_json(snapshot: MarketContextSnapshot) -> str:
    return json.dumps(to_dict(snapshot), sort_keys=True, separators=(",", ":"))


def from_json(payload: str) -> MarketContextSnapshot:
    return from_dict(json.loads(payload))
