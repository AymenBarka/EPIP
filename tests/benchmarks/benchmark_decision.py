"""Manual EPIP-012 Decision Engine analysis benchmark."""

import logging
import tracemalloc
from time import perf_counter

from epip.decision.analyzer import DecisionAnalyzer
from epip.decision.config import DecisionConfig
from epip.decision.rule_engine import DecisionRuleEngine
from tests.decision.helpers import snapshots

LOGGER = logging.getLogger(__name__)


def run_case(count: int) -> None:
    config = DecisionConfig()
    analyzer = DecisionAnalyzer(config)
    rules = DecisionRuleEngine()
    context, elliott = snapshots()
    rule_started = perf_counter()
    for _ in range(count):
        rules.evaluate(context, elliott, config)
    rule_elapsed = perf_counter() - rule_started
    tracemalloc.start()
    started = perf_counter()
    for _ in range(count):
        analyzer.analyze(context, elliott)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LOGGER.info(
        "decisions=%d throughput=%.2f/s latency=%.8fs memory=%d rule_time=%.8fs",
        count,
        count / elapsed,
        elapsed / count,
        peak,
        rule_elapsed / count,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for count in (100_000, 1_000_000):
        run_case(count)


if __name__ == "__main__":
    main()
