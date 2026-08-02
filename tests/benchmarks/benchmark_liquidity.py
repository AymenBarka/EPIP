"""Liquidity throughput and memory benchmark for 100k/1M structures."""

import logging
import tracemalloc
from time import perf_counter

from epip.core.event_bus import EventBus
from epip.liquidity import LiquidityConfig, LiquidityEngine
from tests.liquidity.helpers import sequence, structure

LOGGER = logging.getLogger(__name__)


def run_case(count: int) -> None:
    engine = LiquidityEngine(config=LiquidityConfig(), event_bus=EventBus())
    seq = sequence()
    state = structure()
    tracemalloc.start()
    started = perf_counter()
    for _ in range(count):
        engine.process(state, seq)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LOGGER.info(
        "structures=%d throughput=%.2f/s latency=%.8fs peak_memory=%d",
        count,
        count / elapsed,
        elapsed / count,
        peak,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for count in (100_000, 1_000_000):
        run_case(count)


if __name__ == "__main__":
    main()
