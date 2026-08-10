import logging
import tracemalloc
from time import perf_counter

from epip.core.event_bus import EventBus
from epip.fibonacci import FibonacciConfig, FibonacciEngine
from tests.fibonacci.helpers import inputs

LOGGER = logging.getLogger(__name__)


def run_case(count: int) -> None:
    engine = FibonacciEngine(config=FibonacciConfig(), event_bus=EventBus())
    swings, market_structure, liquidity = inputs()
    tracemalloc.start()
    start = perf_counter()
    for _ in range(count):
        engine.process(swings, market_structure, liquidity)
    elapsed = perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LOGGER.info(
        "structures=%d throughput=%.2f/s latency=%.8fs memory=%d",
        count,
        count / elapsed,
        elapsed / count,
        peak,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for n in (100_000, 1_000_000):
        run_case(n)


if __name__ == "__main__":
    main()
