from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import ProjectionAuthority
from epip.a06.eligibility import (
    EligibilityDiagnostics,
    EligibilityValidation,
    ProjectionEligibility,
)
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError


def parts() -> tuple[ProjectionRequest, ProjectionAuthority, ProjectionScope, ProjectionPlan]:
    req = ProjectionRequest("r", ("a",), "t", "batch", 1)
    auth = ProjectionAuthority("auth", 1, ("a",), 1, 1, 2)
    scope = ProjectionScope(("a",), ("d",))
    plan = ProjectionPlan("p", ("a",), auth)
    return req, auth, scope, plan


def test_eligibility_valid_immutable_and_hashable() -> None:
    req, auth, scope, plan = parts()
    e = ProjectionEligibility(plan, auth, 1, True)
    v = EligibilityValidation(e, plan, req, auth, scope)
    assert v.valid
    assert v == EligibilityValidation(e, plan, req, auth, scope)
    assert hash(v) == hash(EligibilityValidation(e, plan, req, auth, scope))
    with pytest.raises(FrozenInstanceError):
        e.eligible = False
    assert e != object()


def test_eligibility_invalid_fail_closed() -> None:
    req, auth, scope, plan = parts()
    with pytest.raises(DataIntegrityError):
        ProjectionEligibility(object(), auth, 1, True)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionEligibility(plan, object(), 1, True)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionEligibility(plan, auth, 0, True)
    with pytest.raises(DataIntegrityError):
        ProjectionEligibility(plan, auth, 1, 1)
    e = ProjectionEligibility(plan, auth, 1, True)
    with pytest.raises(DataIntegrityError):
        EligibilityValidation(object(), plan, req, auth, scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        EligibilityValidation(e, object(), req, auth, scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        EligibilityValidation(e, plan, object(), auth, scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        EligibilityValidation(e, plan, req, object(), scope)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        EligibilityValidation(e, plan, req, auth, object())  # type: ignore[arg-type]
    assert not EligibilityValidation(
        e, plan, req, ProjectionAuthority("x", 1, ("a",), 1, 1, 2), scope
    ).valid


def test_diagnostics_canonical() -> None:
    assert EligibilityDiagnostics(("z", "a")).diagnostics == ("a", "z")
    assert EligibilityDiagnostics().diagnostics == ()
    with pytest.raises(DataIntegrityError):
        EligibilityDiagnostics([])
    with pytest.raises(DataIntegrityError):
        EligibilityDiagnostics(("",))


def test_e03_to_e04_integration() -> None:
    req, auth, scope, plan = parts()
    eligibility = ProjectionEligibility(plan, auth, 1, True)
    validation = EligibilityValidation(eligibility, plan, req, auth, scope)
    assert validation.plan_identity == plan.plan_identity
    assert validation.valid is True


def test_cross_predecessor_integration() -> None:
    req, auth, scope, plan = parts()
    first = EligibilityValidation(
        ProjectionEligibility(plan, auth, 1, True), plan, req, auth, scope
    )
    second = EligibilityValidation(
        ProjectionEligibility(plan, auth, 1, True), plan, req, auth, scope
    )
    assert first == second
    assert hash(first) == hash(second)
