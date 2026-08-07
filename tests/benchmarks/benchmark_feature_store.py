from __future__ import annotations

import logging
import tracemalloc
from time import perf_counter
from typing import Any

from epip.features.feature_store import FeatureStore
from epip.features.providers.ohlc_provider import OHLCProvider

LOGGER = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    store = FeatureStore()
    store.register_provider(OHLCProvider())

    start = perf_counter()
    tracemalloc.start()

    for index in range(100_000):
        candle: dict[str, Any] = {
            "symbol": "EURUSD",
            "timeframe": "M1",
            "timestamp": f"2024-01-01T00:00:00Z-{index}",
            "open": 1.1000 + index * 0.0001,
            "high": 1.1100 + index * 0.0001,
            "low": 1.0950 + index * 0.0001,
            "close": 1.1050 + index * 0.0001,
        }
        store.build_feature_set("EURUSD", "M1", candle["timestamp"], payload=candle)

    elapsed = perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    LOGGER.info("elapsed_seconds=%.6f", elapsed)
    LOGGER.info("current_memory_bytes=%d", current)
    LOGGER.info("peak_memory_bytes=%d", peak)


if __name__ == "__main__":
    main()
