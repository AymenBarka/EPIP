from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import ProjectionAuthority
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import PlanDiagnostics, PlanValidation, ProjectionPlan
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError, MissingFieldError


def _parts() -> tuple[ProjectionRequest, ProjectionAuthority, ProjectionScope]:
    request = ProjectionRequest("req", ("a",), "t", "batch", 1)
    authority = ProjectionAuthority("auth", 1, ("a",), 1, 1, 2)
    scope = ProjectionScope(("a",), ("day",))
    return request, authority, scope


def test_plan_and_validation_are_canonical_and_immutable() -> None:
    request, authority, scope = _parts()
    plan = ProjectionPlan("plan", ("z", "a"), authority)
    assert plan.steps == ("a", "z")
    assert plan != object()
    validation = PlanValidation(plan, request, authority, scope)
    assert validation.valid is True
    assert validation == PlanValidation(plan, request, authority, scope)
    assert hash(validation) == hash(PlanValidation(plan, request, authority, scope))
    with pytest.raises(FrozenInstanceError):
        plan.steps = ()


def test_invalid_plan_inputs_fail_closed() -> None:
    request, authority, _scope = _parts()
    with pytest.raises(DataIntegrityError):
        ProjectionPlan("p", ("a",), object())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionPlan("p", ["a"], authority)
    with pytest.raises(MissingFieldError):
        ProjectionPlan("p", (), authority)
    plan = ProjectionPlan("p", ("a",), authority)
    with pytest.raises(DataIntegrityError):
        PlanValidation(object(), request, authority, _scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        PlanValidation(plan, object(), authority, _scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        PlanValidation(plan, request, object(), _scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        PlanValidation(plan, request, authority, object())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionPlan("p", ("a", "a"), authority)


def test_plan_validation_rejects_inconsistent_context_and_diagnostics_are_canonical() -> None:
    request, authority, scope = _parts()
    plan = ProjectionPlan("p", ("a",), authority)
    other = ProjectionAuthority("other", 1, ("a",), 1, 1, 2)
    assert PlanValidation(plan, request, other, scope).valid is False
    diagnostics = PlanDiagnostics(("z", "a"))
    assert diagnostics.diagnostics == ("a", "z")
    assert diagnostics == PlanDiagnostics(("a", "z"))
    assert PlanDiagnostics().diagnostics == ()


def test_e00_to_e03_contract_integration() -> None:
    request, authority, scope = _parts()
    plan = ProjectionPlan("p", ("a",), authority)
    result = PlanValidation(plan, request, authority, scope)
    assert result.request_identity == request.request_identity
    assert result.valid is True
    assert request.request_identity == "req"


def test_e01_to_e03_contract_integration() -> None:
    request, authority, scope = _parts()
    plan = ProjectionPlan("p", ("a",), authority)
    result = PlanValidation(plan, request, authority, scope)
    assert result.authority_identity == authority.authority_identity
    assert result.valid is True
    with pytest.raises(FrozenInstanceError):
        authority.authority_identity = "changed"


def test_e02_to_e03_contract_integration() -> None:
    request, authority, scope = _parts()
    plan = ProjectionPlan("p", ("a",), authority)
    result = PlanValidation(plan, request, authority, scope)
    assert result.valid is True
    assert scope.target_artifacts == request.target_scope
    with pytest.raises(FrozenInstanceError):
        scope.target_artifacts = ()


def test_cross_predecessor_composition_is_deterministic() -> None:
    request, authority, scope = _parts()
    first = PlanValidation(ProjectionPlan("p", ("a",), authority), request, authority, scope)
    second = PlanValidation(ProjectionPlan("p", ("a",), authority), request, authority, scope)
    assert first == second
    assert hash(first) == hash(second)
    assert first.valid is True
