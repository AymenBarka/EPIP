"""Acceptance tests for the declarative EPIP exception taxonomy."""

from dataclasses import FrozenInstanceError

import pytest

from epip.core.exceptions import (
    EXCEPTION_REGISTRY,
    AdapterError,
    BoundaryViolationError,
    CancellationError,
    ConcurrencyError,
    ConfigurationError,
    EPIPError,
    EventBusError,
    ExceptionBoundary,
    ExceptionContract,
    ExceptionRegistry,
    ExceptionVisibility,
    ExecutionError,
    ExternalSystemError,
    FatalError,
    FrameworkError,
    InfrastructureError,
    InterruptedError,
    KernelError,
    MemoryError,
    NonRetryableError,
    PluginError,
    PortfolioError,
    ProviderError,
    RecoverableError,
    ReliabilityError,
    ReplayError,
    RetryableError,
    RiskError,
    RuntimeError,
    SerializationError,
    TimeoutError,
    ValidationError,
    audit_exception_hierarchy,
    declared_exception_boundaries,
    declared_exception_contracts,
)
from epip.core.reliability import (
    FailureCategory,
    FailureResponsibility,
    RecoveryExpectation,
)

CANONICAL_EXCEPTIONS = (
    EPIPError,
    FrameworkError,
    InfrastructureError,
    ConfigurationError,
    ValidationError,
    RuntimeError,
    ConcurrencyError,
    MemoryError,
    ReliabilityError,
    ExternalSystemError,
    ProviderError,
    AdapterError,
    PluginError,
    ReplayError,
    KernelError,
    EventBusError,
    ExecutionError,
    PortfolioError,
    RiskError,
    SerializationError,
    TimeoutError,
    CancellationError,
    InterruptedError,
    RetryableError,
    NonRetryableError,
    FatalError,
    RecoverableError,
    BoundaryViolationError,
)

REQUIRED_BOUNDARIES = {
    "Internal Boundary",
    "Public API Boundary",
    "Plugin Boundary",
    "Provider Boundary",
    "Adapter Boundary",
    "External Boundary",
    "Serialization Boundary",
    "Thread Boundary",
    "Replay Boundary",
    "Kernel Boundary",
    "EventBus Boundary",
}


def test_hierarchy_is_single_parent_acyclic_and_registered() -> None:
    for exception_type in CANONICAL_EXCEPTIONS:
        assert issubclass(exception_type, EPIPError)
        assert len(exception_type.__bases__) == 1
        assert EXCEPTION_REGISTRY.resolve(exception_type).exception_type is exception_type
    hierarchy = {
        exception_type.__name__: (
            None if exception_type is EPIPError else exception_type.__bases__[0].__name__
        )
        for exception_type in CANONICAL_EXCEPTIONS
    }
    assert audit_exception_hierarchy(hierarchy) == ()


def test_contracts_are_immutable_complete_and_deterministic() -> None:
    contracts = declared_exception_contracts()
    assert contracts == tuple(sorted(contracts, key=lambda item: item.qualified_name))
    assert len(contracts) == len(CANONICAL_EXCEPTIONS)
    assert all(contract.description.strip() for contract in contracts)
    assert all(isinstance(contract.category, FailureCategory) for contract in contracts)
    assert all(isinstance(contract.responsibility, FailureResponsibility) for contract in contracts)
    with pytest.raises(FrozenInstanceError):
        contracts[0].public = False  # type: ignore[misc]


def test_boundaries_are_complete_immutable_and_resolvable() -> None:
    boundaries = declared_exception_boundaries()
    assert {boundary.name for boundary in boundaries} == REQUIRED_BOUNDARIES
    assert boundaries == tuple(sorted(boundaries, key=lambda item: item.name))
    assert all(boundary.capture for boundary in boundaries)
    assert all(boundary.description.strip() for boundary in boundaries)
    assert all(
        isinstance(boundary.logging_responsibility, FailureResponsibility)
        for boundary in boundaries
    )
    with pytest.raises(FrozenInstanceError):
        boundaries[0].propagation = False  # type: ignore[misc]
    assert EXCEPTION_REGISTRY.resolve_boundary("Kernel Boundary").name == "Kernel Boundary"


def test_registry_reports_unknown_and_missing_declarations() -> None:
    class UnknownError(EPIPError):
        pass

    with pytest.raises(LookupError, match="unregistered"):
        EXCEPTION_REGISTRY.resolve(UnknownError)
    with pytest.raises(LookupError, match="unknown exception boundary"):
        EXCEPTION_REGISTRY.resolve_boundary("Unknown Boundary")
    assert EXCEPTION_REGISTRY.audit((UnknownError,), ("Unknown Boundary",)) == (
        f"unregistered exception: {UnknownError.__module__}.{UnknownError.__qualname__}",
        "missing exception boundary: Unknown Boundary",
    )


def test_invalid_contracts_and_duplicate_registry_entries_are_rejected() -> None:
    with pytest.raises(TypeError, match="exception_type"):
        ExceptionContract(
            ValueError,  # type: ignore[arg-type]
            FailureCategory.DATA_ERROR,
            FailureResponsibility.CALLER,
            True,
            False,
            False,
            "invalid root",
        )
    with pytest.raises(ValueError, match="fatal"):
        ExceptionContract(
            FatalError,
            FailureCategory.PERMANENT_ERROR,
            FailureResponsibility.FRAMEWORK,
            True,
            True,
            True,
            "contradiction",
        )
    contract = EXCEPTION_REGISTRY.resolve(EPIPError)
    with pytest.raises(ValueError, match="unique"):
        ExceptionRegistry((contract, contract))


def test_invalid_and_incomplete_boundaries_are_rejected() -> None:
    with pytest.raises(ValueError, match="capture"):
        ExceptionBoundary(
            "Incomplete",
            (),
            None,
            True,
            False,
            FailureResponsibility.FRAMEWORK,
            ExceptionVisibility.INTERNAL,
            RecoveryExpectation.NONE,
            "missing capture",
        )
    with pytest.raises(ValueError, match="translation"):
        ExceptionBoundary(
            "Invalid wrapping",
            (FrameworkError,),
            None,
            True,
            True,
            FailureResponsibility.FRAMEWORK,
            ExceptionVisibility.INTERNAL,
            RecoveryExpectation.NONE,
            "wrapping without translation",
        )
    with pytest.raises(ValueError, match="public"):
        ExceptionBoundary(
            "Contradictory",
            (FrameworkError,),
            None,
            False,
            False,
            FailureResponsibility.FRAMEWORK,
            ExceptionVisibility.PUBLIC,
            RecoveryExpectation.NONE,
            "hidden but public",
        )


def test_hierarchy_audit_detects_cycles_and_unknown_parents() -> None:
    assert audit_exception_hierarchy({"A": "B", "B": "A"}) == (
        "exception hierarchy cycle: A",
        "exception hierarchy cycle: B",
    )
    assert audit_exception_hierarchy({"A": "Missing"}) == (
        "unknown exception parent: A -> Missing",
    )
