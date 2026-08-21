"""Component tests for A04-E03 deterministic governed-candidate selection."""

from __future__ import annotations

from inspect import getmembers, isfunction
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.candidates import CandidateDiagnostics
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
    ResolutionProfile,
)
from epip.evidence.selection import SelectionDiagnostics, SelectionEngine, SelectionPolicy
from epip.governance import GovernanceEpoch, GovernanceRejection, RegistryEntry


def _entry(producer: str = "producer-a") -> RegistryEntry:
    return RegistryEntry(
        producer,
        "1.0.0",
        f"descriptor-{producer}",
        "owner-1",
        "1.0.0",
        f"build-{producer}",
        (("market.structure", "1.0.0"),),
        "Trusted",
        (),
        (),
        "Enabled",
        ("admission-1",),
    )


def _requirement(**changes: object) -> EvidenceRequirement:
    values: dict[str, object] = {
        "requirement_id": "requirement-1",
        "evidence_type": "market.structure",
        "semantic_version": "1.0.0",
        "subject": "EURUSD",
        "scope": "H1",
        "dependency_type": DependencyType.MANDATORY,
    }
    values.update(changes)
    return EvidenceRequirement(**values)  # type: ignore[arg-type]


def _policy(**changes: object) -> SelectionPolicy:
    values: dict[str, object] = {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
    }
    values.update(changes)
    return SelectionPolicy(ResolutionProfile(**values))  # type: ignore[arg-type]


def _candidates(
    entries: tuple[RegistryEntry, ...],
    rejections: tuple[GovernanceRejection | DiagnosticReason, ...] = (),
) -> CandidateDiagnostics:
    return CandidateDiagnostics(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(4),
        entries,
        cast(Any, rejections),
    )


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import selection

    public_classes = {
        name
        for name, value in vars(selection).items()
        if isinstance(value, type)
        if value.__module__ == selection.__name__ and not name.startswith("_")
    }
    assert public_classes == {"SelectionEngine", "SelectionPolicy", "SelectionDiagnostics"}


def test_selects_one_governed_candidate_and_preserves_snapshot() -> None:
    entry = _entry()
    governed = _candidates((entry,))
    result = SelectionEngine.select(governed, _requirement(), _policy())
    assert result.selected_candidates == (entry,)
    assert result.considered_candidates == (entry,)
    assert result[:3] == ("snapshot-1", "manifest-1", GovernanceEpoch(4))
    assert result.diagnostics == ()


def test_explicit_pin_precedes_general_ambiguity() -> None:
    first = _entry("producer-a")
    pinned = _entry("producer-b")
    result = SelectionEngine.select(
        _candidates((first, pinned)),
        _requirement(),
        _policy(pinned_producer_id="producer-b"),
    )
    assert result.selected_candidates == (pinned,)
    assert result.diagnostics == ()


def test_missing_pin_fails_closed() -> None:
    result = SelectionEngine.select(
        _candidates((_entry(),)),
        _requirement(),
        _policy(pinned_producer_id="producer-z"),
    )
    assert result.selected_candidates == ()
    assert result.diagnostics[-1].code is DiagnosticCode.MISSING_MANDATORY_DEPENDENCY
    assert result.diagnostics[-1].candidate_id == "producer-z"


@pytest.mark.parametrize(
    ("requirement", "code"),
    [
        (_requirement(), DiagnosticCode.MISSING_MANDATORY_DEPENDENCY),
        (
            _requirement(
                dependency_type=DependencyType.OPTIONAL,
                min_cardinality=0,
                max_cardinality=1,
                absence_semantics="explicit-absence",
            ),
            DiagnosticCode.ABSENT_OPTIONAL_DEPENDENCY,
        ),
    ],
)
def test_zero_candidates_are_diagnosed(
    requirement: EvidenceRequirement, code: DiagnosticCode
) -> None:
    result = SelectionEngine.select(_candidates(()), requirement, _policy())
    assert result.selected_candidates == ()
    assert result.diagnostics[-1].code is code


def test_multiple_candidates_fail_ambiguously_without_a_rule() -> None:
    result = SelectionEngine.select(
        _candidates((_entry("producer-b"), _entry("producer-a"))),
        _requirement(),
        _policy(),
    )
    assert result.selected_candidates == ()
    assert result.diagnostics[-1].code is DiagnosticCode.AMBIGUOUS_DEPENDENCY
    assert tuple(entry.producer_identity for entry in result.considered_candidates) == (
        "producer-a",
        "producer-b",
    )


def test_multi_provider_policy_preserves_canonical_order() -> None:
    first = _entry("producer-a")
    second = _entry("producer-b")
    requirement = _requirement(min_cardinality=2, max_cardinality=2, exact_cardinality=2)
    policy = _policy(allow_multi_provider=True)
    expected: SelectionDiagnostics | None = None
    for ordering in permutations((first, second)):
        result = SelectionEngine.select(_candidates(ordering), requirement, policy)
        assert result.selected_candidates == (first, second)
        if expected is None:
            expected = result
        else:
            assert result == expected


def test_multi_provider_subset_ambiguity_fails_closed() -> None:
    result = SelectionEngine.select(
        _candidates((_entry("producer-c"), _entry("producer-a"), _entry("producer-b"))),
        _requirement(min_cardinality=1, max_cardinality=2),
        _policy(allow_multi_provider=True),
    )
    assert result.selected_candidates == ()
    assert result.diagnostics[-1].code is DiagnosticCode.AMBIGUOUS_DEPENDENCY


@pytest.mark.parametrize(
    "requirement",
    [
        _requirement(min_cardinality=2, max_cardinality=2, exact_cardinality=2),
        _requirement(min_cardinality=2, max_cardinality=3),
    ],
)
def test_insufficient_cardinality_fails_closed(requirement: EvidenceRequirement) -> None:
    result = SelectionEngine.select(_candidates((_entry(),)), requirement, _policy())
    assert result.selected_candidates == ()
    assert result.diagnostics[-1].code is DiagnosticCode.CARDINALITY_VIOLATION


def test_prior_governance_rejections_are_preserved() -> None:
    rejection = DiagnosticReason(
        DiagnosticCode.INELIGIBLE_PROVIDER,
        "requirement-1",
        "governance rejection",
        "producer-z",
        "1.0.0",
    )
    result = SelectionEngine.select(
        _candidates((_entry(),), (rejection,)), _requirement(), _policy()
    )
    assert result.diagnostics == (rejection,)


@pytest.mark.parametrize(
    ("reason_code", "expected"),
    [
        ("E02_INCOMPATIBLE_PROVIDER", DiagnosticCode.INCOMPATIBLE_DEPENDENCY),
        ("E02_EXPIRED_PROVIDER", DiagnosticCode.EXPIRED_OR_REVOKED_CERTIFICATION),
        ("E02_REVOKED_PROVIDER", DiagnosticCode.EXPIRED_OR_REVOKED_CERTIFICATION),
        ("E02_UNCERTIFIED_PROVIDER", DiagnosticCode.INELIGIBLE_PROVIDER),
    ],
)
def test_governance_rejections_use_frozen_e00_diagnostics(
    reason_code: str, expected: DiagnosticCode
) -> None:
    rejection = GovernanceRejection(reason_code, ("producer-z",))
    result = SelectionEngine.select(
        _candidates((_entry(),), (rejection,)), _requirement(), _policy()
    )
    assert result.diagnostics == (
        DiagnosticReason(
            expected,
            "requirement-1",
            reason_code,
            "producer-z",
            "1.0.0",
        ),
    )


def test_policy_and_diagnostics_are_immutable_and_hashable() -> None:
    policy = _policy()
    result = SelectionEngine.select(_candidates((_entry(),)), _requirement(), policy)
    with pytest.raises(AttributeError):
        policy.resolution_profile = ResolutionProfile("other", "1.0.0")  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.selected_candidates = ()  # type: ignore[misc]
    assert hash(policy)
    assert hash(result)


def test_selection_preserves_every_immutable_input_and_is_repeatable() -> None:
    candidates = _candidates((_entry(),))
    requirement = _requirement()
    policy = _policy()
    inputs = (candidates, requirement, policy)
    hashes = tuple(hash(item) for item in inputs)
    first = SelectionEngine.select(candidates, requirement, policy)
    second = SelectionEngine.select(candidates, requirement, policy)
    assert first == second
    assert hashes == tuple(hash(item) for item in inputs)


def test_profile_binding_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="does not match"):
        SelectionEngine.select(
            _candidates((_entry(),)),
            _requirement(resolution_profile_id="required-profile"),
            _policy(),
        )


@pytest.mark.parametrize(
    "call",
    [
        lambda: SelectionEngine.select(
            _candidates((_entry(),)),
            _requirement(),
            SelectionPolicy(cast(Any, object())),
        ),
        lambda: SelectionEngine.select(cast(Any, object()), _requirement(), _policy()),
        lambda: SelectionEngine.select(_candidates((_entry(),)), cast(Any, object()), _policy()),
        lambda: SelectionEngine.select(
            _candidates((_entry(),)), _requirement(), cast(Any, object())
        ),
        lambda: SelectionEngine.select(
            CandidateDiagnostics(
                "snapshot-1",
                "manifest-1",
                GovernanceEpoch(1),
                (_entry(), _entry()),
                (),
            ),
            _requirement(),
            _policy(),
        ),
    ],
)
def test_invalid_inputs_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_no_predecessor_or_downstream_responsibility_is_present() -> None:
    forbidden = {
        "enumerate",
        "filter",
        "validate_phase2",
        "evaluate",
        "certify",
        "build_graph",
        "traverse_graph",
        "orchestrate",
        "execute",
        "canonical_identity",
        "replay",
        "track_execution",
        "integrate_lifecycle",
    }
    methods = {
        name
        for owner in (SelectionEngine, SelectionPolicy, SelectionDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)


def test_selection_does_not_import_predecessor_validation_or_governance_services() -> None:
    from epip.evidence import selection

    names = vars(selection)
    assert "CandidateFilter" not in names
    assert "CandidateEnumerator" not in names
    assert "CompatibilityEvaluator" not in names
    assert "SemanticValidator" not in names
    assert "CertificationRecord" not in names
    assert "CompatibilityDecision" not in names


def test_selection_uses_only_frozen_e00_diagnostics() -> None:
    result = SelectionEngine.select(_candidates(()), _requirement(), _policy())
    assert all(isinstance(reason.code, DiagnosticCode) for reason in result.diagnostics)
