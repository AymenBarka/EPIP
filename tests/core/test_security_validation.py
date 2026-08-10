"""Institutional validation campaign for the H007 security architecture."""

from __future__ import annotations

import gc
import hashlib
import json
import tracemalloc
from dataclasses import replace

import pytest

from epip.core.input_validation import (
    InputValidationRegistry,
    ValidationAudit,
    declared_input_validation_contracts,
    get_input_validation_contract,
)
from epip.core.runtime_security import (
    RUNTIME_SECURITY_POLICIES,
    RuntimeSecurityAdapter,
    RuntimeSecurityAdoption,
    RuntimeSecurityContext,
    RuntimeSecurityPolicy,
    RuntimeSecurityViolation,
    SecurityPolicyBinding,
    SecurityPolicyConfiguration,
    SecurityPolicyScope,
    declared_runtime_security_policies,
)
from epip.core.secure_failure import (
    SecureFailureAdapter,
    SecureFailureBoundary,
    SecureFailureCategory,
    SecureFailureContext,
    SecureFailureIncident,
    SecureFailureSeverity,
    declared_secure_failure_contracts,
)
from epip.core.security import (
    SecurityAudit,
    SecurityRegistry,
    declared_security_contracts,
    get_security_contract,
)
from epip.core.security_audit import (
    SECURITY_AUDIT_REGISTRY,
    SecurityAuditEntry,
    SecurityAuditManager,
    SecurityAuditRegistry,
    SecurityObservation,
    SecurityObservationKind,
)
from epip.core.security_boundaries import (
    BoundaryAudit,
    SecurityBoundaryRegistry,
    declared_security_boundaries,
    get_security_boundary_contract,
)

STRESS_ITERATIONS = 100_000
END_TO_END_CYCLES = 1_000


def _digest(value: object) -> str:
    payload = json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _runtime_inputs() -> (
    tuple[RuntimeSecurityAdoption, RuntimeSecurityContext, tuple[RuntimeSecurityViolation, ...]]
):
    binding = SecurityPolicyBinding(
        "validation-call", "strict", SecurityPolicyScope.CALL, "Validation.run"
    )
    adoption = RuntimeSecurityAdoption(
        binding,
        SecurityPolicyConfiguration(RuntimeSecurityPolicy.STRICT, enabled=True),
    )
    context = RuntimeSecurityContext("Validation", "run", SecurityPolicyScope.CALL)
    return adoption, context, (RuntimeSecurityViolation("invalid", "rejected"),)


def test_contract_boundary_and_validation_campaigns_reach_100k() -> None:
    contracts = declared_security_contracts()
    boundaries = declared_security_boundaries()
    validations = declared_input_validation_contracts()
    assert SecurityAudit.inspect(contracts).valid
    assert BoundaryAudit.inspect(boundaries).valid
    assert ValidationAudit.inspect(validations).valid

    for index in range(STRESS_ITERATIONS):
        assert get_security_contract(contracts[index % len(contracts)].component)
        assert get_security_boundary_contract(boundaries[index % len(boundaries)].name)
        assert get_input_validation_contract(validations[index % len(validations)].name)


def test_runtime_and_secure_failure_campaigns_reach_100k() -> None:
    adoption, context, violations = _runtime_inputs()
    failure_contracts = declared_secure_failure_contracts()
    failure_context = SecureFailureContext("Validation", "run", SecureFailureBoundary.CALL)
    incident = SecureFailureIncident(
        "incident",
        SecureFailureCategory.VALIDATION_FAILURE,
        SecureFailureSeverity.HIGH,
        SecureFailureBoundary.CALL,
        "Validation",
        "rejected",
    )
    expected = RuntimeSecurityAdapter.evaluate(adoption, context, violations)
    for index in range(STRESS_ITERATIONS):
        assert RuntimeSecurityAdapter.evaluate(adoption, context, violations) == expected
        contract = failure_contracts[index % len(failure_contracts)][1]
        assert SecureFailureAdapter.decide(contract, failure_context, incident).contract_name


def test_audit_snapshot_report_and_diagnostics_campaign_is_deterministic() -> None:
    manager = SecurityAuditManager(SECURITY_AUDIT_REGISTRY)
    observations = (
        SecurityObservation(
            1,
            "decision",
            "runtime",
            SecurityObservationKind.DECISION,
            "allow",
            policy="disabled",
            adopted=True,
            runtime_active=True,
        ),
    )
    expected = manager.report(manager.snapshot(1, observations)).to_json()
    digests: set[str] = set()
    for _ in range(END_TO_END_CYCLES):
        snapshot = manager.snapshot(1, observations)
        report = manager.report(snapshot)
        assert manager.audit(snapshot).valid
        assert report.to_json() == expected
        digests.add(_digest(report.to_dict()))
    assert len(digests) == 1


def test_fault_injection_detects_missing_duplicates_and_contradictions() -> None:
    contract = declared_security_contracts()[0]
    with pytest.raises(ValueError):
        SecurityRegistry((contract, contract))
    boundary = declared_security_boundaries()[0]
    with pytest.raises(ValueError):
        SecurityBoundaryRegistry((boundary, boundary))
    validation = declared_input_validation_contracts()[0]
    with pytest.raises(ValueError):
        InputValidationRegistry((validation, validation))
    with pytest.raises(LookupError):
        RUNTIME_SECURITY_POLICIES.get("unknown-policy")

    malformed = SecurityAuditRegistry(
        (SecurityAuditEntry("missing", boundary_contract="unknown-boundary"),)
    )
    malformed_manager = SecurityAuditManager(malformed)
    diagnostics = malformed_manager.audit(malformed_manager.snapshot(0))
    assert not diagnostics.valid
    assert {item.code for item in diagnostics.items} == {"MISSING_BOUNDARY_CONTRACT"}

    declared = declared_input_validation_contracts()[0]
    with pytest.raises(ValueError):
        replace(declared, capabilities=frozenset())


def test_security_models_have_bounded_transient_memory() -> None:
    gc.collect()
    tracemalloc.start()
    baseline, _ = tracemalloc.get_traced_memory()
    contracts = declared_security_contracts()
    for index in range(20_000):
        get_security_contract(contracts[index % len(contracts)].component)
    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert current - baseline < 250_000
    assert peak - baseline < 2_000_000


def test_official_registries_are_complete_and_stably_ordered() -> None:
    groups = (
        tuple(item.component for item in declared_security_contracts()),
        tuple(item.name for item in declared_security_boundaries()),
        tuple(item.name for item in declared_input_validation_contracts()),
        tuple(name for name, _ in declared_runtime_security_policies()),
        tuple(name for name, _ in declared_secure_failure_contracts()),
        tuple(SECURITY_AUDIT_REGISTRY),
    )
    assert all(group for group in groups)
    assert all(group == tuple(sorted(group)) for group in groups)
