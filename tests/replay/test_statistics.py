from __future__ import annotations

import pytest

from epip.replay.replay_metrics import ReplayMetrics
from epip.replay.replay_statistics import ReplayStatistics


def test_statistics_snapshot_accumulates_metrics() -> None:
    stats = ReplayStatistics()
    stats.mark_started()
    stats.record_candle(0.2, peak_memory=128)
    stats.record_candle(0.4, peak_memory=256)
    stats.record_event(3)
    stats.record_feature(5)
    stats.observe_peak_memory(512)
    stats.mark_finished()

    snapshot = stats.snapshot()
    assert isinstance(snapshot, ReplayMetrics)
    assert snapshot.processed_candles == 2
    assert snapshot.processed_events == 3
    assert snapshot.processed_features == 5
    assert snapshot.average_latency == pytest.approx(0.3)
    assert snapshot.max_latency == 0.4
    assert snapshot.peak_memory == 512
