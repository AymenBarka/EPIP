from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import ProjectionAuthority
from epip.a06.compatibility import (
    CompatibilityDiagnostics,
    CompatibilityValidation,
    ProjectionCompatibility,
)
from epip.a06.eligibility import ProjectionEligibility
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError


def parts() -> tuple[
    ProjectionRequest,
    ProjectionAuthority,
    ProjectionScope,
    ProjectionPlan,
    ProjectionEligibility,
]:
    request = ProjectionRequest("r", ("a",), "t", "batch", 1)
    authority = ProjectionAuthority("auth", 1, ("a",), 1, 1, 2)
    scope = ProjectionScope(("a",), ("d",))
    plan = ProjectionPlan("p", ("a",), authority)
    eligibility = ProjectionEligibility(plan, authority, 1, True)
    return request, authority, scope, plan, eligibility


def test_compatibility_is_immutable_deterministic_and_hashable() -> None:
    request, authority, scope, plan, eligibility = parts()
    compatibility = ProjectionCompatibility(plan, authority, True)
    validation = CompatibilityValidation(
        compatibility, eligibility, plan, request, authority, scope
    )
    assert validation.valid is True
    assert validation == CompatibilityValidation(
        compatibility, eligibility, plan, request, authority, scope
    )
    assert hash(validation) == hash(
        CompatibilityValidation(compatibility, eligibility, plan, request, authority, scope)
    )
    assert validation != object()
    with pytest.raises(FrozenInstanceError):
        compatibility.compatible = False


def test_compatibility_rejects_invalid_context() -> None:
    request, authority, scope, plan, eligibility = parts()
    with pytest.raises(DataIntegrityError):
        ProjectionCompatibility(object(), authority, True)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionCompatibility(plan, object(), True)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionCompatibility(plan, authority, 1)
    compatibility = ProjectionCompatibility(plan, authority, True)
    for values in (
        (object(), eligibility, plan, request, authority, scope),
        (compatibility, object(), plan, request, authority, scope),
        (compatibility, eligibility, object(), request, authority, scope),
        (compatibility, eligibility, plan, object(), authority, scope),
        (compatibility, eligibility, plan, request, object(), scope),
        (compatibility, eligibility, plan, request, authority, object()),
    ):
        with pytest.raises(DataIntegrityError):
            CompatibilityValidation(*values)
    assert not CompatibilityValidation(
        compatibility,
        eligibility,
        plan,
        request,
        ProjectionAuthority("x", 1, ("a",), 1, 1, 2),
        scope,
    ).valid


def test_diagnostics_are_canonical() -> None:
    assert CompatibilityDiagnostics(("z", "a")).diagnostics == ("a", "z")
    assert CompatibilityDiagnostics().diagnostics == ()
    with pytest.raises(DataIntegrityError):
        CompatibilityDiagnostics([])


def test_e03_to_e05_contract_integration() -> None:
    request, authority, scope, plan, eligibility = parts()
    compatibility = ProjectionCompatibility(plan, authority, True)
    validation = CompatibilityValidation(
        compatibility, eligibility, plan, request, authority, scope
    )
    assert validation.plan_identity == plan.plan_identity
    assert validation.valid is True
    with pytest.raises(FrozenInstanceError):
        plan.plan_identity = "changed"


def test_e04_to_e05_contract_integration() -> None:
    request, authority, scope, plan, eligibility = parts()
    compatibility = ProjectionCompatibility(plan, authority, True)
    validation = CompatibilityValidation(
        compatibility, eligibility, plan, request, authority, scope
    )
    assert validation.valid is True
    assert eligibility.eligible is True
    with pytest.raises(FrozenInstanceError):
        eligibility.eligible = False


def test_cross_predecessor_compatibility_is_deterministic() -> None:
    request, authority, scope, plan, eligibility = parts()
    first = CompatibilityValidation(
        ProjectionCompatibility(plan, authority, True), eligibility, plan, request, authority, scope
    )
    second = CompatibilityValidation(
        ProjectionCompatibility(plan, authority, True), eligibility, plan, request, authority, scope
    )
    assert first == second
    assert hash(first) == hash(second)
