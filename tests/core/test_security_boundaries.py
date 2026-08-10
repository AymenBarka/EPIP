"""Tests for declarative security boundaries and trust transitions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from epip.core.security_boundaries import (
    SECURITY_BOUNDARY_CONTRACTS,
    BoundaryAudit,
    BoundaryCapability,
    BoundaryClassification,
    BoundaryDirection,
    BoundaryPolicy,
    SecurityBoundaryContract,
    SecurityBoundaryRegistry,
    SecurityZone,
    TrustDomain,
    TrustTransition,
    declared_security_boundaries,
    get_security_boundary_contract,
)


def _transition(**overrides: object) -> TrustTransition:
    values: dict[str, object] = {
        "source": SecurityZone.CORE,
        "destination": SecurityZone.PROVIDER,
        "direction": BoundaryDirection.OUTBOUND,
        "ownership": "core",
        "responsibility": "provider",
        "expected_validation": ("Validate provider input.",),
        "trust_level": TrustDomain.PARTIALLY_TRUSTED,
    }
    values.update(overrides)
    return TrustTransition(**values)  # type: ignore[arg-type]


def _contract(**overrides: object) -> SecurityBoundaryContract:
    values: dict[str, object] = {
        "name": "example-boundary",
        "classification": BoundaryClassification.TRUST,
        "transition": _transition(),
        "capabilities": frozenset({BoundaryCapability.READ}),
        "policies": ((BoundaryCapability.READ, BoundaryPolicy.RESTRICTED),),
        "restrictions": ("Declaration only.",),
    }
    values.update(overrides)
    return SecurityBoundaryContract(**values)  # type: ignore[arg-type]


def test_registry_is_complete_immutable_and_deterministic() -> None:
    declared = declared_security_boundaries()
    assert declared
    assert tuple(item.name for item in declared) == tuple(sorted(SECURITY_BOUNDARY_CONTRACTS))
    with pytest.raises(TypeError):
        SECURITY_BOUNDARY_CONTRACTS["other"] = _contract()  # type: ignore[index]


def test_resolution_supports_names_and_native_declarations() -> None:
    expected = SECURITY_BOUNDARY_CONTRACTS["core-provider"]
    assert get_security_boundary_contract("core-provider") is expected

    class Aware:
        @property
        def security_boundary_contract(self) -> SecurityBoundaryContract:
            return _contract()

    assert get_security_boundary_contract(Aware()).name == "example-boundary"
    with pytest.raises(LookupError, match="no security boundary"):
        get_security_boundary_contract("unknown")


def test_contract_and_transition_are_deeply_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.name = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        contract.transition.ownership = "changed"  # type: ignore[misc]


def test_all_required_zones_and_trust_domains_exist() -> None:
    required = {
        "core",
        "framework",
        "kernel",
        "engine",
        "plugin",
        "provider",
        "adapter",
        "external",
        "system",
        "user",
        "network",
        "filesystem",
    }
    assert required <= {item.value for item in SecurityZone}
    assert {item.value for item in TrustDomain} == {
        "fully_trusted",
        "trusted",
        "partially_trusted",
        "untrusted",
        "external_trust",
        "unknown_trust",
    }


def test_required_trust_transitions_are_declared() -> None:
    pairs = {
        (item.transition.source, item.transition.destination)
        for item in declared_security_boundaries()
    }
    assert {
        (SecurityZone.CORE, SecurityZone.PROVIDER),
        (SecurityZone.CORE, SecurityZone.PLUGIN),
        (SecurityZone.PLUGIN, SecurityZone.EVENTBUS),
        (SecurityZone.PROVIDER, SecurityZone.ENGINE),
        (SecurityZone.ENGINE, SecurityZone.ADAPTER),
        (SecurityZone.ADAPTER, SecurityZone.EXTERNAL),
        (SecurityZone.USER, SecurityZone.FRAMEWORK),
        (SecurityZone.FILESYSTEM, SecurityZone.FRAMEWORK),
        (SecurityZone.NETWORK, SecurityZone.PROVIDER),
    } <= pairs


def test_capabilities_and_policies_are_complete_and_typed() -> None:
    contracts = declared_security_boundaries()
    for contract in contracts:
        assert contract.capabilities
        assert {capability for capability, _ in contract.policies} == set(contract.capabilities)
        assert all(isinstance(item, BoundaryCapability) for item in contract.capabilities)
        assert all(isinstance(policy, BoundaryPolicy) for _, policy in contract.policies)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "", "name"),
        ("capabilities", frozenset(), "capability"),
        ("policies", (), "policy"),
        ("restrictions", (), "restriction"),
    ],
)
def test_incomplete_contracts_are_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _contract(**{field: value})


def test_invalid_and_duplicate_policy_declarations_are_rejected() -> None:
    with pytest.raises(ValueError, match="exactly one policy"):
        _contract(capabilities=frozenset({BoundaryCapability.READ, BoundaryCapability.WRITE}))
    with pytest.raises(ValueError, match="unique"):
        _contract(
            policies=(
                (BoundaryCapability.READ, BoundaryPolicy.ALLOWED),
                (BoundaryCapability.READ, BoundaryPolicy.OBSERVED),
            )
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("destination", SecurityZone.CORE, "zones"),
        ("ownership", "", "ownership"),
        ("responsibility", "", "responsibility"),
        ("expected_validation", (), "validation"),
    ],
)
def test_invalid_transitions_are_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _transition(**{field: value})


def test_diagnostics_detect_missing_and_contradictory_boundaries() -> None:
    first = _contract()
    second = _contract(
        name="other-boundary",
        transition=_transition(ownership="provider"),
    )
    diagnostics = BoundaryAudit.inspect(
        (first, second), expected_boundaries=("example-boundary", "missing-boundary")
    )
    assert diagnostics.valid is False
    assert diagnostics.violations == (
        "contradictory boundary ownership: other-boundary",
        "missing boundary: missing-boundary",
    )


def test_diagnostics_detect_invalid_runtime_declarations() -> None:
    invalid = _contract(
        transition=_transition(
            source=cast(SecurityZone, "unknown"),
            direction=cast(BoundaryDirection, "sideways"),
            trust_level=cast(TrustDomain, "invalid"),
        ),
        capabilities=frozenset({cast(BoundaryCapability, "invalid")}),
        policies=((cast(BoundaryCapability, "invalid"), cast(BoundaryPolicy, "bad")),),
    )
    violations = BoundaryAudit.inspect((invalid,)).violations
    assert violations == (
        "unknown security zone: example-boundary",
        "invalid transition direction: example-boundary",
        "incompatible trust declaration: example-boundary",
        "incoherent boundary capability: example-boundary",
        "invalid boundary policy: example-boundary",
    )


def test_registry_rejects_duplicates_and_incomplete_input() -> None:
    contract = _contract()
    with pytest.raises(ValueError, match="unique"):
        SecurityBoundaryRegistry((contract, contract))
    with pytest.raises(ValueError, match="incomplete"):
        SecurityBoundaryRegistry(())


def test_official_boundary_audit_is_clean() -> None:
    diagnostics = BoundaryAudit.inspect(
        declared_security_boundaries(), expected_boundaries=SECURITY_BOUNDARY_CONTRACTS
    )
    assert diagnostics.valid
    assert diagnostics.boundaries_checked == len(SECURITY_BOUNDARY_CONTRACTS)
