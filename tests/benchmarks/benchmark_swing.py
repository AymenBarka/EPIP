from __future__ import annotations

import logging
import tracemalloc
from collections.abc import Iterator
from time import perf_counter, process_time

from epip.core.candle import Candle
from epip.core.event_bus import EventBus
from epip.swing.config import SwingConfig
from epip.swing.engine import SwingEngine

LOGGER = logging.getLogger(__name__)


def _candle_stream(count: int) -> Iterator[Candle]:
    close = 1.1000
    for index in range(count):
        step = 0.0003 if index % 7 in (0, 1, 2) else -0.0002
        close = max(0.5, close + step)
        spread = 0.0007 + (0.0001 if index % 11 == 0 else 0.0)
        yield Candle(
            timestamp=f"2024-01-01T00:{index // 60:02d}:{index % 60:02d}+00:00",
            symbol="EURUSD",
            timeframe="M1",
            open=close - (spread / 4.0),
            high=close + spread,
            low=close - spread,
            close=close,
            volume=1000.0 + float(index % 1000),
        )


def _run_case(candle_count: int) -> None:
    engine = SwingEngine(
        config=SwingConfig(
            left_bars=2,
            right_bars=2,
            minimum_distance=2,
            minimum_price_move=0.00005,
            minimum_atr=0.0,
            adaptive_window=False,
            equal_high_threshold=0.0001,
            equal_low_threshold=0.0001,
        ),
        event_bus=EventBus(),
    )

    tracemalloc.start()
    cpu_start = process_time()
    wall_start = perf_counter()
    metrics = engine.run(_candle_stream(candle_count))
    wall_elapsed = perf_counter() - wall_start
    cpu_elapsed = process_time() - cpu_start
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    LOGGER.info("candles=%d", candle_count)
    LOGGER.info("elapsed_seconds=%.6f", wall_elapsed)
    LOGGER.info("cpu_seconds=%.6f", cpu_elapsed)
    LOGGER.info("swings_per_second=%.2f", metrics.swings_per_second)
    LOGGER.info("swings_count=%d", metrics.swings_count)
    LOGGER.info("peak_memory_bytes=%d", peak_memory)
    LOGGER.info("current_memory_bytes=%d", current_memory)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for candle_count in (1_000_000, 5_000_000, 10_000_000):
        _run_case(candle_count)


if __name__ == "__main__":
    main()
