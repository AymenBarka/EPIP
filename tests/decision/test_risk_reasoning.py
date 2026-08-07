from epip.core.event_bus import EventBus
from epip.decision import DecisionConfig, DecisionEngine, RiskLevel
from tests.decision.helpers import snapshots


def test_decision_contains_reasons_entry_exit_and_risk() -> None:
    snapshot = DecisionEngine(config=DecisionConfig(), event_bus=EventBus()).process(*snapshots())
    decision = snapshot.decision
    assert decision.reasons.positive
    assert decision.reasons.warnings
    assert decision.entry_zone is not None
    assert decision.exit_zone.tp1 is not None
    assert decision.risk_profile.level in (RiskLevel.CONSERVATIVE, RiskLevel.MODERATE)
    assert decision.risk_profile.max_risk_fraction == 0.01
