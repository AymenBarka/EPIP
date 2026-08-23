from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import ProjectionAuthority
from epip.a06.foundation import ProjectionRequest
from epip.a06.scope import ProjectionScope, ScopeDiagnostics, ScopeValidation
from epip.core.integrity import DataIntegrityError


def request(scope: tuple[str, ...] = ("desk",)) -> ProjectionRequest:
    return ProjectionRequest("request", scope, "UTC", "historical", 2)


def authority(scope: tuple[str, ...] = ("desk",)) -> ProjectionAuthority:
    return ProjectionAuthority("authority", 1, scope, 2, 1, 10)


def test_scope_uses_real_e00_e01_contracts() -> None:
    scope = ProjectionScope(("desk",), ("historical", "validity"))
    result = ScopeValidation(scope, request(), authority())
    assert result.valid is True
    assert hash(result) == hash(ScopeValidation(scope, request(), authority()))
    assert result != object()


def test_scope_is_canonical_and_immutable() -> None:
    scope = ProjectionScope(("z", "a"), ("validity", "historical"))
    assert scope.target_artifacts == ("a", "z")
    with pytest.raises(FrozenInstanceError):
        scope.target_artifacts = ("other",)


def test_scope_rejects_mismatch_and_unauthorized_artifact() -> None:
    request_scope = request()
    assert (
        ScopeValidation(
            ProjectionScope(("other",), ("validity",)), request_scope, authority()
        ).valid
        is False
    )
    assert (
        ScopeValidation(
            ProjectionScope(("desk", "other"), ("validity",)), request_scope, authority()
        ).valid
        is False
    )


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ProjectionScope((), ("validity",)),
        lambda: ProjectionScope(("desk",), ()),
        lambda: ProjectionScope(["desk"], ("validity",)),
        lambda: ProjectionScope(("desk", "desk"), ("validity",)),
    ],
)
def test_malformed_scope_fails_closed(factory: Callable[[], object]) -> None:
    with pytest.raises(DataIntegrityError):
        factory()


def test_invalid_predecessors_fail_closed() -> None:
    scope = ProjectionScope(("desk",), ("validity",))
    with pytest.raises(DataIntegrityError):
        ScopeValidation(object(), request(), authority())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ScopeValidation(scope, object(), authority())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ScopeValidation(scope, request(), object())  # type: ignore[arg-type]


def test_diagnostics_are_deterministic() -> None:
    value = ScopeDiagnostics(("z", "a"))
    assert value.diagnostics == ("a", "z")
    assert value == ScopeDiagnostics(("a", "z"))
    assert hash(value) == hash(ScopeDiagnostics(("z", "a")))
