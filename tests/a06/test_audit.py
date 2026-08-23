from dataclasses import FrozenInstanceError

import pytest

from epip.a06.audit import AuditDiagnostics, AuditPreparation, ProjectionAudit
from epip.a06.projection import ProjectionResult
from epip.a06.replay import ProjectionReplay
from epip.core.integrity import DataIntegrityError


def _objects() -> tuple[ProjectionResult, ProjectionReplay]:
    from epip.a06.authority import ProjectionAuthority
    from epip.a06.compatibility import ProjectionCompatibility
    from epip.a06.eligibility import ProjectionEligibility
    from epip.a06.foundation import ProjectionRequest
    from epip.a06.planning import ProjectionPlan
    from epip.a06.scope import ProjectionScope

    req = ProjectionRequest("req", ("a",), "t", "batch", 1)
    auth = ProjectionAuthority("auth", 2, ("a",), 1, 1, 3)
    scope = ProjectionScope(("a",), ("day",))
    plan = ProjectionPlan("plan", ("derive",), auth)
    elig = ProjectionEligibility(plan, auth, 2, True)
    comp = ProjectionCompatibility(plan, auth, True)
    lineage = ("e00", "e01", "e02", "e03", "e04", "e05")
    result = ProjectionResult("r", comp, elig, plan, req, auth, scope, lineage)
    return result, ProjectionReplay(result, "historical", lineage)


def test_audit_is_immutable_deterministic_and_complete() -> None:
    result, replay = _objects()
    audit = ProjectionAudit(result, replay)
    same = ProjectionAudit(result, replay)
    assert audit == same and hash(audit) == hash(same)
    assert audit != object()
    assert AuditPreparation(audit).complete
    with pytest.raises(FrozenInstanceError):
        audit.result_identity = "x"


def test_audit_rejects_invalid_context() -> None:
    result, replay = _objects()
    with pytest.raises(DataIntegrityError):
        ProjectionAudit(object(), replay)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionAudit(result, object())  # type: ignore[arg-type]
    forged = object.__new__(ProjectionReplay)
    for name in ProjectionReplay.__slots__:
        object.__setattr__(forged, name, getattr(replay, name))
    object.__setattr__(forged, "result_identity", "other")
    with pytest.raises(DataIntegrityError):
        ProjectionAudit(result, forged)
    with pytest.raises(DataIntegrityError):
        AuditPreparation(object())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        AuditDiagnostics(["x"])
    assert AuditDiagnostics().diagnostics == ()
    assert AuditDiagnostics(
        (
            "z",
            "a",
        )
    ).diagnostics == ("a", "z")


def test_e06_to_e08_contract_integration() -> None:
    result, replay = _objects()
    audit = ProjectionAudit(result, replay)
    assert audit.result_identity == result.result_identity
    assert audit.projection_identity == result.projection_identity
    assert audit.baseline_tag == result.baseline_tag
    assert audit.lineage == result.lineage
    assert audit.mode == replay.mode


def test_e07_to_e08_contract_integration() -> None:
    result, replay = _objects()
    audit = ProjectionAudit(result, replay)
    assert audit.result_identity == replay.result_identity
    assert audit.lineage == replay.lineage
    assert audit.mode == replay.mode
    assert ProjectionAudit(result, replay) == audit


def test_cross_predecessor_audit_provenance_is_deterministic() -> None:
    result, replay = _objects()
    first = ProjectionAudit(result, replay)
    second = ProjectionAudit(result, replay)
    assert first == second
    assert hash(first) == hash(second)
    assert AuditPreparation(first) == AuditPreparation(second)
