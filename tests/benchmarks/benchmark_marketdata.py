from __future__ import annotations

import logging
import tracemalloc
from time import perf_counter

from epip.marketdata.datasource_models import HistoryRequest
from epip.marketdata.providers.fake_provider import FakeProvider

LOGGER = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    provider = FakeProvider(
        symbols=("EURUSD",),
        timeframes=("M1",),
        candles_per_series=100_000,
        cache_expiration_seconds=120.0,
        cache_max_entries=256,
    )
    provider.connect()

    request = HistoryRequest(
        symbol="EURUSD", timeframe="M1", limit=100_000, page=1, page_size=100_000
    )

    tracemalloc.start()

    miss_start = perf_counter()
    miss_response = provider.history(request)
    miss_elapsed = perf_counter() - miss_start

    hit_start = perf_counter()
    hit_response = provider.history(request)
    hit_elapsed = perf_counter() - hit_start

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stats = provider.cache_stats()

    LOGGER.info("candles=%d", len(miss_response.chunk.candles))
    LOGGER.info("cache_hit=%d", stats.history_hits)
    LOGGER.info("cache_miss=%d", stats.history_misses)
    LOGGER.info("miss_seconds=%.6f", miss_elapsed)
    LOGGER.info("hit_seconds=%.6f", hit_elapsed)
    LOGGER.info("avg_miss_seconds=%.9f", miss_elapsed / max(1, len(miss_response.chunk.candles)))
    LOGGER.info("avg_hit_seconds=%.9f", hit_elapsed / max(1, len(hit_response.chunk.candles)))
    LOGGER.info("current_memory_bytes=%d", current)
    LOGGER.info("peak_memory_bytes=%d", peak)

    provider.disconnect()


if __name__ == "__main__":
    main()
