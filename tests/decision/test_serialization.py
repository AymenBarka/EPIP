from epip.core.event_bus import EventBus
from epip.decision import DecisionConfig, DecisionEngine, DecisionSnapshot
from tests.decision.helpers import snapshots


def test_decision_snapshot_round_trip() -> None:
    snapshot = DecisionEngine(config=DecisionConfig(), event_bus=EventBus()).process(*snapshots())
    payload = snapshot.to_json()
    assert DecisionSnapshot.from_json(payload) == snapshot
    assert DecisionSnapshot.from_json(payload).to_json() == payload
    assert DecisionSnapshot.from_dict(snapshot.to_dict()) == snapshot
