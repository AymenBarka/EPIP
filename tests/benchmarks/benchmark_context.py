"""Manual EPIP-010 throughput, latency, and memory benchmark."""

import logging
import tracemalloc
from time import perf_counter

from epip.context import MarketContextBuilder
from tests.context.helpers import official_inputs

LOGGER = logging.getLogger(__name__)


def run_case(count: int) -> None:
    builder = MarketContextBuilder()
    inputs = official_inputs()
    tracemalloc.start()
    started = perf_counter()
    for _ in range(count):
        builder.build(*inputs)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LOGGER.info(
        "contexts=%d throughput=%.2f/s latency=%.8fs memory=%d",
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
