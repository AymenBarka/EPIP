"""Tests for optional deterministic graceful-degradation infrastructure."""

from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core.circuit_breaker import CircuitBreakerState
from epip.core.fallback import (
    DEGRADATION_CONTRACTS,
    AvailabilityLevel,
    FallbackAction,
    FallbackAware,
    FallbackConfiguration,
    FallbackContext,
    FallbackPolicy,
    FallbackRegistry,
    FallbackRuntime,
    ServiceCapability,
    declared_fallback_contracts,
    get_fallback_contract,
    transition_availability,
)


def _context(**changes: object) -> FallbackContext:
    values: dict[str, object] = {
        "logical_time": 1,
        "availability": AvailabilityLevel.UNAVAILABLE,
        "circuit_state": CircuitBreakerState.OPEN,
        "retries_exhausted": True,
        "failure_classified": True,
        "default_value": "default",
        "empty_value": (),
        "cached_value": "cached",
        "last_known_value": "last",
        "degraded_value": "degraded",
        "secondary_value": "secondary",
        "custom_value": "custom",
    }
    values.update(changes)
    return FallbackContext(**values)  # type: ignore[arg-type]


def test_registry_is_complete_immutable_and_deterministic() -> None:
    contracts = declared_fallback_contracts()
    assert len(contracts) == 14
    assert contracts == tuple(sorted(contracts, key=lambda item: item.name))
    assert {item.policy for item in contracts} == set(FallbackPolicy)
    assert {item.action for item in contracts} == set(FallbackAction)
    with pytest.raises(TypeError):
        DEGRADATION_CONTRACTS["new"] = contracts[0]  # type: ignore[index]


def test_registry_resolves_name_and_aware_component() -> None:
    contract = get_fallback_contract("cached_value")

    class Aware:
        fallback_contract = contract

    assert isinstance(Aware(), FallbackAware)
    assert get_fallback_contract(Aware()) is contract
    with pytest.raises(LookupError, match="missing"):
        get_fallback_contract("missing")


@pytest.mark.parametrize(
    ("name", "field", "expected", "partial", "empty", "skipped"),
    (
        ("cached_value", "cached_value", "cached", False, False, False),
        ("last_known_value", "last_known_value", "last", False, False, False),
        ("secondary_provider", "secondary_value", "secondary", False, False, False),
        ("secondary_adapter", "secondary_value", "secondary", False, False, False),
        ("default_response", "default_value", "default", False, False, False),
        ("empty_response", "empty_value", (), False, True, False),
        ("partial_response", "degraded_value", "degraded", True, False, False),
        ("degraded_mode", "degraded_value", "degraded", False, False, False),
        ("read_only_mode", "degraded_value", "degraded", False, False, False),
        ("disabled_mode", "custom_value", None, False, False, True),
        ("skip_operation", "custom_value", None, False, False, True),
        ("manual_fallback", "custom_value", "custom", False, False, False),
        ("custom_fallback", "custom_value", "custom", False, False, False),
    ),
)
def test_explicit_fallback_strategies(
    name: str,
    field: str,
    expected: object,
    partial: bool,
    empty: bool,
    skipped: bool,
) -> None:
    result = FallbackRuntime(get_fallback_contract(name)).evaluate(_context())
    assert getattr(_context(), field) is not None or expected is None
    assert result.value == expected
    assert (result.partial, result.empty, result.skipped) == (partial, empty, skipped)
    assert result.decision.apply


def test_fail_policy_never_applies_a_fallback() -> None:
    result = FallbackRuntime(get_fallback_contract("fail")).evaluate(_context())
    assert not result.decision.apply
    assert result.value is None


def test_healthy_context_does_not_implicitly_degrade() -> None:
    context = _context(
        availability=AvailabilityLevel.AVAILABLE,
        circuit_state=CircuitBreakerState.CLOSED,
        retries_exhausted=False,
        failure_classified=False,
    )
    result = FallbackRuntime(get_fallback_contract("cached_value")).evaluate(context)
    assert not result.decision.apply
    assert result.decision.availability is AvailabilityLevel.AVAILABLE


def test_manual_fallback_requires_explicit_request_for_healthy_service() -> None:
    context = _context(
        availability=AvailabilityLevel.AVAILABLE,
        circuit_state=CircuitBreakerState.CLOSED,
        retries_exhausted=False,
        failure_classified=False,
        manual_request=True,
    )
    result = FallbackRuntime(get_fallback_contract("manual_fallback")).evaluate(context)
    assert result.decision.apply
    assert result.value == "custom"


def test_read_only_and_disabled_contracts_expose_capability_loss() -> None:
    read_only = get_fallback_contract("read_only_mode")
    disabled = get_fallback_contract("disabled_mode")
    assert read_only.remaining_capabilities == (ServiceCapability.READ,)
    assert read_only.disabled_features == ("write",)
    assert disabled.remaining_capabilities == ()
    assert disabled.disabled_features == ("feature",)


def test_availability_transitions_are_explicit_and_deterministic() -> None:
    assert (
        transition_availability(AvailabilityLevel.AVAILABLE, AvailabilityLevel.DEGRADED)
        is AvailabilityLevel.DEGRADED
    )
    with pytest.raises(ValueError, match="invalid availability transition"):
        transition_availability(AvailabilityLevel.DISABLED, AvailabilityLevel.READ_ONLY)
    with pytest.raises(TypeError, match="declared levels"):
        transition_availability("available", AvailabilityLevel.DEGRADED)  # type: ignore[arg-type]


def test_snapshot_is_immutable_bounded_and_auditable() -> None:
    contract = replace(
        get_fallback_contract("cached_value"),
        configuration=FallbackConfiguration(history_limit=2),
    )
    runtime = FallbackRuntime(contract)
    runtime.evaluate(_context(logical_time=1))
    runtime.evaluate(_context(logical_time=2))
    runtime.evaluate(_context(logical_time=3))
    snapshot = runtime.snapshot()
    assert snapshot.statistics.evaluations == 3
    assert snapshot.statistics.applied == 3
    assert len(snapshot.history) == 2
    with pytest.raises(FrozenInstanceError):
        snapshot.availability = AvailabilityLevel.AVAILABLE  # type: ignore[misc]


def test_logical_time_must_be_valid_and_monotonic() -> None:
    runtime = FallbackRuntime(get_fallback_contract("cached_value"))
    runtime.evaluate(_context(logical_time=2))
    with pytest.raises(ValueError, match="monotonic"):
        runtime.evaluate(_context(logical_time=1))
    with pytest.raises(ValueError, match="non-negative"):
        _context(logical_time=-1)


@pytest.mark.parametrize(
    "configuration",
    (
        FallbackConfiguration.__new__(FallbackConfiguration),
        "invalid",
    ),
)
def test_invalid_contract_configuration_is_rejected(configuration: object) -> None:
    contract = get_fallback_contract("cached_value")
    if isinstance(configuration, FallbackConfiguration):
        object.__setattr__(configuration, "history_limit", 0)
        object.__setattr__(configuration, "allow_partial_result", False)
        object.__setattr__(configuration, "allow_empty_result", False)
        with pytest.raises(ValueError, match="history limit"):
            configuration.__post_init__()
    else:
        with pytest.raises(TypeError, match="fallback configuration"):
            replace(contract, configuration=configuration)  # type: ignore[arg-type]


def test_incompatible_policy_and_action_are_rejected() -> None:
    contract = get_fallback_contract("cached_value")
    with pytest.raises(ValueError, match="incompatible"):
        replace(contract, action=FallbackAction.EMPTY_RESPONSE)


def test_context_flags_must_be_explicit_booleans() -> None:
    with pytest.raises(TypeError, match="flags"):
        _context(failure_classified=1)


def test_registry_rejects_duplicates_and_audits_missing_contracts() -> None:
    contract = get_fallback_contract("cached_value")
    with pytest.raises(ValueError, match="unique"):
        FallbackRegistry((contract, contract))
    audit = DEGRADATION_CONTRACTS.audit(("cached_value", "missing"))
    assert audit.contracts_checked == len(DEGRADATION_CONTRACTS)
    assert audit.diagnostics.messages == ("missing fallback contract: missing",)


def test_partial_and_empty_results_require_explicit_configuration() -> None:
    partial = replace(
        get_fallback_contract("partial_response"),
        configuration=FallbackConfiguration(),
    )
    empty = replace(
        get_fallback_contract("empty_response"),
        configuration=FallbackConfiguration(),
    )
    with pytest.raises(ValueError, match="partial response"):
        FallbackRuntime(partial).evaluate(_context())
    with pytest.raises(ValueError, match="empty response"):
        FallbackRuntime(empty).evaluate(_context())
