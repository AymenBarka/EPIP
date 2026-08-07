"""Decision application service using only official snapshots."""

from epip.context import MarketContextSnapshot
from epip.decision.confidence import ConfidenceCalculator
from epip.decision.config import DecisionConfig
from epip.decision.decision_matrix import DecisionMatrix
from epip.decision.models import (
    DecisionAction,
    DecisionQuality,
    EntryZone,
    ExitZone,
    Invalidation,
    RiskLevel,
    RiskProfile,
    TradeDecision,
)
from epip.decision.priority import PriorityCalculator
from epip.decision.probability import ProbabilityCalculator
from epip.decision.reasoning import DecisionReasoner
from epip.decision.rule_engine import DecisionRuleEngine
from epip.decision.scoring import DecisionScorer
from epip.elliott import CountStatus, WaveSnapshot


class DecisionAnalyzer:
    def __init__(self, config: DecisionConfig) -> None:
        self._config = config
        self._rules = DecisionRuleEngine()
        self._scorer = DecisionScorer()
        self._confidence = ConfidenceCalculator()
        self._probability = ProbabilityCalculator()
        self._priority = PriorityCalculator()
        self._reasoner = DecisionReasoner()
        self._matrix = DecisionMatrix()

    def analyze(
        self,
        context: MarketContextSnapshot,
        elliott: WaveSnapshot,
        previous: TradeDecision | None = None,
    ) -> TradeDecision:
        results = self._rules.evaluate(context, elliott, self._config)
        score = self._scorer.score(context, elliott, results)
        confidence = self._confidence.calculate(score)
        probability = self._probability.calculate(confidence, elliott.analysis.primary.probability)
        invalid = elliott.analysis.primary.status == CountStatus.INVALID
        action = self._matrix.decide(
            context.context.institutional_bias,
            score.total,
            self._config.minimum_action_score,
            invalid=invalid,
            previous=previous.action if previous else None,
        )
        entry, exits, invalidation = self._zones(context, elliott, action)
        return TradeDecision(
            f"{context.symbol}:{context.timeframe}:c{context.version.context}:e{elliott.version}",
            action,
            score,
            confidence,
            probability,
            self._quality(confidence.value),
            self._priority.calculate(score.total),
            self._risk(action, exits, entry),
            self._reasoner.explain(results),
            invalidation,
            entry,
            exits,
        )

    @staticmethod
    def _zones(
        context: MarketContextSnapshot, elliott: WaveSnapshot, action: DecisionAction
    ) -> tuple[EntryZone | None, ExitZone, Invalidation]:
        zone = context.context.ote or context.context.golden_zone
        entry = EntryZone(zone.low, zone.high, (zone.low + zone.high) / 2.0) if zone else None
        projection = elliott.analysis.projection
        targets = projection.targets if projection else ()
        prices = tuple(target.price for target in targets[:3])
        pools = context.context.current_liquidity_pools
        stop = None
        if pools:
            stop = (
                min(pool.price for pool in pools)
                if action == DecisionAction.LONG
                else max(pool.price for pool in pools)
            )
        exits = ExitZone(
            stop,
            prices[0] if len(prices) > 0 else None,
            prices[1] if len(prices) > 1 else None,
            prices[2] if len(prices) > 2 else None,
        )
        return entry, exits, Invalidation(stop, "Official liquidity invalidation level")

    def _risk(
        self, action: DecisionAction, exits: ExitZone, entry: EntryZone | None
    ) -> RiskProfile:
        if action in (DecisionAction.INVALID, DecisionAction.WAIT):
            return RiskProfile(RiskLevel.BLOCKED, 0.0, 0.0)
        reward = abs(exits.tp1 - entry.suggested_price) if exits.tp1 is not None and entry else 0.0
        risk = (
            abs(entry.suggested_price - exits.stop_loss)
            if exits.stop_loss is not None and entry
            else 0.0
        )
        ratio = reward / risk if risk else 0.0
        level = RiskLevel.CONSERVATIVE if ratio >= 2.0 else RiskLevel.MODERATE
        return RiskProfile(level, self._config.maximum_risk_fraction, ratio)

    @staticmethod
    def _quality(value: float) -> DecisionQuality:
        if value >= 0.85:
            return DecisionQuality.VERY_HIGH
        if value >= 0.7:
            return DecisionQuality.HIGH
        if value >= 0.5:
            return DecisionQuality.MEDIUM
        if value >= 0.3:
            return DecisionQuality.LOW
        return DecisionQuality.VERY_LOW
