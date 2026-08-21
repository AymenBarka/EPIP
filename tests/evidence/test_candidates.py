"""Component tests for A04-E02 candidate enumeration and governance filtering."""

from __future__ import annotations

from inspect import getmembers, isfunction
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.evidence.candidates import (
    CandidateDiagnostics,
    CandidateEnumerator,
    CandidateFilter,
)
from epip.evidence.model import (
    AssumptionMetadata,
    CompatibilityEffects,
    CompletenessMetadata,
    DependencyType,
    DispositionAxis,
    EvidenceClaim,
    EvidenceRequirement,
    ProvenanceReference,
    QualityMetadata,
    SemanticBoundary,
    SemanticIdentity,
    SemanticState,
    ValidityMetadata,
)
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


def _snapshot(entries: tuple[RegistryEntry, ...] | None = None) -> RegistrySnapshot:
    return RegistrySnapshot(
        "snapshot-1",
        "manifest-1",
        _epoch(),
        entries if entries is not None else (_entry(),),
        ("action-1",),
        (("admission", "1.0.0"),),
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


def _claim(entry: RegistryEntry, **changes: object) -> EvidenceClaim:
    values: dict[str, object] = {
        "evidence_id": f"{entry.producer_identity}@{entry.producer_version}",
        "identity": SemanticIdentity("market.structure", "1.0.0", "EURUSD", "H1"),
        "source_identity": entry.producer_identity,
        "implementation_version": entry.producer_version,
        "boundary": SemanticBoundary("EURUSD", "H1", "closed", "window-1"),
        "claim": "bullish",
        "value_domain": "structure-state",
        "units": None,
        "validity": ValidityMetadata("closed", True, "boundary-1"),
        "completeness": CompletenessMetadata(
            SemanticState("PRESENT"), ("structure",), 1, ("H1",), ("trend",), True
        ),
        "quality": QualityMetadata("quality", "1.0.0", "accepted"),
        "assumptions": AssumptionMetadata("1.0.0", ("closed",)),
        "provenance": (ProvenanceReference("feed-1", "feed", "1.0.0"),),
        "content_identity": f"content-{entry.producer_identity}",
        "disposition": DispositionAxis.ACCEPTED,
    }
    values.update(changes)
    return EvidenceClaim(**values)  # type: ignore[arg-type]


def _effects(entry: RegistryEntry, **changes: object) -> CompatibilityEffects:
    values: dict[str, object] = {
        "decision_reference": f"decision-{entry.producer_identity}",
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


def _filter(snapshot: RegistrySnapshot) -> CandidateDiagnostics:
    claims = tuple(_claim(entry) for entry in snapshot.entries)
    effects = tuple(_effects(entry) for entry in snapshot.entries)
    return CandidateFilter.filter(
        snapshot,
        _requirement(),
        _claim(_entry("target")),
        claims,
        effects,
        "semantic",
    )


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
    assert CandidateEnumerator.enumerate(snapshot) == (first, second)
    assert CandidateEnumerator.evidence_definitions(snapshot) == (
        ("market.structure", "1.0.0"),
        ("market.trend", "2.0.0"),
    )


def test_candidate_filter_uses_exact_capability_and_stable_order() -> None:
    first = _entry("producer-a")
    second = _entry("producer-b", capability_references=(("market.trend", "1.0.0"),))
    assert CandidateFilter.capabilities((second, first), "market.structure", "1.0.0") == (first,)


def test_governance_filter_accepts_eligible_entry() -> None:
    snapshot = _snapshot()
    result = _filter(snapshot)
    assert result.candidates == snapshot.entries
    assert result.rejections == ()


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"lifecycle_standing": "Declared"}, "E02_NOT_ADMITTED"),
        ({"lifecycle_standing": "Registered"}, "E02_NOT_ENABLED"),
        ({"lifecycle_standing": "Certified"}, "E02_NOT_ENABLED"),
        ({"lifecycle_standing": "Disabled"}, "E02_DISABLED_PROVIDER"),
        ({"lifecycle_standing": "Deprecated"}, "E02_EXPIRED_PROVIDER"),
        ({"lifecycle_standing": "Retired"}, "E02_EXPIRED_PROVIDER"),
        ({"trust_standing": "Untrusted"}, "E02_UNTRUSTED_PROVIDER"),
        ({"trust_standing": "Revoked"}, "E02_REVOKED_PROVIDER"),
        ({"certification_records": ()}, "E02_UNCERTIFIED_PROVIDER"),
    ],
)
def test_admission_enablement_lifecycle_trust_and_certification_rejections(
    changes: dict[str, object], reason: str
) -> None:
    snapshot = _snapshot((cast(Any, _entry)(**changes),))
    result = _filter(snapshot)
    assert result.candidates == ()
    assert tuple(rejection.reason_code for rejection in result.rejections) == (reason,)
    assert result.rejections[0].affected_references == ("producer-a",)


@pytest.mark.parametrize(
    "verdict,reason", [("revoked", "E02_REVOKED_PROVIDER"), ("expired", "E02_EXPIRED_PROVIDER")]
)
def test_revoked_and_expired_certifications_are_rejected(verdict: str, reason: str) -> None:
    entry = _entry(certification_records=(_certification(verdict=verdict),))
    result = _filter(_snapshot((entry,)))
    assert result.rejections[0].reason_code == reason


def test_future_or_mismatched_certification_is_rejected() -> None:
    for certification in (
        _certification(producer_identity="other"),
        _certification(producer_version="2.0.0"),
        _certification(capability_references=(("other", "1.0.0"),)),
        _certification(effective_epoch=_epoch(3)),
        _certification(verdict="suspended"),
    ):
        entry = _entry(certification_records=(certification,))
        assert _filter(_snapshot((entry,))).rejections[0].reason_code == "E02_UNCERTIFIED_PROVIDER"


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
    assert _filter(_snapshot((entry,))).rejections[0].reason_code == "E02_UNCERTIFIED_PROVIDER"


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
        {"review_or_expiry_condition": "uncertified-expiry-condition"},
        {"revocation_reference": "revoked-by"},
        {"supersession_reference": "superseded-by"},
        {"effective_epoch": _epoch(3)},
    ],
)
def test_incompatible_decisions_are_rejected(changes: dict[str, object]) -> None:
    entry = _entry(compatibility_decisions=(cast(Any, _compatibility)(**changes),))
    result = _filter(_snapshot((entry,)))
    assert result.rejections[0].reason_code == "E02_INCOMPATIBLE_PROVIDER"


def test_compatibility_is_computed_by_e01_from_immutable_semantic_facts() -> None:
    entry = _entry()
    snapshot = _snapshot((entry,))
    result = CandidateFilter.filter(
        snapshot,
        _requirement(),
        _claim(_entry("target"), boundary=SemanticBoundary("EURUSD", "H1", "closed", "other")),
        (_claim(entry),),
        (_effects(entry),),
        "semantic",
    )
    assert result.candidates == ()
    assert result.rejections[0].reason_code == "E02_INCOMPATIBLE_PROVIDER"


def test_missing_or_ambiguous_authoritative_facts_fail_closed() -> None:
    entry = _entry()
    snapshot = _snapshot((entry,))
    target = _claim(_entry("target"))
    for sources, effects in (
        ((), (_effects(entry),)),
        ((_claim(entry), _claim(entry)), (_effects(entry),)),
        ((_claim(entry),), ()),
        ((_claim(entry),), (_effects(entry), _effects(entry))),
    ):
        result = CandidateFilter.filter(
            snapshot, _requirement(), target, sources, effects, "semantic"
        )
        assert result.rejections[0].reason_code == "E02_INCOMPATIBLE_PROVIDER"


def test_missing_compatibility_is_rejected_and_diagnostics_are_preserved() -> None:
    entry = _entry(compatibility_decisions=())
    result = _filter(_snapshot((entry,)))
    assert result.candidates == ()
    assert result.rejections == (result.rejections[0],)
    assert result.rejections[0].diagnostic_details == (("producer_version", "1.0.0"),)


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
        lambda: CandidateEnumerator.enumerate(cast(Any, object())),
        lambda: CandidateFilter.capabilities(cast(Any, []), "type", "1.0.0"),
        lambda: CandidateFilter.capabilities((_entry(),), "", "1.0.0"),
        lambda: CandidateFilter.capabilities((_entry(),), "type", ""),
        lambda: CandidateFilter.filter(
            _snapshot(), cast(Any, object()), _claim(_entry("target")), (), (), "semantic"
        ),
        lambda: CandidateFilter.filter(
            _snapshot(), _requirement(), cast(Any, object()), (), (), "semantic"
        ),
        lambda: CandidateFilter.filter(
            _snapshot(), _requirement(), _claim(_entry("target")), cast(Any, []), (), "semantic"
        ),
        lambda: CandidateFilter.filter(
            _snapshot(), _requirement(), _claim(_entry("target")), (), cast(Any, []), "semantic"
        ),
        lambda: CandidateFilter.filter(
            _snapshot(), _requirement(), _claim(_entry("target")), (), (), ""
        ),
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
        CandidateEnumerator.enumerate(_snapshot((entry, entry)))


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
    assert callable(candidates.CandidateFilter.filter)


def test_filtering_preserves_every_immutable_input() -> None:
    entry = _entry()
    snapshot = _snapshot((entry,))
    requirement = _requirement()
    target = _claim(_entry("target"))
    sources = (_claim(entry),)
    effects = (_effects(entry),)
    inputs = (snapshot, requirement, target, sources, effects)
    hashes = tuple(hash(value) for value in inputs)
    first = CandidateFilter.filter(snapshot, requirement, target, sources, effects, "semantic")
    second = CandidateFilter.filter(snapshot, requirement, target, sources, effects, "semantic")
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
