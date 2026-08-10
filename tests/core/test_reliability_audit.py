from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from epip.core.circuit_breaker import CircuitBreakerState
from epip.core.fallback import AvailabilityLevel, FallbackAction, ServiceCapability
from epip.core.reliability import FailureBoundary, FailureCategory
from epip.core.reliability_audit import (
    RELIABILITY_AUDIT_REGISTRY,
    AvailabilityObservation,
    CircuitBreakerObservation,
    FailureMetric,
    FailureObservation,
    FallbackObservation,
    ReliabilityAuditEntry,
    ReliabilityAuditManager,
    ReliabilityAuditRegistry,
    ReliabilityHistory,
    ReliabilityObservation,
    RetryObservation,
)
from epip.core.retry import RetryClassification


def _observations() -> tuple[ReliabilityObservation, ...]:
    return (
        FailureObservation(
            4,
            "provider",
            FailureCategory.TRANSIENT_ERROR,
            "epip.core.exceptions.ProviderError",
            FailureBoundary.PROVIDER,
        ),
        RetryObservation(
            5,
            "temporary_external_failure",
            True,
            RetryClassification.RETRYABLE,
        ),
        RetryObservation(
            6,
            "non_retryable_exception",
            False,
            RetryClassification.NEVER_RETRY,
        ),
        CircuitBreakerObservation(7, "provider", CircuitBreakerState.OPEN),
        FallbackObservation(
            8,
            "cached_value",
            FallbackAction.CACHED_VALUE,
            True,
            AvailabilityLevel.DEGRADED,
        ),
        AvailabilityObservation(
            9,
            "market-data",
            AvailabilityLevel.UNAVAILABLE,
            (ServiceCapability.CACHE_READ,),
        ),
    )


def test_official_registry_is_complete_and_consistent() -> None:
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    snapshot = manager.snapshot(10)

    result = manager.audit(snapshot)

    assert len(RELIABILITY_AUDIT_REGISTRY) == 2
    assert result.entries_checked == 2
    assert result.violations == ()
    assert result.diagnostics.valid


def test_snapshot_is_deterministic_and_descriptive_only() -> None:
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)

    first = manager.snapshot(10, reversed(_observations()))
    second = manager.snapshot(10, _observations())

    assert first == second
    assert first.statistics.failure_count == 1
    assert first.statistics.retry_count == 1
    assert first.statistics.retry_denied == 1
    assert first.statistics.fallback_count == 1
    assert first.statistics.degraded_mode_count == 1
    assert first.statistics.availability_distribution == (
        ("degraded", 1),
        ("unavailable", 1),
    )
    assert first.statistics.circuit_breaker_distribution == (("open", 1),)
    assert first.statistics.failure_category_distribution == (("transient_error", 1),)


def test_report_is_immutable_comparable_and_canonical_json() -> None:
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    snapshot = manager.snapshot(10, _observations())
    history = ReliabilityHistory((snapshot,))

    first = manager.report(snapshot, history)
    second = manager.report(snapshot, history)

    assert first == second
    assert first.to_json() == second.to_json()
    assert json.loads(first.to_json())["summary"] == first.summary
    assert tuple(metric.name for metric in first.metrics[:5]) == (
        "failure_count",
        "retry_count",
        "retry_denied",
        "fallback_count",
        "degraded_mode_count",
    )
    with pytest.raises(FrozenInstanceError):
        first.summary = "changed"  # type: ignore[misc]


def test_missing_and_contradictory_contracts_are_reported() -> None:
    entry = ReliabilityAuditEntry(
        "invalid",
        "missing-reliability",
        "missing-exception",
        "missing-retry",
        "missing-circuit",
        "missing-fallback",
        FailureBoundary.REPLAY_RUN,
    )
    manager = ReliabilityAuditManager(ReliabilityAuditRegistry((entry,)))

    codes = {item.code for item in manager.audit(manager.snapshot(0)).violations}

    assert codes == {
        "MISSING_RELIABILITY_CONTRACT",
        "MISSING_EXCEPTION_CONTRACT",
        "MISSING_RETRY_CONTRACT",
        "MISSING_CIRCUIT_BREAKER_CONTRACT",
        "MISSING_FALLBACK_CONTRACT",
    }


def test_invalid_boundary_and_policy_links_are_reported() -> None:
    official = RELIABILITY_AUDIT_REGISTRY["external_boundary"]
    entry = ReliabilityAuditEntry(
        "contradictory",
        official.reliability_contract,
        official.exception_contract,
        "non_retryable_exception",
        official.circuit_breaker_contract,
        official.fallback_contract,
        FailureBoundary.REPLAY_RUN,
    )
    manager = ReliabilityAuditManager(ReliabilityAuditRegistry((entry,)))

    codes = [item.code for item in manager.audit(manager.snapshot(0)).violations]

    assert codes.count("CONTRACT_CONTRADICTION") == 2
    assert "INVALID_BOUNDARY" in codes


def test_incompatible_observations_are_reported_without_action() -> None:
    observations = (
        RetryObservation(
            1,
            "non_retryable_exception",
            True,
            RetryClassification.NEVER_RETRY,
        ),
        CircuitBreakerObservation(2, "unknown-circuit", CircuitBreakerState.OPEN, False),
        FallbackObservation(
            3,
            "unknown-fallback",
            FallbackAction.CACHED_VALUE,
            True,
            AvailabilityLevel.DEGRADED,
            False,
        ),
    )
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)

    codes = {item.code for item in manager.audit(manager.snapshot(4, observations)).violations}

    assert "INCOMPATIBLE_RETRY" in codes
    assert "INCOHERENT_CIRCUIT_BREAKER" in codes
    assert "INCOMPATIBLE_FALLBACK" in codes
    assert "MISSING_OBSERVED_CONTRACT" in codes


def test_registry_is_immutable_deterministic_and_audit_aware() -> None:
    entry = RELIABILITY_AUDIT_REGISTRY["provider"]

    class Aware:
        reliability_audit_entry = entry

    assert RELIABILITY_AUDIT_REGISTRY.resolve(Aware()) is entry
    assert RELIABILITY_AUDIT_REGISTRY.resolve("provider") is entry
    assert tuple(RELIABILITY_AUDIT_REGISTRY) == (
        "external_boundary",
        "provider",
    )
    with pytest.raises(LookupError):
        RELIABILITY_AUDIT_REGISTRY.resolve("unknown")
    with pytest.raises(ValueError, match="unique"):
        ReliabilityAuditRegistry((entry, entry))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: FailureObservation(
            -1,
            "provider",
            FailureCategory.TRANSIENT_ERROR,
            "epip.core.exceptions.ProviderError",
            FailureBoundary.PROVIDER,
        ),
        lambda: RetryObservation(0, "", False, RetryClassification.NEVER_RETRY),
        lambda: AvailabilityObservation(
            0,
            "service",
            AvailabilityLevel.AVAILABLE,
            (ServiceCapability.READ, ServiceCapability.READ),
        ),
        lambda: FailureMetric("", 0),
        lambda: FailureMetric("metric", -1),
        lambda: FailureMetric("metric", 1, (("", "value"),)),
    ],
)
def test_invalid_observability_values_are_rejected(factory: Callable[[], object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        factory()


def test_manager_rejects_invalid_inputs() -> None:
    with pytest.raises(TypeError):
        ReliabilityAuditManager(object())  # type: ignore[arg-type]
    manager = ReliabilityAuditManager(RELIABILITY_AUDIT_REGISTRY)
    with pytest.raises(ValueError):
        manager.snapshot(-1)
    with pytest.raises(TypeError):
        manager.audit(object())  # type: ignore[arg-type]
