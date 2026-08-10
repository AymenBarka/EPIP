from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from epip.core.secure_failure import (
    SECURE_FAILURE_CONTRACTS,
    SecureFailureAdapter,
    SecureFailureAudit,
    SecureFailureBoundary,
    SecureFailureCategory,
    SecureFailureContext,
    SecureFailureContract,
    SecureFailureDecision,
    SecureFailureIncident,
    SecureFailurePolicy,
    SecureFailureRegistry,
    SecureFailureResult,
    SecureFailureSeverity,
    SecureFailureStatistics,
    declared_secure_failure_contracts,
    get_secure_failure_contract,
)


def _incident(
    category: SecureFailureCategory = SecureFailureCategory.VALIDATION_FAILURE,
    severity: SecureFailureSeverity = SecureFailureSeverity.HIGH,
) -> SecureFailureIncident:
    return SecureFailureIncident(
        "incident-001",
        category,
        severity,
        SecureFailureBoundary.CALL,
        "Validator",
        "rejected untrusted input",
    )


def _contract(
    policy: SecureFailurePolicy = SecureFailurePolicy.CONTAIN,
    *,
    enabled: bool = True,
    boundary: SecureFailureBoundary = SecureFailureBoundary.COMPONENT,
) -> SecureFailureContract:
    return SecureFailureContract(
        "test",
        "TestComponent",
        (SecureFailureCategory.VALIDATION_FAILURE,),
        (SecureFailureSeverity.HIGH,),
        boundary,
        policy,
        enabled,
        ("z", "a", "a"),
    )


def _context() -> SecureFailureContext:
    return SecureFailureContext(
        "Validator",
        "validate",
        SecureFailureBoundary.CALL,
        {"z": "last", "a": "first"},
    )


def test_official_registry_is_complete_inert_and_deterministic() -> None:
    entries = declared_secure_failure_contracts()
    assert tuple(name for name, _ in entries) == tuple(
        sorted(item.value for item in SecureFailureBoundary)
    )
    assert {contract.boundary for _, contract in entries} == set(SecureFailureBoundary)
    assert all(not contract.enabled for _, contract in entries)
    assert get_secure_failure_contract("component").boundary is SecureFailureBoundary.COMPONENT
    with pytest.raises(TypeError):
        SECURE_FAILURE_CONTRACTS.contracts["new"] = _contract()  # type: ignore[index]


def test_contract_context_and_registry_are_immutable() -> None:
    contract = _contract()
    context = _context()
    assert contract.restrictions == ("a", "z")
    assert tuple(context.attributes) == ("a", "z")
    with pytest.raises(FrozenInstanceError):
        contract.enabled = False  # type: ignore[misc]
    with pytest.raises(TypeError):
        context.attributes["new"] = "value"  # type: ignore[index]


def test_registry_resolution_and_invalid_declarations() -> None:
    registry = SecureFailureRegistry({"test": _contract()})
    assert registry.get("test").name == "test"
    with pytest.raises(LookupError):
        registry.get("missing")
    with pytest.raises(ValueError):
        SecureFailureRegistry({"wrong": _contract()})
    with pytest.raises(ValueError):
        replace(_contract(), name="")
    with pytest.raises(ValueError):
        replace(_contract(), categories=())


@pytest.mark.parametrize(
    ("policy", "decision"),
    (
        (SecureFailurePolicy.FAIL_FAST, SecureFailureDecision.BLOCK),
        (SecureFailurePolicy.FAIL_SAFE, SecureFailureDecision.BLOCK),
        (SecureFailurePolicy.CONTAIN, SecureFailureDecision.CONTAIN),
        (SecureFailurePolicy.ISOLATE, SecureFailureDecision.ISOLATE),
        (SecureFailurePolicy.REPORT, SecureFailureDecision.REPORT),
        (SecureFailurePolicy.ESCALATE, SecureFailureDecision.ESCALATE),
        (SecureFailurePolicy.IGNORE, SecureFailureDecision.ALLOW_FAILURE),
        (SecureFailurePolicy.DELEGATE, SecureFailureDecision.DELEGATE),
        (SecureFailurePolicy.CUSTOM, SecureFailureDecision.UNKNOWN),
    ),
)
def test_policy_decisions_are_explicit_and_deterministic(
    policy: SecureFailurePolicy, decision: SecureFailureDecision
) -> None:
    first = SecureFailureAdapter.decide(_contract(policy), _context(), _incident())
    second = SecureFailureAdapter.decide(_contract(policy), _context(), _incident())
    assert first == second
    assert first.decision is decision


def test_disabled_contract_is_inert() -> None:
    result = SecureFailureAdapter.decide(_contract(enabled=False), _context(), _incident())
    assert result.decision is SecureFailureDecision.UNKNOWN


def test_incident_classification_is_complete_and_validated() -> None:
    assert {item.value for item in SecureFailureCategory} == {
        "validation_failure",
        "authorization_failure",
        "authentication_failure",
        "configuration_failure",
        "provider_failure",
        "plugin_failure",
        "adapter_failure",
        "serialization_failure",
        "network_failure",
        "filesystem_failure",
        "resource_failure",
        "unknown_failure",
    }
    with pytest.raises(ValueError):
        replace(_incident(), incident_id="")


def test_audit_reports_missing_contradictory_and_typed_findings() -> None:
    contracts = {
        "custom": replace(_contract(SecureFailurePolicy.CUSTOM), name="custom"),
        "isolate-call": replace(
            _contract(SecureFailurePolicy.ISOLATE, boundary=SecureFailureBoundary.CALL),
            name="isolate-call",
        ),
        "provider": replace(_contract(boundary=SecureFailureBoundary.PROVIDER), name="provider"),
    }
    diagnostics = SecureFailureAudit.inspect(
        SecureFailureRegistry(contracts),
        (_incident(SecureFailureCategory.UNKNOWN_FAILURE, SecureFailureSeverity.UNKNOWN),),
        required_contracts=("absent", "custom"),
    )
    assert diagnostics.missing_contracts == ("absent",)
    assert diagnostics.incompatible_policies == ("isolate-call",)
    assert diagnostics.incoherent_boundaries == ("provider",)
    assert diagnostics.invalid_configurations == ("custom",)
    assert diagnostics.typed_violations == (
        "unknown-category:incident-001",
        "unknown-severity:incident-001",
    )
    assert not diagnostics.valid


def test_audit_accepts_official_registry_and_detects_empty_registry() -> None:
    assert SecureFailureAudit.inspect(SECURE_FAILURE_CONTRACTS).valid
    empty = SecureFailureAudit.inspect(SecureFailureRegistry({}))
    assert empty.incomplete_registry == ("registry is empty",)


def test_audit_detects_invalid_category_and_severity_runtime_values() -> None:
    malformed = replace(
        _contract(),
        categories=cast(tuple[SecureFailureCategory, ...], ("invalid",)),
        severities=cast(tuple[SecureFailureSeverity, ...], ("invalid",)),
    )
    diagnostics = SecureFailureAudit.inspect(SecureFailureRegistry({"test": malformed}))
    assert diagnostics.invalid_categories == ("test:invalid",)
    assert diagnostics.invalid_severities == ("test:invalid",)


def test_statistics_cover_all_decisions() -> None:
    results = tuple(
        SecureFailureResult("test", str(index), decision)
        for index, decision in enumerate(SecureFailureDecision)
    )
    statistics = SecureFailureStatistics.from_results(results)
    assert statistics.total == len(SecureFailureDecision)
    assert (
        statistics.blocked,
        statistics.contained,
        statistics.isolated,
        statistics.reported,
        statistics.escalated,
        statistics.delegated,
        statistics.allowed,
        statistics.unknown,
    ) == (1, 1, 1, 1, 1, 1, 1, 1)
