from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import ProjectionAuthority
from epip.a06.compatibility import ProjectionCompatibility
from epip.a06.eligibility import ProjectionEligibility
from epip.a06.foundation import ProjectionRequest
from epip.a06.planning import ProjectionPlan
from epip.a06.projection import ProjectionResult
from epip.a06.replay import ProjectionReplay, ReplayDiagnostics, ReplayValidation
from epip.a06.scope import ProjectionScope
from epip.core.integrity import DataIntegrityError


def _result() -> ProjectionResult:
    request = ProjectionRequest("req", ("a",), "t", "batch", 1)
    authority = ProjectionAuthority("auth", 2, ("a",), 1, 1, 3)
    scope = ProjectionScope(("a",), ("day",))
    plan = ProjectionPlan("plan", ("derive",), authority)
    eligibility = ProjectionEligibility(plan, authority, 2, True)
    compatibility = ProjectionCompatibility(plan, authority, True)
    return ProjectionResult(
        "result",
        compatibility,
        eligibility,
        plan,
        request,
        authority,
        scope,
        ("e00", "e01", "e02", "e03", "e04", "e05"),
    )


def test_replay_is_deterministic_and_preserves_lineage() -> None:
    result = _result()
    replay = ProjectionReplay(result, "historical", ("e05", "e03", "e01", "e00", "e04", "e02"))
    same = ProjectionReplay(result, "historical", ("e00", "e01", "e02", "e03", "e04", "e05"))
    assert replay == same
    assert hash(replay) == hash(same)
    assert replay.lineage == result.lineage
    assert ReplayValidation(replay, result).valid is True
    with pytest.raises(FrozenInstanceError):
        replay.mode = "live"


def test_replay_rejects_invalid_inputs_and_mismatched_lineage() -> None:
    result = _result()
    with pytest.raises(DataIntegrityError):
        ProjectionReplay(result, "historical", ())
    with pytest.raises(DataIntegrityError):
        ProjectionReplay(result, "historical", [])
    with pytest.raises(DataIntegrityError):
        ProjectionReplay(result, "historical", ("e00", "e00", "e01", "e02", "e03", "e04", "e05"))
    with pytest.raises(DataIntegrityError):
        ProjectionReplay(object(), "historical", ("e00",))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ProjectionReplay(result, "historical", ("other",))
    with pytest.raises(DataIntegrityError):
        ReplayValidation(object(), result)  # type: ignore[arg-type]
    replay = ProjectionReplay(result, "historical", ("e00", "e01", "e02", "e03", "e04", "e05"))
    with pytest.raises(DataIntegrityError):
        ReplayValidation(replay, object())  # type: ignore[arg-type]
    assert replay != object()


def test_replay_diagnostics_are_canonical() -> None:
    diagnostics = ReplayDiagnostics(("z", "a"))
    assert diagnostics.diagnostics == ("a", "z")
    assert hash(diagnostics)
    assert ReplayDiagnostics().diagnostics == ()
    with pytest.raises(DataIntegrityError):
        ReplayDiagnostics(["invalid"])
