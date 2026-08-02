from __future__ import annotations

from epip.swing.statistics import SwingStatisticsCollector
from epip.swing.types import SwingClassification


def test_statistics_collector_snapshot() -> None:
    collector = SwingStatisticsCollector()
    collector.mark_started()
    collector.record_swing(
        classification=SwingClassification.HIGHER_HIGH,
        distance_from_previous=4,
        duration_bars=4,
        detection_latency_bars=2,
    )
    collector.record_swing(
        classification=SwingClassification.LOWER_LOW,
        distance_from_previous=6,
        duration_bars=6,
        detection_latency_bars=2,
    )
    collector.observe_peak_memory(1234)
    collector.mark_finished()

    stats = collector.snapshot_statistics()
    metrics = collector.snapshot_metrics()

    assert stats.swings_count == 2
    assert stats.higher_high_count == 1
    assert stats.lower_low_count == 1
    assert metrics.swings_count == 2
    assert metrics.peak_memory_bytes == 1234
    assert metrics.swings_per_second >= 0.0
