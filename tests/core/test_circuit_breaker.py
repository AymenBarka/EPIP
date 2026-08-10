"""Acceptance tests for the optional deterministic circuit breaker."""

from dataclasses import FrozenInstanceError

import pytest

from epip.core.circuit_breaker import (
    CIRCUIT_BREAKER_CONTRACTS,
    CircuitBreaker,
    CircuitBreakerConfiguration,
    CircuitBreakerRegistry,
    CircuitBreakerState,
    FailureClassifier,
    FailureIsolation,
    FailureWindow,
    declared_circuit_breakers,
    get_circuit_breaker_contract,
)


def breaker(name: str = "provider") -> CircuitBreaker:
    return CircuitBreaker(get_circuit_breaker_contract(name))


def test_registry_is_complete_immutable_deterministic_and_resolvable() -> None:
    contracts = declared_circuit_breakers()
    assert contracts == tuple(sorted(contracts, key=lambda item: item.name))
    assert {item.isolation for item in contracts} == set(FailureIsolation)
    assert get_circuit_breaker_contract("provider") is CIRCUIT_BREAKER_CONTRACTS["provider"]
    with pytest.raises(FrozenInstanceError):
        contracts[0].description = "changed"  # type: ignore[misc]
    with pytest.raises(LookupError, match="no circuit-breaker contract"):
        get_circuit_breaker_contract("missing")


def test_closed_opens_after_deterministic_failure_threshold() -> None:
    item = breaker()
    for logical_time in range(3):
        assert item.allow(logical_time).permitted
        item.record_failure("provider unavailable", logical_time)
    assert item.state is CircuitBreakerState.OPEN
    assert not item.allow(3).permitted
    snapshot = item.snapshot()
    assert snapshot.statistics.failures.total == 3
    assert snapshot.statistics.failures.consecutive == 3
    assert snapshot.statistics.failure_ratio == 1.0
    assert snapshot.reason.startswith("opened:")


def test_open_moves_to_half_open_using_logical_time_only() -> None:
    item = breaker()
    for logical_time in range(3):
        item.record_failure("failure", logical_time)
    assert not item.allow(6).permitted
    decision = item.allow(7)
    assert decision.permitted
    assert decision.state is CircuitBreakerState.HALF_OPEN


def test_half_open_closes_after_success_threshold() -> None:
    item = breaker()
    for logical_time in range(3):
        item.record_failure("failure", logical_time)
    assert item.allow(7).permitted
    item.record_success("trial one", 7)
    assert item.allow(8).permitted
    item.record_success("trial two", 8)
    assert item.state is CircuitBreakerState.CLOSED
    assert item.snapshot().reason.startswith("closed:")


def test_half_open_failure_reopens_without_corruption() -> None:
    item = breaker()
    for logical_time in range(3):
        item.record_failure("failure", logical_time)
    assert item.allow(7).permitted
    item.record_failure("trial failed", 7)
    assert item.state is CircuitBreakerState.OPEN
    assert item.snapshot().reason.startswith("reopened:")


def test_forced_open_and_disabled_policies_are_explicit() -> None:
    item = breaker()
    item.transition(CircuitBreakerState.FORCED_OPEN, "operator isolation")
    assert not item.allow(0).permitted
    item.transition(CircuitBreakerState.DISABLED, "operator disabled isolation")
    assert item.allow(1).permitted
    item.transition(CircuitBreakerState.CLOSED, "operator restored protection")
    assert item.state is CircuitBreakerState.CLOSED


def test_invalid_transition_and_non_monotonic_time_are_rejected() -> None:
    item = breaker()
    with pytest.raises(ValueError, match="invalid circuit-breaker transition"):
        item.transition(CircuitBreakerState.HALF_OPEN, "invalid")
    item.allow(2)
    with pytest.raises(ValueError, match="monotonic"):
        item.allow(1)


def test_half_open_trial_limit_is_enforced() -> None:
    item = breaker()
    for logical_time in range(3):
        item.record_failure("failure", logical_time)
    assert item.allow(7).permitted
    assert item.allow(8).permitted
    assert item.allow(9).permitted
    assert not item.allow(10).permitted


def test_failure_window_is_immutable_bounded_and_reports_ratio() -> None:
    original = FailureWindow()
    updated = original.append(True, 2).append(False, 2).append(True, 2)
    assert original.outcomes == ()
    assert updated.outcomes == (False, True)
    assert updated.failure_ratio == 0.5
    with pytest.raises(ValueError, match="positive"):
        updated.append(True, 0)


def test_failure_classification_uses_all_h006_contracts() -> None:
    contract = get_circuit_breaker_contract("provider")
    assert FailureClassifier.counts_as_failure(
        contract.retry_contract,
        contract.failure_contract,
        contract.exception_contract,
    )
    with pytest.raises(TypeError, match="all three"):
        FailureClassifier.counts_as_failure(
            object(),  # type: ignore[arg-type]
            contract.failure_contract,
            contract.exception_contract,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("failure_threshold", 0, "failure threshold"),
        ("success_threshold", 0, "success threshold"),
        ("window_size", 0, "window size"),
        ("minimum_samples", 0, "minimum samples"),
        ("failure_ratio_threshold", 0.0, "failure ratio threshold"),
        ("logical_open_duration", 0, "logical open duration"),
        ("half_open_max_trials", 0, "half-open maximum trials"),
        ("half_open_failure_threshold", 0, "half-open failure threshold"),
    ),
)
def test_invalid_configurations_are_rejected(field: str, value: object, message: str) -> None:
    values: dict[str, object] = {
        "failure_threshold": 3,
        "success_threshold": 2,
        "window_size": 10,
        "minimum_samples": 3,
        "failure_ratio_threshold": 0.5,
        "logical_open_duration": 5,
        "half_open_max_trials": 3,
        "half_open_failure_threshold": 1,
    }
    values[field] = value
    with pytest.raises(ValueError, match=message):
        CircuitBreakerConfiguration(**values)  # type: ignore[arg-type]


def test_registry_rejects_duplicates_and_audits_missing_contracts() -> None:
    item = get_circuit_breaker_contract("provider")
    with pytest.raises(ValueError, match="unique"):
        CircuitBreakerRegistry((item, item))
    audit = CircuitBreakerRegistry((item,)).audit(("provider", "missing"))
    assert audit.contracts_checked == 1
    assert audit.diagnostics.messages == ("missing circuit-breaker contract: missing",)
    assert not audit.diagnostics.valid
    assert CIRCUIT_BREAKER_CONTRACTS.audit().diagnostics.valid


def test_snapshot_history_is_immutable_and_contains_transition_reasons() -> None:
    item = breaker()
    item.transition(CircuitBreakerState.FORCED_OPEN, "manual isolation")
    snapshot = item.snapshot()
    assert snapshot.history[-1] == (CircuitBreakerState.FORCED_OPEN, "manual isolation")
    with pytest.raises(FrozenInstanceError):
        snapshot.reason = "changed"  # type: ignore[misc]
