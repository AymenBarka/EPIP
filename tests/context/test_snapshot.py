from dataclasses import FrozenInstanceError

import pytest

from epip.context import MarketContextConfig, MarketContextEngine
from epip.core.event_bus import EventBus
from tests.context.helpers import official_inputs


def test_snapshot_is_immutable_and_exposes_context() -> None:
    snapshot = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus()).process(
        *official_inputs()
    )
    assert snapshot.symbol == "EURUSD"
    assert snapshot.context.confluence_score == snapshot.context.confluence.score
    with pytest.raises(FrozenInstanceError):
        snapshot.timestamp = "changed"  # type: ignore[misc]
