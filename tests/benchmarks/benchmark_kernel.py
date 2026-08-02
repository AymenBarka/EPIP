from __future__ import annotations

from time import perf_counter

from epip.core.context import MarketContext
from epip.core.kernel import Kernel
from epip.core.plugin_context import PluginContext
from epip.core.plugin_result import PluginResult
from epip.core.registry import Registry


class BenchmarkPlugin:
    name = "benchmark"
    priority = 0

    def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(
            plugin=self.name,
            execution_time=0.0,
            success=True,
            errors=(),
            warnings=(),
            generated_evidence=(),
            metadata={},
        )


def main() -> None:
    registry = Registry()
    for _ in range(100):
        registry.register(BenchmarkPlugin())

    kernel = Kernel(registry=registry)
    context = MarketContext(symbol="EURUSD", timeframe="M1", timestamp="2024-01-01T00:00:00Z")

    start = perf_counter()
    for _ in range(100):
        kernel.run(context)
    duration = perf_counter() - start
    print(f"kernel_run_100x100_plugins={duration:.6f}s")


if __name__ == "__main__":
    main()
