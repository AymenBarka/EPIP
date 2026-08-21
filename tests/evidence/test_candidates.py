"""Component tests for A04-E02 candidate enumeration and governance filtering."""

from __future__ import annotations

from inspect import getmembers, getsource, isfunction
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.candidates import (
    CandidateDiagnostics,
    CandidateEnumerator,
    CandidateFilter,
)
from epip.evidence.model import (
    CompatibilityEffects,
    DependencyType,
    DiagnosticCode,
    EvidenceRequirement,
)
from epip.evidence.validation import CompatibilityEvaluator
from epip.governance import (
    CertificationRecord,
    CompatibilityDecision,
    GovernanceEpoch,
    RegistryEntry,
    RegistrySnapshot,
)


def _epoch(value: int = 2) -> GovernanceEpoch:
    return GovernanceEpoch(value)


def _certification(producer: str = "producer-a", **changes: object) -> CertificationRecord:
    values: dict[str, object] = {
        "record_identity": f"cert-{producer}",
        "certification_authority_identity": "certification-authority",
        "producer_identity": producer,
        "producer_version": "1.0.0",
        "implementation_identity": f"build-{producer}",
        "producer_contract_version": "1.0.0",
        "capability_references": (("market.structure", "1.0.0"),),
        "configuration_profile": "default",
        "schema_versions": (("output", "1.0.0"),),
        "temporal_profile": "closed",
        "determinism_profile": "deterministic",
        "replay_profile": "historical",
        "execution_profile": "bounded",
        "isolation_profile": "isolated",
        "resource_profile": "bounded",
        "privilege_scope": (),
        "certification_profile_reference": "profile-1",
        "certification_suite_version": "1.0.0",
        "evidence_references": (f"decision-{producer}",),
        "verdict": "passed",
        "effective_epoch": _epoch(1),
        "expiration_or_review_condition": "version-change",
    }
    values.update(changes)
    return CertificationRecord(**values)  # type: ignore[arg-type]


def _compatibility(producer: str = "producer-a", **changes: object) -> CompatibilityDecision:
    values: dict[str, object] = {
        "decision_identity": f"decision-{producer}",
        "compatibility_authority_identity": "compatibility-authority",
        "source_reference": f"{producer}@1.0.0",
        "target_reference": "consumer-1",
        "compatibility_dimension": "semantic",
        "direction": "source-to-target",
        "intended_use": "consumer-1",
        "version_scope": (("source", "1.0.0"), ("target", "1.0.0")),
        "profile_scope": (("scope", "H1"),),
        "evidence_references": ("evidence-1",),
        "policy_version": "1.0.0",
        "effective_epoch": _epoch(1),
        "review_or_expiry_condition": "version-change",
    }
    values.update(changes)
    return CompatibilityDecision(**values)  # type: ignore[arg-type]


def _entry(producer: str = "producer-a", **changes: object) -> RegistryEntry:
    values: dict[str, object] = {
        "producer_identity": producer,
        "producer_version": "1.0.0",
        "descriptor_reference": f"descriptor-{producer}",
        "owner_identity": "owner-1",
        "producer_contract_version": "1.0.0",
        "implementation_identity": f"build-{producer}",
        "capability_references": (("market.structure", "1.0.0"),),
        "trust_standing": "Trusted",
        "certification_records": (_certification(producer),),
        "compatibility_decisions": (_compatibility(producer),),
        "lifecycle_standing": "Enabled",
        "governance_provenance": ("admission-1",),
    }
    values.update(changes)
    return RegistryEntry(**values)  # type: ignore[arg-type]


def _effects(producer: str = "producer-a", **changes: object) -> CompatibilityEffects:
    values: dict[str, object] = {
        "decision_reference": f"decision-{producer}",
        "effects_version": "1.0.0",
        "conversion": None,
        "narrowing": None,
        "widening": None,
        "unit_effect": "structure-state",
        "completeness_effect": "PRESENT",
        "temporal_effect": "window-1",
        "quality_effect": "accepted",
        "provenance_effect": "feed-1",
    }
    values.update(changes)
    return CompatibilityEffects(**values)  # type: ignore[arg-type]


def _snapshot(entries: tuple[RegistryEntry, ...] | None = None) -> RegistrySnapshot:
    return RegistrySnapshot(
        "snapshot-1",
        "manifest-1",
        _epoch(),
        entries if entries is not None else (_entry(),),
        ("action-1",),
        (("admission", "1.0.0"), ("compatibility", "1.0.0")),
    )


def _requirement(**changes: object) -> EvidenceRequirement:
    values: dict[str, object] = {
        "requirement_id": "consumer-1",
        "evidence_type": "market.structure",
        "semantic_version": "1.0.0",
        "subject": "EURUSD",
        "scope": "H1",
        "dependency_type": DependencyType.MANDATORY,
    }
    values.update(changes)
    return EvidenceRequirement(**values)  # type: ignore[arg-type]


def _filter(snapshot: RegistrySnapshot) -> CandidateDiagnostics:
    effects = tuple(_effects(entry.producer_identity) for entry in snapshot.entries)
    return CandidateFilter.filter(snapshot, _requirement(), effects, "semantic")


def test_public_production_inventory_is_exact() -> None:
    from epip.evidence import candidates

    public_classes: set[str] = {
        name
        for name, value in vars(candidates).items()
        if isinstance(value, type)
        if value.__module__ == candidates.__name__ and not name.startswith("_")
    }
    assert public_classes == {
        "CandidateDiagnostics",
        "CandidateEnumerator",
        "CandidateFilter",
    }


def test_enumerates_snapshot_and_evidence_definitions_deterministically() -> None:
    second = _entry("producer-b", capability_references=(("market.trend", "2.0.0"),))
    first = _entry("producer-a")
    snapshot = _snapshot((second, first))
    assert CandidateEnumerator._enumerate(snapshot) == (first, second)
    assert CandidateEnumerator._evidence_definitions(snapshot) == (
        ("market.structure", "1.0.0"),
        ("market.trend", "2.0.0"),
    )


def test_candidate_filter_uses_exact_capability_and_stable_order() -> None:
    first = _entry("producer-a")
    second = _entry("producer-b", capability_references=(("market.trend", "1.0.0"),))
    result = CandidateFilter.filter(
        _snapshot((second, first)), _requirement(), (_effects("producer-a"),), "semantic"
    )
    assert result.candidates == (first,)


def test_governance_filter_accepts_eligible_entry() -> None:
    snapshot = _snapshot()
    result = _filter(snapshot)
    assert result.candidates == snapshot.entries
    assert result.rejections == ()


def test_compatibility_eligibility_is_delegated_exclusively_to_e01(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    def validate(*facts: object) -> None:
        calls.append(facts)

    monkeypatch.setattr(CompatibilityEvaluator, "validate_phase2", validate)
    entry = _entry()
    snapshot = _snapshot((entry,))
    effects = (_effects(),)

    result = CandidateFilter.filter(snapshot, _requirement(), effects, "semantic")

    assert result.candidates == (entry,)
    assert calls == [(_requirement(), snapshot, entry, effects, "semantic")]


def test_e01_fail_closed_diagnostic_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject(*facts: object) -> None:
        del facts
        raise DataIntegrityError("INCOMPATIBLE_DEPENDENCY: delegated rejection")

    monkeypatch.setattr(CompatibilityEvaluator, "validate_phase2", reject)
    result = _filter(_snapshot())
    assert result.candidates == ()
    assert result.rejections[0].code is DiagnosticCode.INCOMPATIBLE_DEPENDENCY


def test_no_local_compatibility_validation_remains() -> None:
    from epip.evidence import candidates

    source = getsource(candidates)
    assert "CompatibilityEvaluator.validate_phase2" in source
    assert "_decision_matches" not in source
    assert "_certification_matches" not in source
    assert "_SUPPORTED_EXPIRY_CONDITIONS" not in source


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"lifecycle_standing": "Declared"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"lifecycle_standing": "Registered"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"lifecycle_standing": "Certified"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"lifecycle_standing": "Disabled"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"lifecycle_standing": "Deprecated"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"lifecycle_standing": "Retired"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"trust_standing": "Untrusted"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"trust_standing": "Revoked"}, DiagnosticCode.INELIGIBLE_PROVIDER),
        ({"certification_records": ()}, DiagnosticCode.INELIGIBLE_PROVIDER),
    ],
)
def test_admission_enablement_lifecycle_trust_and_certification_rejections(
    changes: dict[str, object], reason: DiagnosticCode
) -> None:
    snapshot = _snapshot((cast(Any, _entry)(**changes),))
    result = _filter(snapshot)
    assert result.candidates == ()
    assert tuple(rejection.code for rejection in result.rejections) == (reason,)
    assert result.rejections[0].candidate_id == "producer-a"


@pytest.mark.parametrize("verdict", ["revoked", "expired"])
def test_revoked_and_expired_certifications_are_rejected(verdict: str) -> None:
    entry = _entry(certification_records=(_certification(verdict=verdict),))
    result = _filter(_snapshot((entry,)))
    assert result.rejections[0].code is DiagnosticCode.EXPIRED_OR_REVOKED_CERTIFICATION


def test_future_or_mismatched_certification_is_rejected() -> None:
    for certification in (
        _certification(producer_identity="other"),
        _certification(producer_version="2.0.0"),
        _certification(capability_references=(("other", "1.0.0"),)),
        _certification(effective_epoch=_epoch(3)),
        _certification(verdict="suspended"),
    ):
        entry = _entry(certification_records=(certification,))
        assert _filter(_snapshot((entry,))).rejections[0].code is DiagnosticCode.INELIGIBLE_PROVIDER


@pytest.mark.parametrize(
    "changes",
    [
        {"implementation_identity": "other-build"},
        {"producer_contract_version": "2.0.0"},
    ],
)
def test_certification_is_bound_to_implementation_and_contract(
    changes: dict[str, object],
) -> None:
    entry = _entry(certification_records=(cast(Any, _certification)(**changes),))
    assert _filter(_snapshot((entry,))).rejections[0].code is DiagnosticCode.INELIGIBLE_PROVIDER


@pytest.mark.parametrize(
    "changes",
    [
        {"target_reference": "other"},
        {"source_reference": "other@1.0.0"},
        {"direction": "target-to-source"},
        {"version_scope": (("source", "2.0.0"),)},
        {"version_scope": (("source", "1.0.0"), ("target", "2.0.0"))},
        {"intended_use": "other-use"},
        {"profile_scope": (("scope", "M15"),)},
        {"compatibility_dimension": "structural"},
        {"policy_version": "2.0.0"},
        {"review_or_expiry_condition": "opaque-condition"},
        {"revocation_reference": "revoked-by"},
        {"supersession_reference": "superseded-by"},
        {"effective_epoch": _epoch(3)},
    ],
)
def test_incompatible_decisions_are_rejected(changes: dict[str, object]) -> None:
    entry = _entry(compatibility_decisions=(cast(Any, _compatibility)(**changes),))
    result = _filter(_snapshot((entry,)))
    assert result.rejections[0].code is DiagnosticCode.INCOMPATIBLE_DEPENDENCY


def test_enumeration_requires_no_prematerialized_evidence() -> None:
    entry = _entry()
    result = CandidateFilter.filter(_snapshot((entry,)), _requirement(), (_effects(),), "semantic")
    assert result.candidates == (entry,)


def test_unsupported_certification_expiry_condition_fails_closed() -> None:
    entry = _entry(
        certification_records=(_certification(expiration_or_review_condition="opaque-condition"),)
    )
    result = _filter(_snapshot((entry,)))
    assert result.candidates == ()
    assert result.rejections[0].code is DiagnosticCode.INELIGIBLE_PROVIDER


def test_certification_status_relationship_fails_closed() -> None:
    entry = _entry(
        certification_records=(
            _certification(status_relationship_reference="revocation-or-supersession"),
        )
    )
    assert _filter(_snapshot((entry,))).candidates == ()


def test_missing_or_ambiguous_authoritative_facts_fail_closed() -> None:
    decision = _compatibility()
    for decisions in ((), (decision, decision)):
        entry = _entry(compatibility_decisions=decisions)
        result = _filter(_snapshot((entry,)))
        assert result.rejections[0].code is DiagnosticCode.INCOMPATIBLE_DEPENDENCY
    certification = _certification()
    entry = _entry(certification_records=(certification, certification))
    assert _filter(_snapshot((entry,))).rejections[0].code is DiagnosticCode.INELIGIBLE_PROVIDER


def test_certification_must_authorize_the_compatibility_decision() -> None:
    entry = _entry(certification_records=(_certification(evidence_references=("other-decision",)),))
    result = _filter(_snapshot((entry,)))
    assert result.candidates == ()
    assert result.rejections[0].code is DiagnosticCode.INCOMPATIBLE_DEPENDENCY


def test_missing_compatibility_is_rejected_and_diagnostics_are_preserved() -> None:
    entry = _entry(compatibility_decisions=())
    result = _filter(_snapshot((entry,)))
    assert result.candidates == ()
    assert result.rejections == (result.rejections[0],)
    assert result.rejections[0].candidate_id == "producer-a"
    assert result.rejections[0].semantic_version == "1.0.0"


@pytest.mark.parametrize(
    "effects",
    [
        (),
        (_effects(), _effects()),
        (_effects(decision_reference="other-decision"),),
    ],
)
def test_compatibility_effects_fail_closed(
    effects: tuple[CompatibilityEffects, ...],
) -> None:
    result = CandidateFilter.filter(_snapshot(), _requirement(), effects, "semantic")
    assert result.candidates == ()
    assert result.rejections[0].code is DiagnosticCode.INCOMPATIBLE_DEPENDENCY


def test_repeated_execution_and_input_permutations_are_stable() -> None:
    accepted = _entry("producer-a")
    rejected = _entry("producer-b", lifecycle_standing="Disabled")
    expected: CandidateDiagnostics | None = None
    for entries in ((accepted, rejected), (rejected, accepted)):
        snapshot = _snapshot(entries)
        result = _filter(snapshot)
        if expected is None:
            expected = result
        else:
            assert result == expected
    assert _filter(_snapshot((accepted, rejected))) == expected


@pytest.mark.parametrize(
    "call",
    [
        lambda: CandidateEnumerator._enumerate(cast(Any, object())),
        lambda: CandidateFilter._capabilities(cast(Any, []), "type", "1.0.0"),
        lambda: CandidateFilter._capabilities((_entry(),), "", "1.0.0"),
        lambda: CandidateFilter._capabilities((_entry(),), "type", ""),
        lambda: CandidateFilter.filter(_snapshot(), cast(Any, object()), (_effects(),), "semantic"),
        lambda: CandidateFilter.filter(_snapshot(), _requirement(), (_effects(),), ""),
        lambda: CandidateFilter.filter(_snapshot(), _requirement(), cast(Any, []), "semantic"),
    ],
)
def test_invalid_inputs_fail_closed(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_unknown_registry_states_fail_closed() -> None:
    for entry in (
        _entry(lifecycle_standing="Unknown"),
        _entry(trust_standing="Unknown"),
    ):
        with pytest.raises(DataIntegrityError, match="unknown"):
            _filter(_snapshot((entry,)))


def test_entries_must_be_unique() -> None:
    entry = _entry()
    with pytest.raises(DataIntegrityError, match="unique"):
        CandidateFilter.filter(_snapshot((entry, entry)), _requirement(), (_effects(),), "semantic")


def test_diagnostics_are_deeply_immutable_and_hashable() -> None:
    accepted = _entry("producer-a")
    disabled = _entry("producer-b", lifecycle_standing="Disabled")
    rejected = _filter(_snapshot((disabled,))).rejections[0]
    diagnostics = CandidateDiagnostics(
        "snapshot-1", "manifest-1", _epoch(), (accepted,), (rejected,)
    )
    with pytest.raises(AttributeError):
        diagnostics.candidates = ()  # type: ignore[misc]
    assert hash(diagnostics)
    assert diagnostics[:3] == ("snapshot-1", "manifest-1", _epoch())


def test_candidate_filter_is_the_only_externally_usable_filter() -> None:
    from epip.evidence import candidates

    assert not hasattr(candidates, "GovernanceFilter")
    assert not hasattr(candidates.CandidateEnumerator, "filter")
    assert not hasattr(candidates.CandidateEnumerator, "enumerate")
    assert not hasattr(candidates.CandidateFilter, "capabilities")
    assert callable(candidates.CandidateFilter.filter)


def test_filtering_preserves_every_immutable_input() -> None:
    entry = _entry()
    snapshot = _snapshot((entry,))
    requirement = _requirement()
    effects = (_effects(),)
    inputs = (snapshot, requirement, effects)
    hashes = tuple(hash(value) for value in inputs)
    first = CandidateFilter.filter(snapshot, requirement, effects, "semantic")
    second = CandidateFilter.filter(snapshot, requirement, effects, "semantic")
    assert first == second
    assert hashes == tuple(hash(value) for value in inputs)


def test_no_downstream_responsibility_is_present() -> None:
    forbidden = {
        "select",
        "tie_break",
        "resolve_ambiguity",
        "build_graph",
        "detect_cycle",
        "canonical_identity",
        "orchestrate",
        "execute",
        "track_execution",
        "verify_lineage",
        "replay",
    }
    methods = {
        name
        for owner in (CandidateEnumerator, CandidateFilter, CandidateDiagnostics)
        for name, value in getmembers(owner)
        if isfunction(value) or callable(value)
    }
    assert forbidden.isdisjoint(methods)
