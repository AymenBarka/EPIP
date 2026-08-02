from __future__ import annotations

from epip.core.context import MarketContext
from epip.core.decision import Decision
from epip.core.events import EvidenceCreated, ScenarioCreated
from epip.core.evidence import Evidence
from epip.core.kernel import Kernel
from epip.core.plugin_context import PluginContext
from epip.core.plugin_result import PluginResult
from epip.core.registry import Registry
from epip.core.types import DecisionType, Direction


class EchoPlugin:
    name = "echo"
    priority = 5

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, context: PluginContext) -> PluginResult:
        self.calls += 1
        evidence = Evidence(
            id="ev-1",
            source=self.name,
            category="structure",
            direction=Direction.BUY,
            confidence=0.8,
            timestamp=context.market_context.timestamp,
            metadata={"plugin": self.name},
        )
        return PluginResult(
            plugin=self.name,
            execution_time=0.01,
            success=True,
            errors=(),
            warnings=(),
            generated_evidence=(evidence,),
            metadata={"calls": self.calls},
        )


class FailingPlugin:
    name = "failing"
    priority = 1

    def execute(self, context: PluginContext) -> PluginResult:
        raise RuntimeError("boom")


def test_kernel_runs_plugins_and_builds_domain_objects() -> None:
    registry = Registry()
    plugin = EchoPlugin()
    registry.register(plugin)

    kernel = Kernel(registry=registry)
    context = MarketContext(
        symbol="EURUSD",
        timeframe="M1",
        timestamp="2024-01-01T00:00:00Z",
        candles=(),
    )

    result = kernel.run(context)

    assert len(result.plugin_results) == 1
    assert result.evidence[0].source == "echo"
    assert result.scenario is not None
    assert result.hypothesis is not None
    assert result.decision is not None
    assert isinstance(result.decision, Decision)
    assert result.decision.decision_type == DecisionType.BUY

    published = kernel.event_bus.event_history()
    assert any(isinstance(item, EvidenceCreated) for item in published)
    assert any(isinstance(item, ScenarioCreated) for item in published)


def test_kernel_handles_disabled_plugins_and_failures() -> None:
    registry = Registry()
    plugin = EchoPlugin()
    failing = FailingPlugin()
    registry.register(plugin)
    registry.register(failing)
    registry.disable(plugin)

    kernel = Kernel(registry=registry)
    context = MarketContext(symbol="EURUSD", timeframe="M1", timestamp="2024-01-01T00:00:00Z")

    result = kernel.run(context)

    assert len(result.plugin_results) == 1
    assert result.plugin_results[0].success is False
    assert result.plugin_results[0].errors[0].startswith("boom")
    assert result.evidence == ()
    assert result.scenario is None
