from __future__ import annotations

import logging
import tracemalloc
from time import perf_counter

from epip.core.event_bus import EventBus
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.engine import MarketStructureEngine
from epip.market_structure.graph import StructureGraph
from epip.market_structure.history import StructureHistory
from epip.market_structure.observers import ObserverRegistry
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope

LOGGER = logging.getLogger(__name__)


def _swing(idx: int) -> Swing:
    cycle = idx % 8
    if cycle in (0, 1):
        classification = SwingClassification.HIGHER_HIGH
        pivot = PivotType.HIGH
        price = 1.2 + (idx * 0.00001)
    elif cycle in (2, 3):
        classification = SwingClassification.HIGHER_LOW
        pivot = PivotType.LOW
        price = 1.1 + (idx * 0.000005)
    elif cycle in (4, 5):
        classification = SwingClassification.LOWER_LOW
        pivot = PivotType.LOW
        price = 1.0 - (idx * 0.000005)
    else:
        classification = SwingClassification.LOWER_HIGH
        pivot = PivotType.HIGH
        price = 1.15 - (idx * 0.000003)

    return Swing(
        point=SwingPoint(
            symbol="EURUSD",
            timeframe="M1",
            index=idx,
            timestamp=f"2024-01-01T00:{(idx // 60) % 60:02d}:{idx % 60:02d}+00:00",
            price=price,
            pivot_type=pivot,
            left_bars=2,
            right_bars=2,
        ),
        classification=classification,
        scope=SwingScope.EXTERNAL,
        distance_from_previous=2,
        price_move_from_previous=0.001,
        detection_latency_bars=2,
    )


def _sequence(count: int) -> SwingSequence:
    return SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=tuple(_swing(idx) for idx in range(count)),
    )


def _run_case(count: int) -> None:
    event_bus = EventBus()
    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4),
        event_bus=event_bus,
    )
    batch_size = 20_000

    tracemalloc.start()
    started = perf_counter()
    processed = 0
    offset = 0
    while processed < count:
        size = min(batch_size, count - processed)
        # Keep per-call allocations bounded while still benchmarking high total volumes.
        sequence = SwingSequence(
            symbol="EURUSD",
            timeframe="M1",
            swings=tuple(_swing(offset + idx) for idx in range(size)),
        )
        engine.process_sequence(sequence)
        processed += size
        offset += size
    elapsed = perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    LOGGER.info("swings=%d", count)
    LOGGER.info("elapsed_seconds=%.6f", elapsed)
    LOGGER.info("swings_per_second=%.2f", count / elapsed if elapsed > 0.0 else 0.0)
    metrics = engine.metrics()
    LOGGER.info("event_count=%d", len(event_bus.event_history()))
    LOGGER.info("average_latency_seconds=%.8f", metrics.average_detection_time_seconds)
    LOGGER.info("peak_memory_bytes=%d", peak)
    LOGGER.info("current_memory_bytes=%d", current)


def _run_framework_case(iterations: int = 10_000) -> None:
    """Measure stabilization API overhead independently from detector throughput."""
    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4), event_bus=EventBus()
    )
    snapshot = engine.process_sequence(_sequence(20))
    registry = ObserverRegistry()

    class Counter:
        def __init__(self) -> None:
            self.count = 0

        def on_structure(self, _snapshot: object) -> None:
            self.count += 1

    counter = Counter()
    registry.register(counter)
    tracemalloc.start()

    started = perf_counter()
    for _ in range(iterations):
        StructureGraph().append(snapshot)
    graph_seconds = perf_counter() - started

    started = perf_counter()
    for _ in range(iterations):
        StructureHistory().append(snapshot)
    history_seconds = perf_counter() - started

    started = perf_counter()
    payloads = [snapshot.to_json() for _ in range(iterations)]
    serialization_seconds = perf_counter() - started

    started = perf_counter()
    for payload in payloads:
        type(snapshot).from_json(payload)
    deserialization_seconds = perf_counter() - started

    started = perf_counter()
    for _ in range(iterations):
        registry.notify(snapshot)
    observer_seconds = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    LOGGER.info("framework_iterations=%d", iterations)
    LOGGER.info("graph_creation_seconds=%.6f", graph_seconds)
    LOGGER.info("history_append_seconds=%.6f", history_seconds)
    LOGGER.info("serialization_seconds=%.6f", serialization_seconds)
    LOGGER.info("deserialization_seconds=%.6f", deserialization_seconds)
    LOGGER.info("observer_notification_seconds=%.6f", observer_seconds)
    LOGGER.info("framework_peak_memory_bytes=%d", peak)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    _run_framework_case()
    for count in (100_000, 1_000_000, 10_000_000):
        _run_case(count)


if __name__ == "__main__":
    main()
