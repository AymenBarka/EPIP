from __future__ import annotations

from epip.replay.replay_metrics import ReplayMetrics


def test_metrics_value_object() -> None:
    metrics = ReplayMetrics(
        elapsed_time=1.0,
        candles_per_second=100.0,
        average_latency=0.01,
        max_latency=0.02,
        peak_memory=1024,
        processed_candles=100,
        processed_events=50,
        processed_features=200,
    )

    assert metrics.processed_candles == 100
    assert metrics.candles_per_second == 100.0
