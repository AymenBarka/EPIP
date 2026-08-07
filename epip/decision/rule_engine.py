"""Modular configurable Decision Rule Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from epip.context import InstitutionalBias, MarketContextSnapshot, MarketPhase
from epip.decision.config import DecisionConfig
from epip.decision.models import RuleOutcome, RuleResult
from epip.elliott import CountStatus, WaveSnapshot


class DecisionRule(Protocol):
    @property
    def rule_id(self) -> str: ...

    def evaluate(
        self, context: MarketContextSnapshot, elliott: WaveSnapshot, config: DecisionConfig
    ) -> RuleResult: ...


@dataclass(frozen=True, slots=True)
class FunctionalRule:
    rule_id: str
    message: str
    weight: float
    predicate: str

    def evaluate(
        self, context: MarketContextSnapshot, elliott: WaveSnapshot, config: DecisionConfig
    ) -> RuleResult:
        c = context.context
        primary = elliott.analysis.primary
        outcomes = {
            "trend": c.trend.direction.value in ("UPTREND", "DOWNTREND"),
            "liquidity": bool(c.current_liquidity_pools),
            "fibonacci": c.fibonacci_snapshot.probability > 0.0,
            "elliott": primary.status != CountStatus.INVALID,
            "premium_discount": c.premium is not None and c.discount is not None,
            "ote": c.ote is not None,
            "wave_probability": primary.probability >= config.minimum_wave_probability,
            "confluence": c.confluence_score >= config.minimum_confluence,
            "phase": c.phase not in (MarketPhase.UNKNOWN, MarketPhase.RANGE),
            "bias": c.institutional_bias != InstitutionalBias.NEUTRAL,
        }
        if self.predicate == "volatility":
            return RuleResult(self.rule_id, RuleOutcome.WARNING, self.message, self.weight)
        passed = outcomes[self.predicate]
        return RuleResult(
            self.rule_id,
            RuleOutcome.PASS if passed else RuleOutcome.FAIL,
            self.message,
            self.weight,
        )


class DecisionRuleEngine:
    def __init__(self, rules: tuple[DecisionRule, ...] | None = None) -> None:
        self._rules = rules or default_rules()

    def evaluate(
        self, context: MarketContextSnapshot, elliott: WaveSnapshot, config: DecisionConfig
    ) -> tuple[RuleResult, ...]:
        return tuple(
            rule.evaluate(context, elliott, config)
            for rule in self._rules
            if rule.rule_id in config.enabled_rules
        )


def default_rules() -> tuple[DecisionRule, ...]:
    definitions = (
        ("TREND_ALIGNMENT", "Trend is directional", 1.0, "trend"),
        ("LIQUIDITY_CONFIRMATION", "Official liquidity confirms", 1.0, "liquidity"),
        ("FIBONACCI_CONFIRMATION", "Official Fibonacci confirms", 1.0, "fibonacci"),
        ("ELLIOTT_CONFIRMATION", "Official Elliott count is valid", 1.2, "elliott"),
        ("PREMIUM_DISCOUNT", "Premium and discount are available", 0.6, "premium_discount"),
        ("OTE", "OTE is available", 0.7, "ote"),
        ("WAVE_PROBABILITY", "Wave probability meets threshold", 1.1, "wave_probability"),
        ("CONFLUENCE_THRESHOLD", "Context confluence meets threshold", 1.2, "confluence"),
        ("MARKET_PHASE", "Market phase is directional", 0.8, "phase"),
        ("BIAS", "Institutional bias is directional", 1.0, "bias"),
        ("VOLATILITY_FILTER", "No official volatility snapshot available", 0.3, "volatility"),
    )
    return tuple(FunctionalRule(*definition) for definition in definitions)
