from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.temporal.certification import (
    CertificationDiagnostics,
    CertificationPreparation,
    CertificationPreparer,
)


def test_certification_is_deterministic_and_immutable() -> None:
    facts = (("z", "2"), ("a", "1"))
    one = CertificationPreparer.prepare("p", "profile", facts)
    two = CertificationPreparer.prepare("p", "profile", tuple(reversed(facts)))
    assert one == two
    assert hash(one) == hash(two)
    assert one.preparations[0].facts == (("a", "1"), ("z", "2"))
    with pytest.raises(FrozenInstanceError):
        one.preparations = ()


def test_certification_fails_closed_for_invalid_inputs() -> None:
    with pytest.raises(DataIntegrityError):
        CertificationPreparer.prepare("p", "profile", [])  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        CertificationPreparer.prepare("p", "profile", ())
    with pytest.raises(DataIntegrityError):
        CertificationPreparer.prepare("p", "profile", (("a", "1"), ("a", "1")))
    with pytest.raises(DataIntegrityError):
        CertificationPreparer.prepare("p", "profile", (("a", "1"),), complete=1)  # type: ignore[arg-type]


def test_incomplete_preparation_is_diagnostic() -> None:
    result = CertificationPreparer.prepare("p", "profile", (("a", "1"),), complete=False)
    assert result.reasons
    assert result.preparations[0].complete is False


def test_certification_rejects_malformed_and_invalid_facts() -> None:
    with pytest.raises(DataIntegrityError):
        CertificationPreparer.prepare("p", "profile", (("a",),))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        CertificationPreparer.prepare("p", "profile", (("a", ""),))
    with pytest.raises(DataIntegrityError):
        CertificationPreparer.prepare("p", "profile", (("a", "1"),), complete=cast(Any, "yes"))


def test_certification_diagnostics_reject_invalid_and_duplicate_entries() -> None:
    preparation = CertificationPreparation("p", "profile", (("a", "1"),), True)
    with pytest.raises(DataIntegrityError):
        CertificationDiagnostics(cast(Any, []))
    with pytest.raises(DataIntegrityError):
        CertificationDiagnostics((preparation,), cast(Any, []))
    with pytest.raises(DataIntegrityError):
        CertificationDiagnostics((preparation, preparation))


def test_certification_models_have_type_sensitive_equality() -> None:
    preparation = CertificationPreparation("p", "profile", (("a", "1"),), True)
    assert preparation != object()
    diagnostics = CertificationDiagnostics((preparation,))
    assert diagnostics != preparation
