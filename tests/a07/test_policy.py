"""A07-E01 behavioral tests for immutable strategy-policy contracts."""

import inspect
import os
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import Any, cast

import pytest

from epip.a07.foundation import (
    StrategyDirection,
    StrategyEvaluationRequest,
    StrategyEvidenceIdentity,
    StrategyIdentity,
)
from epip.a07.policy import (
    PolicyDiagnostics,
    PolicyValidation,
    StrategyPolicy,
    StrategyPolicyIdentity,
)
from epip.core.integrity import DataIntegrityError

FINGERPRINT = "7a318df8625c81d953e145745d021b945de086d5169fada3f428da08648059fe"


def _policy(**changes: object) -> StrategyPolicy:
    values: dict[str, object] = {
        "policy_id": "policy",
        "policy_version": "1.0",
        "strategy_identity": StrategyIdentity("strategy", "2"),
        "enabled_directions": (StrategyDirection.SELL, StrategyDirection.BUY),
        "minimum_rr": 2.5,
        "minimum_confidence": 0.75,
        "required_evidence": ("wave", "context"),
        "optional_evidence": ("liquidity",),
        "expiration_seconds": 3600,
        "numeric_precision": 5,
        "elliott_policy": (("degree", "MINOR"), ("allow_alternate", "true")),
    }
    values.update(changes)
    return StrategyPolicy(**values)


def test_identity_is_immutable_hashable_reconstructable_and_referenced() -> None:
    identity = StrategyPolicyIdentity(" policy ", " 1.0 ", "0" * 64)
    rebuilt = StrategyPolicyIdentity(
        identity.policy_id, identity.policy_version, identity.fingerprint
    )
    assert identity == rebuilt
    assert hash(identity) == hash(rebuilt)
    assert identity.reference == f"a07-policy:1:policy:1.0:sha256:{'0' * 64}"
    assert identity != StrategyIdentity("policy", "1.0")
    with pytest.raises(FrozenInstanceError):
        identity.policy_id = "changed"


@pytest.mark.parametrize("field", ["policy_id", "policy_version"])
@pytest.mark.parametrize("value", [None, "", " ", 1, "bad:id", "é"])
def test_identity_rejects_invalid_identifiers(field: str, value: object) -> None:
    values: dict[str, object] = {"policy_id": "p", "policy_version": "1", "fingerprint": "0" * 64}
    values[field] = value
    with pytest.raises(DataIntegrityError):
        StrategyPolicyIdentity(**values)


@pytest.mark.parametrize("value", [None, "", 1, "0" * 63, "0" * 65, "A" * 64, "g" * 64])
def test_identity_rejects_invalid_fingerprints(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        StrategyPolicyIdentity("p", "1", value)


def test_policy_exact_vector_canonicalization_and_nested_immutability() -> None:
    policy = _policy()
    assert policy.identity.fingerprint == FINGERPRINT
    assert policy.identity.reference == f"a07-policy:1:policy:1.0:sha256:{FINGERPRINT}"
    assert policy.enabled_directions == (StrategyDirection.BUY, StrategyDirection.SELL)
    assert policy.required_evidence == ("context", "wave")
    assert policy.elliott_policy == (("allow_alternate", "true"), ("degree", "MINOR"))
    with pytest.raises(FrozenInstanceError):
        policy.minimum_rr = 3.0
    with pytest.raises(TypeError):
        cast(Any, policy.required_evidence)[0] = "other"


def test_policy_equality_hash_repeated_construction_and_empty_configuration() -> None:
    first = _policy()
    second = _policy()
    empty = _policy(required_evidence=(), optional_evidence=(), elliott_policy=())
    assert first == second
    assert hash(first) == hash(second)
    assert first.identity == second.identity
    assert empty.required_evidence == ()
    assert empty.optional_evidence == ()
    assert empty.elliott_policy == ()


def test_policy_reconstructs_and_rejects_inconsistent_identity() -> None:
    policy = _policy()
    rebuilt = StrategyPolicy.reconstruct(policy.identity, *policy._values()[1:])
    assert rebuilt == policy
    assert hash(rebuilt) == hash(policy)
    wrong = StrategyPolicyIdentity("policy", "1.0", "0" * 64)
    with pytest.raises(DataIntegrityError, match="does not match"):
        StrategyPolicy.reconstruct(wrong, *policy._values()[1:])
    with pytest.raises(DataIntegrityError):
        StrategyPolicy.reconstruct(object(), *policy._values()[1:])


@pytest.mark.parametrize(
    "changes",
    [
        {"policy_id": "other"},
        {"policy_version": "2"},
        {"strategy_identity": StrategyIdentity("other", "2")},
        {"enabled_directions": (StrategyDirection.BUY,)},
        {"minimum_rr": 3.0},
        {"minimum_confidence": 0.5},
        {"required_evidence": ("context",)},
        {"optional_evidence": ()},
        {"expiration_seconds": 60},
        {"numeric_precision": 4},
        {"elliott_policy": (("degree", "MAJOR"),)},
    ],
)
def test_every_semantic_field_changes_fingerprint(changes: dict[str, object]) -> None:
    assert _policy(**changes).identity.fingerprint != FINGERPRINT


def test_permutations_and_negative_zero_have_canonical_identity() -> None:
    left = _policy()
    right = _policy(
        enabled_directions=(StrategyDirection.BUY, StrategyDirection.SELL),
        required_evidence=("context", "wave"),
        elliott_policy=(("allow_alternate", "true"), ("degree", "MINOR")),
    )
    assert left == right
    zero = _policy(minimum_confidence=-0.0)
    positive_zero = _policy(minimum_confidence=0.0)
    assert zero == positive_zero
    assert _policy(minimum_rr=1e20).minimum_rr == 1e20


@pytest.mark.parametrize(
    "value",
    [
        (),
        [],
        (StrategyDirection.NO_TRADE,),
        (StrategyDirection.BUY, StrategyDirection.BUY),
        ("BUY",),
    ],
)
def test_directions_fail_closed(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(enabled_directions=value)


@pytest.mark.parametrize(
    "value", [0.0, -1.0, float("nan"), float("inf"), float("-inf"), 2, True, "2", Decimal(2)]
)
def test_minimum_rr_fails_closed(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(minimum_rr=value)


@pytest.mark.parametrize("value", [0.0, 1.0])
def test_minimum_confidence_accepts_boundaries(value: float) -> None:
    assert _policy(minimum_confidence=value).minimum_confidence == value


@pytest.mark.parametrize(
    "value", [-0.1, 1.1, float("nan"), float("inf"), 1, True, "0.5", Decimal("0.5")]
)
def test_minimum_confidence_fails_closed(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(minimum_confidence=value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("required_evidence", []),
        ("required_evidence", ("wave", "wave")),
        ("required_evidence", ("",)),
        ("required_evidence", (1,)),
        ("optional_evidence", []),
        ("optional_evidence", ("liquidity", "liquidity")),
        ("optional_evidence", ("",)),
    ],
)
def test_evidence_fails_closed(field: str, value: object) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(**{field: value})


def test_evidence_overlap_fails_closed() -> None:
    with pytest.raises(DataIntegrityError):
        _policy(optional_evidence=("wave",))


@pytest.mark.parametrize("field", ["expiration_seconds", "numeric_precision"])
@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_integer_policy_fields_reject_wrong_types(field: str, value: object) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [("expiration_seconds", 0), ("expiration_seconds", -1), ("numeric_precision", -1)],
)
def test_integer_policy_fields_reject_invalid_bounds(field: str, value: int) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(**{field: value})


def test_integer_policy_fields_accept_boundaries() -> None:
    policy = _policy(expiration_seconds=1, numeric_precision=0)
    assert (policy.expiration_seconds, policy.numeric_precision) == (1, 0)


@pytest.mark.parametrize(
    "value",
    [
        [],
        (("key",),),
        (["key", "value"],),
        (("", "value"),),
        (("key", ""),),
        (("key", 1),),
        (("key", "1"), ("key", "2")),
    ],
)
def test_elliott_policy_fails_closed(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        _policy(elliott_policy=value)


def test_diagnostics_are_canonical_immutable_and_reconstructable() -> None:
    value = PolicyDiagnostics(("POLICY_REFERENCE_MISMATCH",))
    rebuilt = PolicyDiagnostics(value.diagnostics)
    assert rebuilt == value
    assert hash(rebuilt) == hash(value)
    assert PolicyDiagnostics().diagnostics == ()
    with pytest.raises(FrozenInstanceError):
        value.diagnostics = ()


@pytest.mark.parametrize(
    "value",
    [["POLICY_REFERENCE_MISMATCH"], ("UNKNOWN",), ("",), ("POLICY_REFERENCE_MISMATCH",) * 2],
)
def test_diagnostics_fail_closed(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        PolicyDiagnostics(value)


def test_validation_match_mismatch_hash_and_immutability() -> None:
    policy = _policy()
    matched = PolicyValidation(policy, policy.identity.reference)
    other = _policy(policy_version="2")
    mismatched = PolicyValidation(policy, other.identity.reference)
    assert matched.valid and matched.diagnostics == PolicyDiagnostics()
    assert not mismatched.valid
    assert mismatched.diagnostics.diagnostics == ("POLICY_REFERENCE_MISMATCH",)
    assert matched == PolicyValidation(policy, policy.identity.reference)
    assert hash(matched) == hash(PolicyValidation(policy, policy.identity.reference))
    with pytest.raises(FrozenInstanceError):
        matched.valid = False


@pytest.mark.parametrize(
    "reference",
    [
        None,
        "",
        " bad ",
        "policy:1:p:1:sha256:" + "0" * 64,
        "a07-policy:2:p:1:sha256:" + "0" * 64,
        "a07-policy:1::1:sha256:" + "0" * 64,
        "a07-policy:1:p::sha256:" + "0" * 64,
        "a07-policy:1:p:1:sha1:" + "0" * 64,
        "a07-policy:1:p:1:sha256:" + "A" * 64,
        "a07-policy:1:p:1:sha256:" + "g" * 64,
        "a07-policy:1:p:1:sha256:" + "0" * 63,
        "a07-policy:1:p:1:sha256:" + "0" * 64 + ":extra",
    ],
)
def test_validation_rejects_malformed_references(reference: object) -> None:
    with pytest.raises(DataIntegrityError):
        PolicyValidation(_policy(), reference)


def test_validation_rejects_wrong_policy_type() -> None:
    with pytest.raises(DataIntegrityError):
        PolicyValidation(object(), _policy().identity.reference)


def test_e00_opaque_reference_compatibility() -> None:
    policy = _policy()
    request = StrategyEvaluationRequest(
        policy.strategy_identity,
        StrategyEvidenceIdentity("evidence", "source"),
        "2026-01-01T00:00:00+00:00",
        "A05-v1.0.0",
        policy.identity.reference,
    )
    assert PolicyValidation(policy, request.policy_reference).valid


def test_external_state_independence_and_dependency_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = _policy()
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    monkeypatch.setenv("EPIP_POLICY", "changed")
    os.environ.setdefault("LC_ALL", "C")
    after = _policy()
    assert before == after
    source = inspect.getsource(__import__("epip.a07.policy", fromlist=["policy"]))
    assert "epip.a05" not in source and "epip.a06" not in source
    for successor in (
        "evidence",
        "direction",
        "entry",
        "stop",
        "target",
        "reward_risk",
        "confidence",
        "signal",
    ):
        assert f"epip.a07.{successor}" not in source


def test_missing_and_unknown_policy_arguments_fail_closed() -> None:
    values = {
        "policy_id": "p",
        "policy_version": "1",
        "strategy_identity": StrategyIdentity("s", "1"),
        "enabled_directions": (StrategyDirection.BUY,),
        "minimum_rr": 1.0,
        "minimum_confidence": 0.0,
        "required_evidence": (),
        "optional_evidence": (),
        "expiration_seconds": 1,
        "numeric_precision": 0,
        "elliott_policy": (),
    }
    values.pop("minimum_rr")
    with pytest.raises(TypeError):
        StrategyPolicy(**values)
    values["minimum_rr"] = 1.0
    values["unknown"] = True
    with pytest.raises(TypeError):
        StrategyPolicy(**values)


def test_policy_rejects_wrong_strategy_identity() -> None:
    with pytest.raises(DataIntegrityError):
        _policy(strategy_identity=object())
