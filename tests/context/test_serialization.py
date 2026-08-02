from epip.context import MarketContextConfig, MarketContextEngine
from epip.context.snapshot import MarketContextSnapshot
from epip.core.event_bus import EventBus
from tests.context.helpers import official_inputs


def test_snapshot_serialization_round_trip_is_deterministic() -> None:
    snapshot = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus()).process(
        *official_inputs()
    )
    payload = snapshot.to_json()
    restored = MarketContextSnapshot.from_json(payload)
    assert restored == snapshot
    assert restored.to_json() == payload
    assert MarketContextSnapshot.from_dict(snapshot.to_dict()) == snapshot
