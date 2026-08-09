"""Institutional reliability validation and deterministic fault injection."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

import pytest

from epip.core.circuit_breaker import (
    CIRCUIT_BREAKER_CONTRACTS,
    CircuitBreaker,
    CircuitBreakerState,
)
from epip.core.exceptions import (
    AdapterError,
    EventBusError,
    ExternalSystemError,
    FrameworkError,
    InfrastructureError,
    KernelError,
    PluginError,
    ProviderError,
    RecoverableError,
    ReplayError,
    RetryableError,
    TimeoutError,
)
from epip.core.fallback import (
    DEGRADATION_CONTRACTS,
    AvailabilityLevel,
    FallbackContext,
    FallbackRuntime,
)
from epip.core.reliability import FailureResponsibility
from epip.core.reliability_audit import (
    RELIABILITY_AUDIT_REGISTRY,
    ReliabilityAuditManager,
)
from epip.core.retry import (
    RETRY_CONTRACTS,
    RetryClassification,
    RetryCondition,
    RetryContext,
    RetryDecision,
    RetryTrigger,
)

CI_DECISIONS = 100_000
COMBINED_CYCLES = 1_000


class FaultTarget(str, Enum):
    """Deterministic fault targets exercised by the validation campaign."""

    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_SLOW = "provider_slow"
    PROVIDER_INTERMITTENT = "provider_intermittent"
    ADAPTER_UNAVAILABLE = "adapter_unavailable"
    PLUGIN = "plugin"
    USER_CALLBACK = "user_callback"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    EVENT_BUS = "event_bus"
    REPLAY = "replay"
    KERNEL = "kernel"
    RECOVERY = "recovery"
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK = "fallback"


FAULT_TYPES: dict[FaultTarget, type[BaseException]] = {
    FaultTarget.PROVIDER_UNAVAILABLE: ProviderError,
    FaultTarget.PROVIDER_SLOW: TimeoutError,
    FaultTarget.PROVIDER_INTERMITTENT: ProviderError,
    FaultTarget.ADAPTER_UNAVAILABLE: AdapterError,
    FaultTarget.PLUGIN: PluginError,
    FaultTarget.USER_CALLBACK: FrameworkError,
    FaultTarget.NETWORK: ExternalSystemError,
    FaultTarget.FILESYSTEM: InfrastructureError,
    FaultTarget.EVENT_BUS: EventBusError,
    FaultTarget.REPLAY: ReplayError,
    FaultTarget.KERNEL: KernelError,
    FaultTarget.RECOVERY: RecoverableError,
    FaultTarget.RETRY: RetryableError,
    FaultTarget.CIRCUIT_BREAKER: ExternalSystemError,
    FaultTarget.FALLBACK: RecoverableError,
}
FAULT_EXCEPTIONS = tuple(FAULT_TYPES.values())


class DeterministicFaultInjector:
    """Configurable test-only injector driven exclusively by logical ticks."""

    __slots__ = ("_period", "_target")

    def __init__(self, target: FaultTarget, period: int = 1) -> None:
        if period < 1:
            raise ValueError("period must be positive")
        self._target = target
        self._period = period

    def evaluate(self, logical_tick: int) -> str:
        """Return success or raise the configured typed fault deterministically."""

        if logical_tick % self._period:
            return "ok"
        error_type = FAULT_TYPES[self._target]
        raise error_type(f"{self._target.value}@{logical_tick}")


def _capture(injector: DeterministicFaultInjector, cycles: int) -> tuple[str, ...]:
    outcomes: list[str] = []
    for tick in range(1, cycles + 1):
        try:
            outcomes.append(injector.evaluate(tick))
        except FAULT_EXCEPTIONS as error:
            outcomes.append(f"{type(error).__name__}:{error}")
    return tuple(outcomes)


def _retry_decision(context: RetryContext) -> RetryDecision:
    contract = RETRY_CONTRACTS[context.contract_name]
    eligible = contract.classification not in {
        RetryClassification.NON_RETRYABLE,
        RetryClassification.NEVER_RETRY,
    }
    allowed = (
        eligible
        and context.condition in contract.conditions
        and context.attempt_number < contract.configuration.maximum_attempts
        and context.elapsed_duration < contract.configuration.maximum_elapsed_duration
    )
    return RetryDecision(allowed, contract.responsibility, contract.classification.value)


@pytest.mark.parametrize("target", tuple(FaultTarget))
def test_fault_injection_is_typed_configurable_and_reproducible(target: FaultTarget) -> None:
    first = _capture(DeterministicFaultInjector(target, period=3), 12)
    second = _capture(DeterministicFaultInjector(target, period=3), 12)

    assert first == second
    assert len(first) == 12
    assert sum(item != "ok" for item in first) == 4
    assert issubclass(FAULT_TYPES[target], BaseException)


def test_ci_scale_retry_decisions_are_stable() -> None:
    context = RetryContext(
        "temporary_external_failure",
        RetryTrigger.EXCEPTION,
        RetryCondition.TEMPORARY_EXTERNAL_FAILURE,
        0,
        0.0,
    )
    expected = _retry_decision(context)

    decisions = tuple(_retry_decision(context) for _ in range(CI_DECISIONS))

    assert len(decisions) == CI_DECISIONS
    assert all(item == expected for item in decisions)


def test_ci_scale_circuit_breaker_decisions_are_stable() -> None:
    breaker = CircuitBreaker(CIRCUIT_BREAKER_CONTRACTS["provider"])

    decisions = tuple(breaker.allow(tick) for tick in range(CI_DECISIONS))

    assert len(decisions) == CI_DECISIONS
    assert all(item.permitted for item in decisions)
    assert breaker.snapshot().state is CircuitBreakerState.CLOSED


def test_ci_scale_fallback_decisions_are_bounded_and_stable() -> None:
    runtime = FallbackRuntime(DEGRADATION_CONTRACTS["fail"])

    results = []
    for tick in range(CI_DECISIONS):
        context = FallbackContext(
            tick,
            AvailabilityLevel.AVAILABLE,
            CircuitBreakerState.CLOSED,
            False,
            False,
        )
        results.append(runtime.evaluate(context).decision)

    snapshot = runtime.snapshot()
    assert len(results) == CI_DECISIONS
    assert not any(item.apply for item in results)
    assert snapshot.statistics.evaluations == CI_DECISIONS
    assert len(snapshot.history) <= DEGRADATION_CONTRACTS["fail"].configuration.history_limit


def test_ci_scale_audit_snapshots_reports_and_diagnostics_are_stable() -> None:
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    last_snapshot = None
    for tick in range(CI_DECISIONS):
        last_snapshot = manager.snapshot(tick)
    assert last_snapshot is not None
    assert last_snapshot.logical_time == CI_DECISIONS - 1

    reports = tuple(manager.report(last_snapshot) for _ in range(CI_DECISIONS))

    assert len(reports) == CI_DECISIONS
    assert all(report == reports[0] for report in reports)
    assert all(report.diagnostics == reports[0].diagnostics for report in reports)
    assert reports[0].to_json() == reports[-1].to_json()


def _combined_campaign() -> tuple[object, ...]:
    breaker = CircuitBreaker(CIRCUIT_BREAKER_CONTRACTS["external_boundary"])
    fallback = FallbackRuntime(DEGRADATION_CONTRACTS["cached_value"])
    audit = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    outcomes: list[object] = []
    for tick in range(COMBINED_CYCLES):
        circuit_decision = breaker.allow(tick)
        fallback_result = fallback.evaluate(
            FallbackContext(
                tick,
                AvailabilityLevel.DEGRADED if tick % 5 == 0 else AvailabilityLevel.AVAILABLE,
                breaker.state,
                False,
                tick % 5 == 0,
                cached_value=("cached", tick),
            )
        )
        snapshot = audit.snapshot(tick, circuit_breakers=(breaker.snapshot(),))
        outcomes.append(
            (
                circuit_decision,
                fallback_result,
                audit.report(snapshot).to_json(),
            )
        )
    return tuple(outcomes)


def test_combined_reliability_cycles_are_byte_deterministic() -> None:
    assert _combined_campaign() == _combined_campaign()


def test_validation_does_not_retain_transient_contexts_or_reports() -> None:
    fallback = FallbackRuntime(DEGRADATION_CONTRACTS["fail"])
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    context = FallbackContext(
        0,
        AvailabilityLevel.AVAILABLE,
        CircuitBreakerState.CLOSED,
        False,
        False,
    )
    result = fallback.evaluate(context)
    snapshot = manager.snapshot(0, fallbacks=(fallback.snapshot(),))
    report = manager.report(snapshot)

    runtime_references = tuple(vars(fallback).values())
    assert all(value is not context and value is not result for value in runtime_references)
    assert manager._registry is RELIABILITY_AUDIT_REGISTRY
    assert report.snapshots == (snapshot,)
    assert report.statistics == snapshot.statistics


def test_h001_to_h006_contracts_remain_composable() -> None:
    retry = RETRY_CONTRACTS["temporary_external_failure"]
    circuit = CIRCUIT_BREAKER_CONTRACTS["external_boundary"]
    fallback = DEGRADATION_CONTRACTS["cached_value"]
    audit = RELIABILITY_AUDIT_REGISTRY["external_boundary"]

    assert circuit.retry_contract is retry
    assert fallback.retry_contract is retry
    assert audit.component == "external_boundary"
    assert retry.responsibility is FailureResponsibility.EXTERNAL_SYSTEM


def test_fault_campaign_never_reads_wall_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("wall clock access is forbidden")

    monkeypatch.setattr("time.time", forbidden)
    monkeypatch.setattr("time.monotonic", forbidden)
    campaign: Callable[[], tuple[str, ...]] = lambda: _capture(
        DeterministicFaultInjector(FaultTarget.PROVIDER_INTERMITTENT, period=2), 20
    )

    assert campaign() == campaign()
