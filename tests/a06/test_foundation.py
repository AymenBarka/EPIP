from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from epip.a06.foundation import (
    ProjectionFoundationDiagnostics,
    ProjectionIdentity,
    ProjectionRequest,
)
from epip.core.integrity import DataIntegrityError


def test_identity_is_immutable_hashable_and_deterministic() -> None:
    value = ProjectionIdentity("p", "A05-v1.0.0", "architecture")
    assert value == ProjectionIdentity("p", "A05-v1.0.0", "architecture")
    assert hash(value) == hash(ProjectionIdentity("p", "A05-v1.0.0", "architecture"))
    with pytest.raises(FrozenInstanceError):
        value.identity = "other"
    assert value != object()


def test_request_canonicalizes_scope() -> None:
    request = ProjectionRequest("r", ("z", "a"), "UTC", "historical", 1)
    assert request.target_scope == ("a", "z")
    assert request.policy_version == 1


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ProjectionIdentity("", "tag", "authority"),
        lambda: ProjectionRequest("r", (), "basis", "mode", 1),
        lambda: ProjectionRequest("r", ("x",), "basis", "mode", 0),
        lambda: ProjectionRequest("r", ["x"], "basis", "mode", 1),
        lambda: ProjectionRequest("r", ("x", "x"), "basis", "mode", 1),
    ],
)
def test_invalid_foundation_inputs_fail_closed(factory: Callable[[], object]) -> None:
    with pytest.raises(DataIntegrityError):
        factory()


def test_diagnostics_are_sorted_and_immutable() -> None:
    diagnostics = ProjectionFoundationDiagnostics(("z", "a"))
    assert diagnostics.diagnostics == ("a", "z")
    assert diagnostics == ProjectionFoundationDiagnostics(("a", "z"))
    assert hash(diagnostics) == hash(ProjectionFoundationDiagnostics(("z", "a")))
    assert ProjectionFoundationDiagnostics().diagnostics == ()


def test_empty_diagnostic_entries_fail_closed() -> None:
    with pytest.raises(DataIntegrityError):
        ProjectionFoundationDiagnostics(("",))
