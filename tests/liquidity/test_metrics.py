from epip.liquidity.statistics import LiquidityStatistics


def test_metrics_accumulate_false_detections() -> None:
    stats = LiquidityStatistics()
    stats.record(pools=2, sweeps=1, highs=1, lows=1, stop_hunts=1, elapsed=0.1)
    stats.record_false_detection()
    result = stats.snapshot()
    assert result.pools == 2 and result.false_detections == 1
