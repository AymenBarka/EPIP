from __future__ import annotations

from threading import Event, Thread
from time import sleep

import pytest

from epip.core.context import MarketContext
from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent
from epip.core.evidence import Evidence
from epip.core.kernel import Kernel
from epip.core.kernel_transaction import KernelPipelineBusyError
from epip.core.plugin_context import PluginContext
from epip.core.plugin_result import PluginResult
from epip.core.registry import Registry
from epip.core.types import Direction


def _context() -> MarketContext:
    return MarketContext("EURUSD", "M1", "2026-01-01T00:00:00Z")


def _evidence(context: PluginContext, name: str) -> Evidence:
    return Evidence(
        id=f"evidence-{name}",
        source=name,
        category="kernel-atomicity",
        direction=Direction.BUY,
        confidence=0.75,
        timestamp=context.market_context.timestamp,
        clock=context.clock,
        id_generator=context.id_generator,
    )


class _Plugin:
    priority = 0

    def __init__(self, name: str, action: str = "success") -> None:
        self.name = name
        self.action = action
        self.calls = 0
        self.observed_real_events = -1

    def execute(self, context: PluginContext) -> PluginResult | object:
        self.calls += 1
        if self.action == "exception":
            raise RuntimeError("plugin failure")
        if self.action == "base_exception":
            raise _PluginAbort("plugin abort")
        if self.action == "invalid":
            return object()
        if self.action == "slow":
            sleep(0.05)
        if self.action == "mutate_registry":
            assert context.registry is not None
            context.registry.unregister(self.name)
        context.event_bus.publish(
            BaseEvent(id=f"plugin-{self.name}", timestamp=context.market_context.timestamp)
        )
        return PluginResult(
            plugin=self.name,
            execution_time=0.0,
            success=True,
            generated_evidence=(_evidence(context, self.name),),
        )


class _PluginAbort(BaseException):
    pass


def test_pipeline_commits_results_and_events_in_plugin_order() -> None:
    registry = Registry()
    first = _Plugin("first")
    second = _Plugin("second")
    registry.register(first, priority=1)
    registry.register(second, priority=2)
    bus = EventBus()
    observed: list[str] = []
    bus.subscribe(object, lambda event: observed.append(getattr(event, "id", "")))

    result = Kernel(registry=registry, event_bus=bus).run(_context())

    assert tuple(item.plugin for item in result.plugin_results) == ("first", "second")
    assert observed[:2] == ["plugin-first", "plugin-second"]
    assert len(result.evidence) == 2


@pytest.mark.parametrize("action", ["exception", "invalid"])
def test_failure_rolls_back_prior_results_events_and_stops_pipeline(action: str) -> None:
    registry = Registry()
    first = _Plugin("first")
    failing = _Plugin("failing", action)
    after = _Plugin("after")
    registry.register(first, priority=1)
    registry.register(failing, priority=2)
    registry.register(after, priority=3)
    bus = EventBus()

    result = Kernel(registry=registry, event_bus=bus).run(_context())

    assert len(result.plugin_results) == 1
    assert result.plugin_results[0].plugin == "failing"
    assert result.plugin_results[0].success is False
    assert result.evidence == ()
    assert result.scenario is None
    assert bus.event_history() == ()
    assert first.calls == 1
    assert after.calls == 0


def test_base_exception_rolls_back_and_kernel_recovers() -> None:
    registry = Registry()
    failing = _Plugin("abort", "base_exception")
    after = _Plugin("after")
    registry.register(failing, priority=1)
    registry.register(after, priority=2)
    kernel = Kernel(registry=registry)

    with pytest.raises(_PluginAbort):
        kernel.run(_context())

    assert kernel.event_bus.event_history() == ()
    assert after.calls == 0
    registry.unregister(failing)
    assert kernel.run(_context()).plugin_results[0].success is True


def test_plugin_registry_mutation_is_confined_to_its_context() -> None:
    registry = Registry()
    plugin = _Plugin("isolated", "mutate_registry")
    registry.register(plugin)

    result = Kernel(registry=registry).run(_context())

    assert result.plugin_results[0].success is True
    assert registry.exists(plugin)


def test_slow_plugin_rejects_concurrent_execution_without_deadlock() -> None:
    registry = Registry()
    plugin = _Plugin("slow", "slow")
    registry.register(plugin)
    kernel = Kernel(registry=registry)
    started = Event()
    finished = Event()

    def run() -> None:
        started.set()
        kernel.run(_context())
        finished.set()

    worker = Thread(target=run)
    worker.start()
    started.wait(timeout=1.0)
    sleep(0.01)
    with pytest.raises(KernelPipelineBusyError):
        kernel.run(_context())
    worker.join(timeout=1.0)

    assert finished.is_set()


def test_reentrant_plugin_is_rejected_and_outer_pipeline_can_commit() -> None:
    registry = Registry()
    kernel = Kernel(registry=registry)

    class ReentrantPlugin:
        name = "reentrant"
        priority = 0

        def execute(self, context: PluginContext) -> PluginResult:
            with pytest.raises(KernelPipelineBusyError):
                kernel.run(context.market_context)
            return PluginResult(plugin=self.name, execution_time=0.0, success=True)

    registry.register(ReentrantPlugin())

    assert kernel.run(_context()).plugin_results[0].success is True


def test_plugin_thread_cannot_enter_active_kernel_and_can_be_joined() -> None:
    registry = Registry()
    kernel = Kernel(registry=registry)

    class ThreadPlugin:
        name = "thread"
        priority = 0

        def execute(self, context: PluginContext) -> PluginResult:
            errors: list[type[BaseException]] = []

            def reenter() -> None:
                try:
                    kernel.run(context.market_context)
                except BaseException as exc:  # noqa: BLE001 - asserted boundary
                    errors.append(type(exc))

            worker = Thread(target=reenter)
            worker.start()
            worker.join(timeout=1.0)
            assert not worker.is_alive()
            assert errors == [KernelPipelineBusyError]
            return PluginResult(plugin=self.name, execution_time=0.0, success=True)

    registry.register(ThreadPlugin())

    assert kernel.run(_context()).plugin_results[0].success is True


def test_plugin_events_are_not_observable_before_pipeline_commit() -> None:
    registry = Registry()
    bus = EventBus()
    observed: list[str] = []
    bus.subscribe(object, lambda event: observed.append(getattr(event, "id", "")))

    class ObservingPlugin(_Plugin):
        def execute(self, context: PluginContext) -> PluginResult | object:
            self.observed_real_events = len(observed)
            return super().execute(context)

    first = ObservingPlugin("first")
    second = ObservingPlugin("second")
    registry.register(first, priority=1)
    registry.register(second, priority=2)

    Kernel(registry=registry, event_bus=bus).run(_context())

    assert first.observed_real_events == 0
    assert second.observed_real_events == 0
    assert observed
