"""Institutional entry zone combining upstream evidence."""

from dataclasses import dataclass

from epip.fibonacci.models import FibonacciDirection, GoldenZone, OTEZone


@dataclass(frozen=True, slots=True)
class InstitutionalEntryZone:
    symbol: str
    timeframe: str
    low: float
    high: float
    direction: FibonacciDirection
    ote: OTEZone
    golden_zone: GoldenZone
    liquidity_score: float
    structure_score: float
    confluence_score: float = 0.0
    probability: float = 0.0
