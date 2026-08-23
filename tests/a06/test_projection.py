from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import ProjectionAuthority
from epip.a06.compatibility import ProjectionCompatibility
from epip.a06.eligibility import ProjectionEligibility
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.projection import (
    ProjectionDiagnostics,
    ProjectionResult,
    ProjectionResultValidation,
)
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError


def _objects() -> tuple[
    ProjectionRequest,
    ProjectionAuthority,
    ProjectionScope,
    ProjectionPlan,
    ProjectionEligibility,
    ProjectionCompatibility,
]:
    request = ProjectionRequest("req", ("a",), "t", "batch", 1)
    authority = ProjectionAuthority("auth", 2, ("a",), 1, 1, 3)
    scope = ProjectionScope(("a",), ("day",))
    plan = ProjectionPlan("plan", ("derive",), authority)
    eligibility = ProjectionEligibility(plan, authority, 2, True)
    compatibility = ProjectionCompatibility(plan, authority, True)
    return request, authority, scope, plan, eligibility, compatibility


def test_projection_result_and_validation_are_deterministic_and_hashable() -> None:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    result = ProjectionResult(
        "result", compatibility, eligibility, plan, request, authority, scope, ("e05", "e00")
    )
    same = ProjectionResult(
        "result", compatibility, eligibility, plan, request, authority, scope, ("e00", "e05")
    )
    assert result == same
    assert hash(result) == hash(same)
    assert result.lineage == ("e00", "e05")
    validation = ProjectionResultValidation(
        result, compatibility, eligibility, plan, request, authority, scope
    )
    assert validation.valid is True
    with pytest.raises(FrozenInstanceError):
        result.result_identity = "other"


def test_projection_rejects_invalid_contracts() -> None:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    with pytest.raises(DataIntegrityError):
        ProjectionResult("", compatibility, eligibility, plan, request, authority, scope, ("e00",))
    with pytest.raises(DataIntegrityError):
        ProjectionResult("r", compatibility, eligibility, plan, request, authority, scope, [])
    with pytest.raises(DataIntegrityError):
        ProjectionResult(
            "r", compatibility, eligibility, plan, request, authority, scope, ("e00", "e00")
        )
    with pytest.raises(DataIntegrityError):
        ProjectionResult("r", object(), eligibility, plan, request, authority, scope, ("e00",))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionResult("r", compatibility, eligibility, plan, request, authority, scope, ())


@pytest.mark.parametrize("field", ["plan_identity", "authority_identity"])
def test_projection_rejects_inconsistent_predecessor_identity(field: str) -> None:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    altered = object.__new__(ProjectionCompatibility)
    for name in ProjectionCompatibility.__slots__:
        object.__setattr__(altered, name, getattr(compatibility, name))
    object.__setattr__(altered, field, "other")
    with pytest.raises(DataIntegrityError):
        ProjectionResult("r", altered, eligibility, plan, request, authority, scope, ("e00",))


@pytest.mark.parametrize("field", ["plan_identity", "authority_identity"])
def test_projection_rejects_inconsistent_eligibility_identity(field: str) -> None:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    altered = object.__new__(ProjectionEligibility)
    for name in ProjectionEligibility.__slots__:
        object.__setattr__(altered, name, getattr(eligibility, name))
    object.__setattr__(altered, field, "other")
    with pytest.raises(DataIntegrityError):
        ProjectionResult("r", compatibility, altered, plan, request, authority, scope, ("e00",))


def test_projection_rejects_scope_mismatch_and_validation_type() -> None:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    bad_scope = ProjectionScope(("b",), ("day",))
    with pytest.raises(DataIntegrityError):
        ProjectionResult(
            "r", compatibility, eligibility, plan, request, authority, bad_scope, ("e00",)
        )
    result = ProjectionResult(
        "r", compatibility, eligibility, plan, request, authority, scope, ("e00",)
    )
    with pytest.raises(DataIntegrityError):
        ProjectionResultValidation(object(), compatibility, eligibility, plan, request, authority, scope)  # type: ignore[arg-type]
    object.__setattr__(result, "eligible", False)
    assert (
        ProjectionResultValidation(
            result, compatibility, eligibility, plan, request, authority, scope
        ).valid
        is False
    )


def test_diagnostics_are_canonical_and_immutable() -> None:
    assert ProjectionDiagnostics().diagnostics == ()
    diagnostics = ProjectionDiagnostics(("z", "a"))
    assert diagnostics.diagnostics == ("a", "z")
    assert hash(diagnostics)
    with pytest.raises(DataIntegrityError):
        ProjectionDiagnostics(["x"])


def test_result_equality_rejects_other_type() -> None:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    result = ProjectionResult(
        "r", compatibility, eligibility, plan, request, authority, scope, ("e00",)
    )
    assert result != object()


def _result() -> tuple[
    ProjectionResult,
    ProjectionRequest,
    ProjectionAuthority,
    ProjectionScope,
    ProjectionPlan,
    ProjectionEligibility,
    ProjectionCompatibility,
]:
    request, authority, scope, plan, eligibility, compatibility = _objects()
    return (
        ProjectionResult(
            "r", compatibility, eligibility, plan, request, authority, scope, ("e00", "e05")
        ),
        request,
        authority,
        scope,
        plan,
        eligibility,
        compatibility,
    )


def test_e00_to_e06_contract_integration() -> None:
    result, request, *_ = _result()
    assert result.request_identity == request.request_identity
    assert result.lineage == ("e00", "e05")
    assert request.target_scope == ("a",)


def test_e01_to_e06_contract_integration() -> None:
    result, _, authority, *_ = _result()
    assert result.authority_identity == authority.authority_identity
    with pytest.raises(FrozenInstanceError):
        authority.authority_identity = "other"


def test_e02_to_e06_contract_integration() -> None:
    result, _, _, scope, *_ = _result()
    assert scope.target_artifacts == ("a",)
    assert result.request_identity == "req"


def test_e03_to_e06_contract_integration() -> None:
    result, _, _, _, plan, *_ = _result()
    assert result.plan_identity == plan.plan_identity
    assert plan.steps == ("derive",)


def test_e04_to_e06_contract_integration() -> None:
    result, _, _, _, _, eligibility, _ = _result()
    assert result.eligible is eligibility.eligible
    assert eligibility.knowledge_boundary == 2


def test_e05_to_e06_contract_integration() -> None:
    result, _, _, _, _, _, compatibility = _result()
    assert result.compatible is compatibility.compatible
    assert compatibility.plan_identity == result.plan_identity
