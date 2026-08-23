from dataclasses import FrozenInstanceError

import pytest

from epip.a06.audit import AuditPreparation, ProjectionAudit
from epip.a06.closure import (
    IntegratedProjectionClosure,
    ProjectionClosureDiagnostics,
    ProjectionClosureVerifier,
)
from epip.core.integrity import DataIntegrityError
from tests.a06.test_audit import _objects


def _closure() -> IntegratedProjectionClosure:
    result, replay = _objects()
    audit = ProjectionAudit(result, replay)
    return IntegratedProjectionClosure(audit, AuditPreparation(audit))


def test_integrated_closure_is_immutable_deterministic_and_verified() -> None:
    closure = _closure()
    assert closure == _closure()
    assert closure != object()
    assert hash(closure) == hash(_closure())
    assert ProjectionClosureVerifier(closure).valid
    with pytest.raises(FrozenInstanceError):
        closure.closed = False


def test_integrated_closure_rejects_missing_or_inconsistent_predecessors() -> None:
    result, replay = _objects()
    audit = ProjectionAudit(result, replay)
    with pytest.raises(DataIntegrityError):
        IntegratedProjectionClosure(object(), AuditPreparation(audit))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        IntegratedProjectionClosure(audit, object())  # type: ignore[arg-type]
    bad = object.__new__(AuditPreparation)
    for name in AuditPreparation.__slots__:
        object.__setattr__(bad, name, getattr(AuditPreparation(audit), name))
    object.__setattr__(bad, "audit_identity", "other")
    with pytest.raises(DataIntegrityError):
        IntegratedProjectionClosure(audit, bad)


def test_closure_diagnostics_are_canonical_and_immutable() -> None:
    diagnostics = ProjectionClosureDiagnostics(("z", "a"))
    assert diagnostics.diagnostics == ("a", "z")
    assert diagnostics == ProjectionClosureDiagnostics(("a", "z"))
    with pytest.raises(FrozenInstanceError):
        diagnostics.diagnostics = ()


def test_closure_rejects_invalid_verifier_and_diagnostics() -> None:
    with pytest.raises(DataIntegrityError):
        ProjectionClosureVerifier(object())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionClosureDiagnostics(["x"])
    with pytest.raises(DataIntegrityError):
        ProjectionClosureDiagnostics((object(),))
    assert ProjectionClosureDiagnostics().diagnostics == ()
