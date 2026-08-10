"""Tests for the declarative institutional security contract model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epip.core.security import (
    SECURITY_CONTRACTS,
    SecurityAudit,
    SecurityBoundary,
    SecurityCapability,
    SecurityClassification,
    SecurityContract,
    SecurityDiagnostics,
    SecurityLevel,
    SecurityRegistry,
    SecurityResponsibility,
    TrustLevel,
    declared_security_contracts,
    get_security_contract,
)


def _contract(**overrides: object) -> SecurityContract:
    values: dict[str, object] = {
        "component": "epip.example.Component",
        "classification": SecurityClassification.INTERNAL,
        "level": SecurityLevel.GUARDED,
        "trust": TrustLevel.CONDITIONAL,
        "boundaries": frozenset({SecurityBoundary.CORE}),
        "responsibilities": frozenset({SecurityResponsibility.FRAMEWORK}),
        "capabilities": frozenset({SecurityCapability.READ}),
        "restrictions": ("Caller validates external input.",),
    }
    values.update(overrides)
    return SecurityContract(**values)  # type: ignore[arg-type]


def test_registry_is_immutable_complete_and_deterministic() -> None:
    contracts = declared_security_contracts()
    assert contracts
    assert tuple(item.component for item in contracts) == tuple(sorted(SECURITY_CONTRACTS))
    assert len(contracts) == len(SECURITY_CONTRACTS)
    with pytest.raises(TypeError):
        SECURITY_CONTRACTS["epip.example.Component"] = _contract()  # type: ignore[index]


def test_resolution_supports_names_types_and_native_declarations() -> None:
    from epip.core.kernel import Kernel

    expected = SECURITY_CONTRACTS["epip.core.kernel.Kernel"]
    assert get_security_contract("epip.core.kernel.Kernel") is expected
    assert get_security_contract(Kernel) is expected

    class Aware:
        @property
        def security_contract(self) -> SecurityContract:
            return _contract()

    assert get_security_contract(Aware()).component == "epip.example.Component"
    with pytest.raises(LookupError, match="no security contract"):
        get_security_contract("epip.unknown.Component")


def test_contracts_and_diagnostics_are_immutable() -> None:
    contract = _contract()
    diagnostics = SecurityDiagnostics(1, ())
    assert diagnostics.valid
    with pytest.raises(FrozenInstanceError):
        contract.component = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        diagnostics.components_checked = 2  # type: ignore[misc]


@pytest.mark.parametrize("classification", list(SecurityClassification))
def test_every_security_classification_is_valid(
    classification: SecurityClassification,
) -> None:
    trust = TrustLevel.CONDITIONAL
    assert _contract(classification=classification, trust=trust).classification is classification


def test_responsibilities_boundaries_and_capabilities_are_typed() -> None:
    contract = _contract(
        boundaries=frozenset(SecurityBoundary),
        responsibilities=frozenset(SecurityResponsibility),
        capabilities=frozenset(SecurityCapability),
    )
    assert contract.boundaries == frozenset(SecurityBoundary)
    assert contract.responsibilities == frozenset(SecurityResponsibility)
    assert contract.capabilities == frozenset(SecurityCapability)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("component", "", "component"),
        ("boundaries", frozenset(), "boundary"),
        ("responsibilities", frozenset(), "responsibility"),
        ("capabilities", frozenset(), "capability"),
        ("restrictions", (), "restriction"),
        ("restrictions", ("",), "restriction"),
    ],
)
def test_incomplete_contracts_are_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _contract(**{field: value})


@pytest.mark.parametrize(
    ("classification", "trust"),
    [
        (SecurityClassification.TRUSTED, TrustLevel.UNTRUSTED),
        (SecurityClassification.UNTRUSTED, TrustLevel.TRUSTED),
    ],
)
def test_contradictory_contracts_are_rejected(
    classification: SecurityClassification, trust: TrustLevel
) -> None:
    with pytest.raises(ValueError, match="contradicts"):
        _contract(classification=classification, trust=trust)


def test_registry_rejects_duplicate_components() -> None:
    contract = _contract()
    with pytest.raises(ValueError, match="unique"):
        SecurityRegistry((contract, contract))


def test_audit_reports_boundary_capability_contradictions() -> None:
    network = _contract(capabilities=frozenset({SecurityCapability.NETWORK_ACCESS}))
    filesystem = _contract(
        component="epip.example.Files",
        capabilities=frozenset({SecurityCapability.FILESYSTEM_ACCESS}),
    )
    diagnostics = SecurityAudit.inspect((network, filesystem))
    assert diagnostics.components_checked == 2
    assert diagnostics.valid is False
    assert diagnostics.violations == (
        "network capability without boundary: epip.example.Component",
        "filesystem capability without boundary: epip.example.Files",
    )


def test_declared_contracts_have_clean_diagnostics() -> None:
    diagnostics = SecurityAudit.inspect(declared_security_contracts())
    assert diagnostics.valid
    assert diagnostics.components_checked == len(SECURITY_CONTRACTS)
