from __future__ import annotations

from epip.market_structure.statistics import MarketStructureStatistics


def test_statistics_and_metrics_snapshot() -> None:
    stats = MarketStructureStatistics()
    stats.mark_started()
    stats.record_processed_swings(10)
    stats.record_bos(0.01)
    stats.record_bos(0.03)
    stats.record_choch(0.02)
    stats.record_false_bos()
    stats.record_false_choch()
    stats.record_invalid_structure()
    stats.record_duplicate_event()
    stats.record_detection_time(0.04)
    stats.record_detection_time(0.06)
    stats.record_trend_change()
    stats.record_range()
    stats.observe_peak_memory(2048)
    stats.mark_finished()

    snap = stats.snapshot_statistics()
    metrics = stats.snapshot_metrics()

    assert snap.number_of_bos == 2
    assert snap.number_of_choch == 1
    assert snap.trend_changes == 1
    assert snap.ranges == 1
    assert snap.processed_swings == 10
    assert snap.false_bos == 1
    assert snap.false_choch == 1
    assert snap.invalid_structures == 1
    assert snap.duplicate_events == 1
    assert metrics.average_bos_detection_time_seconds > 0.0
    assert metrics.average_choch_detection_time_seconds > 0.0
    assert metrics.average_detection_time_seconds > 0.0
    assert metrics.maximum_detection_time_seconds >= metrics.average_detection_time_seconds
    assert metrics.total_processed_swings == 10
    assert metrics.peak_memory_bytes == 2048
