"""A07-E02 behavioral tests for immutable evidence binding."""

import inspect
import os
from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from epip.a07.evidence import (
    EvidenceBinding,
    EvidenceDiagnostics,
    EvidenceValidation,
    StrategyEvidenceSnapshot,
)
from epip.a07.foundation import StrategyDirection, StrategyEvidenceIdentity, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError


def _strategy(identifier: str = "strategy") -> StrategyIdentity:
    return StrategyIdentity(identifier, "1")


def _policy(
    *, required: tuple[str, ...] = ("context", "wave"), optional: tuple[str, ...] = ("liquidity",)
) -> StrategyPolicy:
    return StrategyPolicy(
        "policy",
        "1",
        _strategy(),
        (StrategyDirection.BUY,),
        2.0,
        0.5,
        required,
        optional,
        60,
        5,
        (),
    )


def _snapshot(
    key: str,
    *,
    evidence_id: str | None = None,
    strategy: StrategyIdentity | None = None,
    provenance: str = "A05/A06:frozen",
    fresh: bool = True,
    eligible: bool = True,
) -> StrategyEvidenceSnapshot:
    return StrategyEvidenceSnapshot(
        strategy or _strategy(),
        StrategyEvidenceIdentity(evidence_id or f"evidence-{key}", provenance),
        key,
        fresh,
        eligible,
    )


def _binding() -> EvidenceBinding:
    return EvidenceBinding(
        _policy(),
        (_snapshot("wave"), _snapshot("liquidity"), _snapshot("context")),
    )


def test_snapshot_preserves_identity_provenance_and_canonical_key() -> None:
    strategy = _strategy()
    identity = StrategyEvidenceIdentity("evidence", "A06:frozen")
    value = StrategyEvidenceSnapshot(strategy, identity, " Evidence.Key ", True, False)
    rebuilt = StrategyEvidenceSnapshot(
        value.strategy_identity,
        value.evidence_identity,
        value.evidence_key,
        value.fresh,
        value.temporally_eligible,
    )
    assert value.evidence_key == "Evidence.Key"
    assert value.evidence_identity is identity
    assert value.evidence_identity.provenance == "A06:frozen"
    assert rebuilt == value and hash(rebuilt) == hash(value)
    assert value != identity


@pytest.mark.parametrize("field", ["strategy_identity", "evidence_identity"])
@pytest.mark.parametrize("value", [None, object(), "identity"])
def test_snapshot_rejects_wrong_predecessor_types(field: str, value: object) -> None:
    values: dict[str, object] = {
        "strategy_identity": _strategy(),
        "evidence_identity": StrategyEvidenceIdentity("e", "p"),
        "evidence_key": "key",
        "fresh": True,
        "temporally_eligible": True,
    }
    values[field] = value
    with pytest.raises(DataIntegrityError):
        StrategyEvidenceSnapshot(**values)


@pytest.mark.parametrize("value", [None, "", "   ", 1, object()])
def test_snapshot_rejects_invalid_evidence_key(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        StrategyEvidenceSnapshot(_strategy(), StrategyEvidenceIdentity("e", "p"), value, True, True)


@pytest.mark.parametrize("field", ["fresh", "temporally_eligible"])
@pytest.mark.parametrize("value", [0, 1, None, "true", object()])
def test_snapshot_rejects_non_boolean_facts(field: str, value: object) -> None:
    values: dict[str, object] = {
        "strategy_identity": _strategy(),
        "evidence_identity": StrategyEvidenceIdentity("e", "p"),
        "evidence_key": "key",
        "fresh": True,
        "temporally_eligible": True,
    }
    values[field] = value
    with pytest.raises(DataIntegrityError):
        StrategyEvidenceSnapshot(**values)


def test_snapshot_is_immutable_and_has_no_mutable_nested_state() -> None:
    snapshot = _snapshot("wave")
    with pytest.raises(FrozenInstanceError):
        snapshot.fresh = False
    with pytest.raises(FrozenInstanceError):
        snapshot.evidence_identity.evidence_id = "changed"


def test_binding_derives_all_fields_and_canonicalizes_permutations() -> None:
    policy = _policy(required=("wave", "context"), optional=("liquidity",))
    values = (_snapshot("wave"), _snapshot("other"), _snapshot("liquidity"))
    left = EvidenceBinding(policy, values)
    right = EvidenceBinding(policy, tuple(reversed(values)))
    assert left == right and hash(left) == hash(right)
    assert tuple(item.evidence_key for item in left.available_evidence) == (
        "liquidity",
        "other",
        "wave",
    )
    assert tuple(item.evidence_key for item in left.bound_required) == ("wave",)
    assert tuple(item.evidence_key for item in left.bound_optional) == ("liquidity",)
    assert left.missing_required == ("context",)
    assert tuple(item.evidence_key for item in left.unexpected_evidence) == ("other",)


def test_empty_available_evidence_is_valid_binding_input() -> None:
    binding = EvidenceBinding(_policy(), ())
    assert binding.available_evidence == binding.bound_required == binding.bound_optional == ()
    assert binding.unexpected_evidence == ()
    assert binding.missing_required == ("context", "wave")


@pytest.mark.parametrize("value", [[], {}, set(), iter(())])
def test_binding_rejects_mutable_or_non_tuple_container(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        EvidenceBinding(_policy(), value)


def test_binding_rejects_wrong_policy_and_snapshot_types() -> None:
    with pytest.raises(DataIntegrityError):
        EvidenceBinding(object(), ())
    with pytest.raises(DataIntegrityError):
        EvidenceBinding(_policy(), (object(),))


def test_binding_rejects_duplicate_equal_snapshot_and_key() -> None:
    snapshot = _snapshot("wave")
    with pytest.raises(DataIntegrityError, match="keys"):
        EvidenceBinding(_policy(), (snapshot, snapshot))
    with pytest.raises(DataIntegrityError, match="keys"):
        EvidenceBinding(
            _policy(),
            (snapshot, _snapshot("wave", evidence_id="different", fresh=False)),
        )


def test_binding_rejects_duplicate_evidence_identity_across_keys() -> None:
    with pytest.raises(DataIntegrityError, match="identities"):
        EvidenceBinding(
            _policy(),
            (_snapshot("wave", evidence_id="same"), _snapshot("context", evidence_id="same")),
        )


def test_binding_reconstruction_round_trip_and_contradictions() -> None:
    value = _binding()
    args = (
        value.policy,
        value.available_evidence,
        value.bound_required,
        value.bound_optional,
        value.missing_required,
        value.unexpected_evidence,
    )
    rebuilt = EvidenceBinding.reconstruct(*args)
    assert rebuilt == value and hash(rebuilt) == hash(value)
    for index in range(2, 6):
        changed = list(args)
        changed[index] = ()
        if args[index] == ():
            changed[index] = ("wrong",)
        with pytest.raises(DataIntegrityError):
            EvidenceBinding.reconstruct(*changed)
    with pytest.raises(DataIntegrityError):
        EvidenceBinding.reconstruct(
            value.policy,
            tuple(reversed(value.available_evidence)),
            value.bound_required,
            value.bound_optional,
            value.missing_required,
            value.unexpected_evidence,
        )


def test_binding_is_immutable_and_nested_collections_are_immutable() -> None:
    binding = _binding()
    with pytest.raises(FrozenInstanceError):
        binding.policy = _policy(required=())
    with pytest.raises(TypeError):
        cast(Any, binding.available_evidence)[0] = _snapshot("other")


def test_all_required_satisfied_and_optional_absence_are_valid() -> None:
    policy = _policy(optional=("optional",))
    validation = EvidenceValidation(
        EvidenceBinding(policy, (_snapshot("wave"), _snapshot("context")))
    )
    assert validation.valid
    assert validation.diagnostics == EvidenceDiagnostics()


def test_missing_required_is_result_not_exception() -> None:
    binding = EvidenceBinding(_policy(), (_snapshot("wave"),))
    validation = EvidenceValidation(binding)
    assert binding.missing_required == ("context",)
    assert not validation.valid
    assert validation.diagnostics.diagnostics == ("MISSING_REQUIRED_EVIDENCE",)


@pytest.mark.parametrize(
    ("key", "changes", "code"),
    [
        ("wave", {"fresh": False}, "STALE_REQUIRED_EVIDENCE"),
        (
            "wave",
            {"eligible": False},
            "TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE",
        ),
        ("liquidity", {"fresh": False}, "STALE_OPTIONAL_EVIDENCE"),
        (
            "liquidity",
            {"eligible": False},
            "TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE",
        ),
    ],
)
def test_required_and_optional_status_failures(
    key: str, changes: dict[str, object], code: str
) -> None:
    snapshots = (_snapshot("wave"), _snapshot("context"), _snapshot("liquidity"))
    replacement = _snapshot(key, **changes)  # type: ignore[arg-type]
    available = tuple(replacement if item.evidence_key == key else item for item in snapshots)
    validation = EvidenceValidation(EvidenceBinding(_policy(), available))
    assert not validation.valid
    assert validation.diagnostics.diagnostics == (code,)


def test_strategy_mismatch_is_validation_result_for_required_optional_and_unexpected() -> None:
    other = _strategy("other")
    for key in ("wave", "liquidity", "unexpected"):
        available: tuple[StrategyEvidenceSnapshot, ...] = (
            _snapshot("context"),
            _snapshot("wave" if key != "wave" else key, strategy=other if key == "wave" else None),
            _snapshot(
                "liquidity",
                strategy=other if key == "liquidity" else None,
            ),
        )
        if key == "unexpected":
            available += (_snapshot(key, strategy=other),)
        validation = EvidenceValidation(EvidenceBinding(_policy(), available))
        assert "STRATEGY_IDENTITY_MISMATCH" in validation.diagnostics.diagnostics


def test_unexpected_evidence_is_preserved_diagnosed_and_invalid() -> None:
    unexpected = _snapshot("extra")
    binding = EvidenceBinding(_policy(), (_snapshot("context"), _snapshot("wave"), unexpected))
    validation = EvidenceValidation(binding)
    assert binding.unexpected_evidence == (unexpected,)
    assert validation.diagnostics.diagnostics == ("UNEXPECTED_EVIDENCE",)
    assert not validation.valid


def test_simultaneous_diagnostics_are_unique_and_lexicographic() -> None:
    binding = EvidenceBinding(
        _policy(),
        (
            _snapshot("wave", fresh=False, eligible=False, strategy=_strategy("other")),
            _snapshot("liquidity", fresh=False, eligible=False),
            _snapshot("extra"),
        ),
    )
    validation = EvidenceValidation(binding)
    assert validation.diagnostics.diagnostics == tuple(
        sorted(
            {
                "MISSING_REQUIRED_EVIDENCE",
                "STALE_OPTIONAL_EVIDENCE",
                "STALE_REQUIRED_EVIDENCE",
                "STRATEGY_IDENTITY_MISMATCH",
                "TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE",
                "TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE",
                "UNEXPECTED_EVIDENCE",
            }
        )
    )


def test_diagnostics_accept_every_code_and_canonicalize() -> None:
    values = (
        "UNEXPECTED_EVIDENCE",
        "TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE",
        "TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE",
        "STRATEGY_IDENTITY_MISMATCH",
        "STALE_REQUIRED_EVIDENCE",
        "STALE_OPTIONAL_EVIDENCE",
        "MISSING_REQUIRED_EVIDENCE",
    )
    diagnostics = EvidenceDiagnostics(values)
    rebuilt = EvidenceDiagnostics(diagnostics.diagnostics)
    assert diagnostics.diagnostics == tuple(sorted(values))
    assert rebuilt == diagnostics and hash(rebuilt) == hash(diagnostics)


@pytest.mark.parametrize(
    "value",
    [
        ["MISSING_REQUIRED_EVIDENCE"],
        ("UNKNOWN",),
        ("",),
        (1,),
        ("MISSING_REQUIRED_EVIDENCE", "MISSING_REQUIRED_EVIDENCE"),
    ],
)
def test_diagnostics_fail_closed(value: object) -> None:
    with pytest.raises(DataIntegrityError):
        EvidenceDiagnostics(value)


def test_diagnostics_are_immutable() -> None:
    diagnostics = EvidenceDiagnostics(("MISSING_REQUIRED_EVIDENCE",))
    with pytest.raises(FrozenInstanceError):
        diagnostics.diagnostics = ()


def test_validation_reconstruction_round_trip_and_inconsistency() -> None:
    value = EvidenceValidation(_binding())
    rebuilt = EvidenceValidation.reconstruct(value.binding, value.valid, value.diagnostics)
    assert rebuilt == value and hash(rebuilt) == hash(value)
    with pytest.raises(DataIntegrityError):
        EvidenceValidation.reconstruct(value.binding, not value.valid, value.diagnostics)
    with pytest.raises(DataIntegrityError):
        EvidenceValidation.reconstruct(
            value.binding,
            value.valid,
            EvidenceDiagnostics(("UNEXPECTED_EVIDENCE",)),
        )
    with pytest.raises(DataIntegrityError):
        EvidenceValidation.reconstruct(value.binding, 1, value.diagnostics)
    with pytest.raises(DataIntegrityError):
        EvidenceValidation.reconstruct(value.binding, value.valid, object())


def test_validation_rejects_wrong_binding_and_is_immutable() -> None:
    with pytest.raises(DataIntegrityError):
        EvidenceValidation(object())
    validation = EvidenceValidation(_binding())
    with pytest.raises(FrozenInstanceError):
        validation.valid = False


def test_external_state_independence_and_dependency_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = EvidenceValidation(_binding())
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    monkeypatch.setenv("EPIP_EVIDENCE", "changed")
    os.environ.setdefault("LC_ALL", "C")
    after = EvidenceValidation(_binding())
    assert before == after
    source = inspect.getsource(__import__("epip.a07.evidence", fromlist=["evidence"]))
    for forbidden in ("epip.a05", "epip.a06", "datetime", "time.time", "random"):
        assert forbidden not in source
    for successor in (
        "direction",
        "entry",
        "stop",
        "target",
        "reward_risk",
        "confidence",
        "signal",
    ):
        assert f"epip.a07.{successor}" not in source


def test_missing_and_unknown_arguments_are_rejected() -> None:
    with pytest.raises(TypeError):
        StrategyEvidenceSnapshot(  # type: ignore[call-arg]
            _strategy(), StrategyEvidenceIdentity("e", "p"), "key", True
        )
    with pytest.raises(TypeError):
        EvidenceBinding(_policy(), (), unknown=True)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        EvidenceValidation.reconstruct(_binding(), True)  # type: ignore[call-arg]
