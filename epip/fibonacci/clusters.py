"""Immutable Fibonacci confluence cluster."""

from dataclasses import dataclass

from epip.fibonacci.models import (
    DiscountZone,
    FibonacciExtension,
    FibonacciRetracement,
    GoldenZone,
    OTEZone,
    PremiumZone,
)


@dataclass(frozen=True, slots=True)
class FibonacciCluster:
    cluster_id: str
    retracement: FibonacciRetracement
    extension: FibonacciExtension
    ote: OTEZone
    golden_zone: GoldenZone
    premium: PremiumZone
    discount: DiscountZone
    confluence_score: float = 0.0
    probability: float = 0.0
