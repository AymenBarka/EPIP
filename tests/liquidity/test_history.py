import pytest

from epip.liquidity.exceptions import LiquidityHistoryError, LiquidityVersionError
from epip.liquidity.history import LiquidityHistory
from epip.liquidity.models import LiquiditySnapshot


def snap(v: int, t: str) -> LiquiditySnapshot:
    return LiquiditySnapshot(t, "EURUSD", "M1", v)


def test_history_replay_serialization_and_errors() -> None:
    history = LiquidityHistory().append(snap(1, "1")).append(snap(2, "2"))
    assert history.latest() == snap(2, "2")
    assert history.by_version(1) == snap(1, "1")
    assert history.by_timestamp("2") == snap(2, "2")
    assert tuple(history.replay()) == history.snapshots
    assert LiquidityHistory.from_json(history.to_json()) == history
    with pytest.raises(LiquidityVersionError):
        history.append(snap(4, "4"))
    with pytest.raises(LiquidityHistoryError):
        history.append(snap(3, "0"))
