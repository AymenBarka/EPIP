from epip.core.event_bus import EventBus
from epip.elliott import ElliottConfig, ElliottWaveEngine, WaveSnapshot
from tests.elliott.helpers import market_context


def test_snapshot_round_trip_is_deterministic() -> None:
    snapshot = ElliottWaveEngine(config=ElliottConfig(), event_bus=EventBus()).process(
        market_context()
    )
    payload = snapshot.to_json()
    assert WaveSnapshot.from_json(payload) == snapshot
    assert WaveSnapshot.from_json(payload).to_json() == payload
    assert WaveSnapshot.from_dict(snapshot.to_dict()) == snapshot
