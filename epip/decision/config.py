"""EPIP-012 configuration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionConfig:
    minimum_confluence: float = 0.45
    minimum_wave_probability: float = 0.35
    minimum_action_score: float = 55.0
    maximum_risk_fraction: float = 0.01
    enabled_rules: tuple[str, ...] = (
        "TREND_ALIGNMENT",
        "LIQUIDITY_CONFIRMATION",
        "FIBONACCI_CONFIRMATION",
        "ELLIOTT_CONFIRMATION",
        "PREMIUM_DISCOUNT",
        "OTE",
        "WAVE_PROBABILITY",
        "CONFLUENCE_THRESHOLD",
        "MARKET_PHASE",
        "BIAS",
        "VOLATILITY_FILTER",
    )
    engine_version: str = "EPIP-012"
