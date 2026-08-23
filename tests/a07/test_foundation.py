from dataclasses import FrozenInstanceError

import pytest

from epip.a07.foundation import (
    StrategyDirection,
    StrategyEvaluationRequest,
    StrategyEvidenceIdentity,
    StrategyFoundationDiagnostics,
    StrategyIdentity,
)
from epip.core.integrity import DataIntegrityError, MissingFieldError


def _request() -> StrategyEvaluationRequest:
    return StrategyEvaluationRequest(
        StrategyIdentity("strategy", "1"),
        StrategyEvidenceIdentity("evidence", "source"),
        "2026-01-01T00:00:00+00:00",
        "A05-v1.0.0",
        "policy-ref",
    )


def test_direction_is_frozen() -> None:
    assert [item.value for item in StrategyDirection] == ["BUY", "SELL", "NO_TRADE"]


def test_identity_equality_hash_and_immutability() -> None:
    left = StrategyIdentity("s", "1")
    right = StrategyIdentity("s", "1")
    assert left == right
    assert hash(left) == hash(right)
    with pytest.raises(FrozenInstanceError):
        left.strategy_id = "other"
    assert left != StrategyEvidenceIdentity("s", "1")


@pytest.mark.parametrize("value", [None, "", "  ", 1])
def test_identity_rejects_invalid_values(value: object) -> None:
    with pytest.raises(MissingFieldError):
        StrategyIdentity(value, "1")


def test_evidence_identity_reconstructs() -> None:
    value = StrategyEvidenceIdentity("e", "p")
    rebuilt = StrategyEvidenceIdentity(value.evidence_id, value.provenance)
    assert rebuilt == value
    assert hash(rebuilt) == hash(value)


def test_request_validates_opaque_references_and_reconstructs() -> None:
    value = _request()
    rebuilt = StrategyEvaluationRequest(
        value.strategy_identity,
        value.evidence_identity,
        value.evaluation_timestamp,
        value.baseline_reference,
        value.policy_reference,
    )
    assert rebuilt == value
    assert hash(rebuilt) == hash(value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"strategy_identity": object()},
        {"evidence_identity": object()},
        {"evaluation_timestamp": "2026-01-01T00:00:00"},
        {"evaluation_timestamp": "not-a-timestamp"},
    ],
)
def test_request_fails_closed(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "strategy_identity": StrategyIdentity("s", "1"),
        "evidence_identity": StrategyEvidenceIdentity("e", "p"),
        "evaluation_timestamp": "2026-01-01T00:00:00+00:00",
        "baseline_reference": "baseline",
        "policy_reference": "policy",
    }
    values.update(kwargs)
    with pytest.raises(DataIntegrityError):
        StrategyEvaluationRequest(**values)


def test_diagnostics_are_canonical_and_reconstructable() -> None:
    value = StrategyFoundationDiagnostics(("z", "a"))
    rebuilt = StrategyFoundationDiagnostics(value.diagnostics)
    assert value.diagnostics == ("a", "z")
    assert rebuilt == value
    assert hash(rebuilt) == hash(value)


def test_diagnostics_reject_mutable_or_duplicate_values() -> None:
    with pytest.raises(DataIntegrityError):
        StrategyFoundationDiagnostics(["a"])
    with pytest.raises(DataIntegrityError):
        StrategyFoundationDiagnostics(("a", "a"))
