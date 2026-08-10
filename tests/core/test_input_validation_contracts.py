from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from epip.core.input_validation import (
    INPUT_VALIDATION_CONTRACTS,
    InputValidationAware,
    InputValidationContract,
    InputValidationRegistry,
    InputValidationRule,
    ValidationAudit,
    ValidationBoundary,
    ValidationCapability,
    ValidationCategory,
    ValidationPolicy,
    ValidationResponsibility,
    ValidationSeverity,
    declared_input_validation_contracts,
    get_input_validation_contract,
)


def _rule(**overrides: object) -> InputValidationRule:
    values: dict[str, object] = {
        "name": "example-rule",
        "category": ValidationCategory.TYPE_VALIDATION,
        "severity": ValidationSeverity.HIGH,
        "policy": ValidationPolicy.FRAMEWORK_RESPONSIBLE,
        "responsibility": ValidationResponsibility.FRAMEWORK,
        "capability": ValidationCapability.TYPE_CHECKING,
        "description": "Declarative test rule.",
    }
    values.update(overrides)
    return InputValidationRule(**values)  # type: ignore[arg-type]


def _contract(**overrides: object) -> InputValidationContract:
    values: dict[str, object] = {
        "name": "example",
        "boundary": ValidationBoundary.PUBLIC_API,
        "rules": (_rule(),),
        "capabilities": frozenset({ValidationCapability.TYPE_CHECKING}),
        "responsibility": ValidationResponsibility.FRAMEWORK,
        "restrictions": ("Declaration only.",),
    }
    values.update(overrides)
    return InputValidationContract(**values)  # type: ignore[arg-type]


def test_official_registry_is_complete_read_only_and_deterministic() -> None:
    declared = declared_input_validation_contracts()
    assert tuple(item.name for item in declared) == tuple(sorted(INPUT_VALIDATION_CONTRACTS))
    assert {item.boundary for item in declared} == set(ValidationBoundary)
    with pytest.raises(TypeError):
        INPUT_VALIDATION_CONTRACTS["new"] = declared[0]  # type: ignore[index]


def test_contracts_and_rules_are_immutable() -> None:
    contract = declared_input_validation_contracts()[0]
    with pytest.raises(FrozenInstanceError):
        contract.name = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        contract.rules[0].name = "changed"  # type: ignore[misc]


def test_resolution_supports_names_and_aware_objects() -> None:
    contract = get_input_validation_contract("public-api")

    class Aware:
        input_validation_contract = contract

    assert isinstance(Aware(), InputValidationAware)
    assert get_input_validation_contract(Aware()) is contract
    with pytest.raises(LookupError, match="no input-validation contract"):
        get_input_validation_contract("missing")


def test_classification_policies_severities_and_responsibilities_are_covered() -> None:
    assert set(ValidationCategory) == {
        ValidationCategory.TYPE_VALIDATION,
        ValidationCategory.NULLABILITY,
        ValidationCategory.RANGE_VALIDATION,
        ValidationCategory.ENUM_VALIDATION,
        ValidationCategory.FORMAT_VALIDATION,
        ValidationCategory.STRUCTURE_VALIDATION,
        ValidationCategory.IDENTITY_VALIDATION,
        ValidationCategory.RESOURCE_VALIDATION,
        ValidationCategory.SECURITY_VALIDATION,
        ValidationCategory.CONFIGURATION_VALIDATION,
    }
    assert len(ValidationPolicy) == 7
    assert len(ValidationSeverity) == 5
    assert len(ValidationResponsibility) == 9


def test_all_capabilities_are_declarative_and_available() -> None:
    assert len(ValidationCapability) == 10
    for contract in declared_input_validation_contracts():
        assert {rule.capability for rule in contract.rules} <= contract.capabilities
        assert all(restriction.strip() for restriction in contract.restrictions)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "", "name"),
        ("rules", (), "rule"),
        ("capabilities", frozenset(), "capability"),
        ("restrictions", (), "restriction"),
    ],
)
def test_incomplete_contracts_are_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _contract(**{field: value})


def test_incomplete_and_duplicate_rules_are_rejected() -> None:
    with pytest.raises(ValueError, match="name"):
        _rule(name="")
    with pytest.raises(ValueError, match="description"):
        _rule(description="")
    rule = _rule()
    with pytest.raises(ValueError, match="unique"):
        _contract(rules=(rule, rule))
    with pytest.raises(ValueError, match="declared"):
        _contract(capabilities=frozenset({ValidationCapability.RANGE_CHECKING}))


def test_registry_rejects_duplicate_and_empty_declarations() -> None:
    contract = _contract()
    with pytest.raises(ValueError, match="unique"):
        InputValidationRegistry((contract, contract))
    with pytest.raises(ValueError, match="incomplete"):
        InputValidationRegistry(())


def test_diagnostics_detect_invalid_declarations() -> None:
    invalid = _contract(
        boundary=cast(ValidationBoundary, "unknown"),
        responsibility=cast(ValidationResponsibility, "unknown"),
        rules=(
            _rule(
                category=cast(ValidationCategory, "unknown"),
                severity=cast(ValidationSeverity, "unknown"),
                policy=cast(ValidationPolicy, "unknown"),
                responsibility=cast(ValidationResponsibility, "unknown"),
                capability=cast(ValidationCapability, "unknown"),
            ),
        ),
        capabilities=frozenset({cast(ValidationCapability, "unknown")}),
    )
    assert ValidationAudit.inspect((invalid,)).violations == (
        "invalid validation boundary: example",
        "incoherent validation responsibility: example",
        "invalid validation category: example",
        "invalid validation severity: example",
        "incompatible validation policy: example",
        "incoherent rule responsibility: example",
        "invalid validation capability: example",
    )


@pytest.mark.parametrize(
    ("policy", "responsibility", "message"),
    [
        (
            ValidationPolicy.CALLER_RESPONSIBLE,
            ValidationResponsibility.FRAMEWORK,
            "caller",
        ),
        (
            ValidationPolicy.FRAMEWORK_RESPONSIBLE,
            ValidationResponsibility.CALLER,
            "framework",
        ),
        (
            ValidationPolicy.EXTERNAL_RESPONSIBLE,
            ValidationResponsibility.USER,
            "external",
        ),
    ],
)
def test_diagnostics_detect_contradictory_responsibilities(
    policy: ValidationPolicy,
    responsibility: ValidationResponsibility,
    message: str,
) -> None:
    diagnostics = ValidationAudit.inspect(
        (_contract(rules=(_rule(policy=policy, responsibility=responsibility),)),)
    )
    assert any(message in violation for violation in diagnostics.violations)


def test_diagnostics_detect_missing_boundaries_and_duplicates() -> None:
    contract = _contract()
    diagnostics = ValidationAudit.inspect(
        (contract, contract), expected_boundaries=(ValidationBoundary.KERNEL,)
    )
    assert diagnostics.violations == (
        "duplicate input-validation contract: example",
        "missing validation boundary: kernel",
    )


def test_official_audit_is_clean() -> None:
    diagnostics = ValidationAudit.inspect(
        declared_input_validation_contracts(), expected_boundaries=ValidationBoundary
    )
    assert diagnostics.valid
    assert diagnostics.contracts_checked == len(ValidationBoundary)
