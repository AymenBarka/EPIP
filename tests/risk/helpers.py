from epip.decision.models import (
    DecisionAction,
    DecisionConfidence,
    DecisionProbability,
    DecisionQuality,
    DecisionReason,
    DecisionScore,
    DecisionSnapshot,
    EntryZone,
    ExecutionPriority,
    ExitZone,
    Invalidation,
    PriorityLevel,
    RiskLevel,
    RiskProfile,
    TradeDecision,
)


def decision(*, action: DecisionAction = DecisionAction.LONG, version: int = 1) -> DecisionSnapshot:
    trade = TradeDecision(
        "d-1",
        action,
        DecisionScore(80, 80, 80, 80),
        DecisionConfidence(0.8),
        DecisionProbability(0.7),
        DecisionQuality.HIGH,
        ExecutionPriority(PriorityLevel.HIGH, 2),
        RiskProfile(RiskLevel.MODERATE, 0.01, 2),
        DecisionReason(("trend",), (), (), ()),
        Invalidation(98.0, "structure"),
        EntryZone(99, 101, 100),
        ExitZone(98, 102, 104, 106),
    )
    return DecisionSnapshot("2026-01-01T00:00:00Z", "EURUSD", "H1", version, 1, 1, trade)
