from epip.liquidity.events import LiquidityConsumed, LiquidityInvalidated


def test_lifecycle_events() -> None:
    consumed = LiquidityConsumed(
        id="c", timestamp="t", symbol="EURUSD", timeframe="M1", pool_id="p"
    )
    invalidated = LiquidityInvalidated(
        id="i", timestamp="t", symbol="EURUSD", timeframe="M1", pool_id="p"
    )
    assert consumed.pool_id == invalidated.pool_id == "p"
