from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from epip.a06.authority import (
    AuthorityDiagnostics,
    AuthorityValidation,
    ProjectionAuthority,
)
from epip.a06.foundation import ProjectionRequest
from epip.core.integrity import DataIntegrityError
from epip.governance import GovernanceEpoch
from epip.temporal.model import TemporalAuthorityReference


def request(scope: tuple[str, ...] = ("desk",), policy: int = 2) -> ProjectionRequest:
    return ProjectionRequest("request", scope, "UTC", "historical", policy)


def authority(scope: tuple[str, ...] = ("desk",), policy: int = 2) -> ProjectionAuthority:
    return ProjectionAuthority("authority", 1, scope, policy, 1, 10)


def test_e00_to_e01_and_a05_authority_boundaries_are_preserved() -> None:
    reference = TemporalAuthorityReference("authority", "temporal", "1.0", GovernanceEpoch(1))
    projected = ProjectionAuthority.from_a05_authority(reference, ("desk",), 2, 1, 10)
    result = AuthorityValidation(projected, request())
    assert result.valid is True
    assert projected.authority_identity == reference.authority_identity
    assert reference.governance_epoch.sequence == 1
    with pytest.raises(DataIntegrityError):
        ProjectionAuthority.from_a05_authority(object(), ("desk",), 2, 1, 10)  # type: ignore[arg-type]


def test_valid_authority_is_deterministic_and_hashable() -> None:
    value = AuthorityValidation(authority(), request())
    assert value.valid is True
    assert value == AuthorityValidation(authority(), request())
    assert hash(value) == hash(AuthorityValidation(authority(), request()))
    assert value != object()


def test_scope_and_policy_fail_closed() -> None:
    assert AuthorityValidation(authority(("other",)), request()).valid is False
    assert AuthorityValidation(authority(policy=3), request()).valid is False


def test_authority_is_immutable() -> None:
    value = authority()
    with pytest.raises(FrozenInstanceError):
        value.authority_identity = "other"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ProjectionAuthority("", 1, ("desk",), 1, 1, 2),
        lambda: ProjectionAuthority("a", 0, ("desk",), 1, 1, 2),
        lambda: ProjectionAuthority("a", 1, (), 1, 1, 2),
        lambda: ProjectionAuthority("a", 1, ("desk", "desk"), 1, 1, 2),
        lambda: ProjectionAuthority("a", 1, ["desk"], 1, 1, 2),
        lambda: ProjectionAuthority("a", 1, ("desk",), 1, 3, 2),
    ],
)
def test_malformed_authority_fails_closed(factory: Callable[[], object]) -> None:
    with pytest.raises(DataIntegrityError):
        factory()


def test_predecessor_contract_types_are_required() -> None:
    with pytest.raises(DataIntegrityError):
        AuthorityValidation(authority(), object())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        AuthorityValidation(object(), request())  # type: ignore[arg-type]


def test_diagnostics_are_canonical_and_immutable() -> None:
    value = AuthorityDiagnostics(("scope", "identity"))
    assert value.diagnostics == ("identity", "scope")
    assert value == AuthorityDiagnostics(("identity", "scope"))
    assert hash(value) == hash(AuthorityDiagnostics(("scope", "identity")))
    assert AuthorityDiagnostics().diagnostics == ()
