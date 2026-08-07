"""Manual EPIP-011 Elliott analysis benchmark."""

import logging
import tracemalloc
from time import perf_counter

from epip.elliott import ElliottConfig
from epip.elliott.analyzer import ElliottAnalyzer
from tests.elliott.helpers import market_context

LOGGER = logging.getLogger(__name__)


def run_case(count: int) -> None:
    analyzer = ElliottAnalyzer(ElliottConfig())
    context = market_context()
    tracemalloc.start()
    started = perf_counter()
    alternate_count = 0
    for _ in range(count):
        alternate_count += len(analyzer.analyze(context).alternates)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LOGGER.info(
        "contexts=%d throughput=%.2f/s latency=%.8fs memory=%d alternates=%d alternate_cost=%.8fs",
        count,
        count / elapsed,
        elapsed / count,
        peak,
        alternate_count,
        elapsed / alternate_count if alternate_count else 0.0,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for count in (100_000, 1_000_000):
        run_case(count)


if __name__ == "__main__":
    main()
