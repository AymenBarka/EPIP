"""Candidate generation, lifecycle, registry, and replay tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core import candidate_engine
from epip.core.integrity import RelationshipIntegrityError
from epip.decision.candidate import (
    CandidateCollection,
    CandidateDiagnostics,
    CandidateDigest,
    CandidateEngine,
    CandidateLifecycleState,
    CandidateReferenceResolver,
    CandidateRegistry,
    CandidateSnapshot,
    CandidateStatistics,
    _CandidateEntry,
)
from epip.decision.domain import (
    CandidateType,
    Confidence,
    ConfidenceLevel,
    DecisionCandidate,
    DecisionDigest,
    DecisionMetadata,
    Evidence,
    EvidenceCategory,
    EvidenceReference,
    Hypothesis,
    HypothesisCategory,
    HypothesisReference,
    Quality,
    QualityLevel,
    Scenario,
    ScenarioCategory,
    ScenarioReference,
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.evidence import EvidenceBuilder, EvidenceRegistry
from epip.decision.graph import (
    DecisionDependency,
    DecisionGraphBuilder,
    DecisionGraphNode,
    DecisionNodeType,
)
from epip.decision.inference import (
    HypothesisBuilder,
    HypothesisRegistry,
    InferenceLifecycleState,
    ScenarioBuilder,
    ScenarioRegistry,
)


def _scores() -> tuple[Confidence, Quality, Validity, Uncertainty]:
    return (
        Confidence(0.8, ConfidenceLevel.HIGH),
        Quality(0.9, QualityLevel.VERY_HIGH),
        Validity(1.0, ValidityLevel.VALID),
        Uncertainty(0.2),
    )


def _evidence() -> Evidence:
    confidence, quality, validity, uncertainty = _scores()
    return EvidenceBuilder().build(
        evidence_id="evidence-1",
        category=EvidenceCategory.MARKET_DATA,
        source="feed-a",
        source_version=1,
        payload=(("price", "1.10000"),),
        confidence=confidence,
        quality=quality,
        validity=validity,
        uncertainty=uncertainty,
        dependencies=(),
        metadata=DecisionMetadata(1, "42", "programme-b"),
    )


def _hypothesis() -> Hypothesis:
    confidence, quality, validity, uncertainty = _scores()
    reference = EvidenceReference("evidence-1", 1)
    return HypothesisBuilder().build(
        hypothesis_id="hypothesis-1",
        category=HypothesisCategory.DIRECTIONAL,
        evidence=(reference,),
        supporting_evidence=(reference,),
        contradicting_evidence=(),
        assumptions=("feed is valid",),
        invalidation_conditions=("feed is withdrawn",),
        confidence=confidence,
        quality=quality,
        validity=validity,
        uncertainty=uncertainty,
        metadata=DecisionMetadata(1, "43", "programme-c"),
    )


def _scenario() -> Scenario:
    confidence, quality, validity, uncertainty = _scores()
    return ScenarioBuilder().build(
        scenario_id="scenario-1",
        category=ScenarioCategory.BULLISH,
        hypotheses=(HypothesisReference("hypothesis-1", 1),),
        parent_scenarios=(),
        supporting_evidence=(EvidenceReference("evidence-1", 1),),
        contradicting_evidence=(),
        assumptions=("hypothesis remains valid",),
        invalidation_conditions=("hypothesis is discarded",),
        confidence=confidence,
        quality=quality,
        validity=validity,
        uncertainty=uncertainty,
        metadata=DecisionMetadata(1, "44", "programme-c"),
    )


def _resolver() -> CandidateReferenceResolver:
    evidence = EvidenceRegistry().register(_evidence())
    hypotheses = HypothesisRegistry().register(_hypothesis(), evidence)
    scenarios = ScenarioRegistry().register(_scenario(), hypotheses, evidence)
    graph = (
        DecisionGraphBuilder()
        .add_node(DecisionGraphNode("scenario", DecisionNodeType.SCENARIO))
        .add_node(
            DecisionGraphNode(
                "candidate",
                DecisionNodeType.CANDIDATE,
                (DecisionDependency("scenario"),),
            )
        )
        .connect("scenario", "candidate")
        .build()
    )
    return CandidateReferenceResolver(evidence, hypotheses, scenarios, graph)


def _candidate(
    candidate_type: CandidateType = CandidateType.LONG,
) -> tuple[CandidateReferenceResolver, DecisionCandidate]:
    resolver = _resolver()
    report = CandidateEngine(resolver).generate(
        "scenario-1", (candidate_type,), graph_node_ids=("candidate",)
    )
    return resolver, report.candidates.items[0]


def test_public_surface_digest_and_immutability() -> None:
    resolver, candidate = _candidate()
    assert candidate_engine.CandidateEngine is CandidateEngine
    assert CandidateDigest.of(candidate).value == candidate.content_digest.value
    assert hash(CandidateDigest.of(candidate))
    with pytest.raises(FrozenInstanceError):
        candidate.candidate_id = "changed"  # type: ignore[misc]
    for value, algorithm in (("0" * 63, "sha256"), ("Z" * 64, "sha256"), ("0" * 64, "sha1")):
        with pytest.raises(RelationshipIntegrityError):
            CandidateDigest(value, algorithm)
    with pytest.raises(RelationshipIntegrityError):
        CandidateDigest("g" * 64)
    assert resolver.scenarios.get("scenario-1") is not None


def test_generation_is_deterministic_structural_and_non_ranking() -> None:
    resolver = _resolver()
    types = (CandidateType.WAIT, CandidateType.LONG, CandidateType.SHORT)
    first = CandidateEngine(resolver).generate(
        "scenario-1", types, graph_node_ids=("candidate", "scenario")
    )
    second = CandidateEngine(resolver).generate(
        "scenario-1", tuple(reversed(types)), graph_node_ids=("scenario", "candidate")
    )
    assert first.snapshot.to_json() == second.snapshot.to_json()
    assert tuple(item.candidate_type for item in first.candidates) == (
        CandidateType.LONG,
        CandidateType.SHORT,
        CandidateType.WAIT,
    )
    assert all(item.priority.value == "normal" for item in first.candidates)
    assert first.audit.generated == first.audit.registered == 3
    assert first.audit.duplicates == first.audit.validation_failures == 0
    assert first.diagnostics.issues == ()


def test_collection_indexes_grouping_and_validation() -> None:
    resolver, long_candidate = _candidate(CandidateType.LONG)
    _, wait_candidate = _candidate(CandidateType.WAIT)
    collection = CandidateCollection(
        (wait_candidate, long_candidate),
        (
            (wait_candidate.candidate_id, ("scenario",)),
            (long_candidate.candidate_id, ("candidate",)),
        ),
    )
    assert len(collection) == 2
    assert tuple(collection) == tuple(sorted(collection.items, key=lambda item: item.candidate_id))
    assert collection.get(long_candidate.candidate_id) == long_candidate
    assert collection.get("missing") is None
    assert collection.by_type(CandidateType.WAIT).items == (wait_candidate,)
    assert len(collection.by_scenario(ScenarioReference("scenario-1", 1))) == 2
    assert len(collection.by_evidence(EvidenceReference("evidence-1", 1))) == 2
    assert collection.by_graph_node("candidate").items == (long_candidate,)
    assert collection.by_digest(CandidateDigest.of(long_candidate)).items == (long_candidate,)
    assert len(collection.group_by_type()) == 2
    assert collection.to_payload()["candidates"]
    with pytest.raises(RelationshipIntegrityError):
        CandidateCollection([long_candidate])  # type: ignore[arg-type]
    for links in (
        ((long_candidate.candidate_id, ()), (long_candidate.candidate_id, ())),
        (("missing", ()),),
        ((long_candidate.candidate_id, ("candidate", "candidate")),),
    ):
        with pytest.raises(RelationshipIntegrityError):
            CandidateCollection((long_candidate,), links)
    with pytest.raises(RelationshipIntegrityError):
        CandidateCollection((long_candidate, long_candidate))
    resolver.validate(long_candidate, ("candidate",))


def test_registry_lifecycle_indexes_statistics_and_duplicates() -> None:
    resolver, candidate = _candidate()
    registry = CandidateRegistry().register(candidate, resolver, ("scenario", "candidate"))
    assert registry.entry(candidate.candidate_id).state is CandidateLifecycleState.AVAILABLE
    assert registry.get(candidate.candidate_id) == candidate
    assert registry.get("missing") is None
    with pytest.raises(KeyError):
        registry.entry("missing")
    assert registry.by_type(CandidateType.LONG).items == (candidate,)
    assert registry.by_scenario(candidate.scenarios[0]).items == (candidate,)
    assert registry.by_evidence(candidate.evidence[0]).items == (candidate,)
    assert registry.by_graph_node("candidate").items == (candidate,)
    assert registry.by_digest(CandidateDigest.of(candidate)).items == (candidate,)
    statistics = CandidateStatistics.from_registry(registry)
    assert statistics.total == 1
    assert dict(statistics.by_state)[CandidateLifecycleState.AVAILABLE] == 1
    with pytest.raises(RelationshipIntegrityError):
        registry.register(candidate, resolver)
    with pytest.raises(RelationshipIntegrityError):
        registry.transition(candidate.candidate_id, CandidateLifecycleState.ARCHIVED)
    state = registry
    for target in (
        CandidateLifecycleState.SNAPSHOTTED,
        CandidateLifecycleState.ARCHIVED,
        CandidateLifecycleState.DISCARDED,
    ):
        state = state.transition(candidate.candidate_id, target)
    assert state.entry(candidate.candidate_id).state is CandidateLifecycleState.DISCARDED
    with pytest.raises(RelationshipIntegrityError):
        CandidateRegistry((_CandidateEntry(candidate, CandidateLifecycleState.CREATED, ()),) * 2)


def test_resolver_rejects_invalid_references_state_digest_and_graph() -> None:
    resolver, candidate = _candidate()
    mutations = (
        replace(candidate, scenarios=()),
        replace(candidate, evidence=candidate.evidence * 2),
        replace(candidate, hypotheses=candidate.hypotheses * 2),
        replace(candidate, scenarios=candidate.scenarios * 2),
        replace(candidate, evidence=(EvidenceReference("missing", 1),)),
        replace(candidate, hypotheses=(HypothesisReference("missing", 1),)),
        replace(candidate, scenarios=(ScenarioReference("missing", 1),)),
        replace(candidate, content_digest=DecisionDigest("0" * 64)),
    )
    for invalid in mutations:
        with pytest.raises(RelationshipIntegrityError):
            resolver.validate(invalid)
    with pytest.raises(RelationshipIntegrityError):
        resolver.validate(candidate, ("candidate", "candidate"))
    with pytest.raises(RelationshipIntegrityError):
        resolver.validate(candidate, ("missing",))
    created_scenarios = replace(
        resolver.scenarios,
        entries=(replace(resolver.scenarios.entries[0], state=InferenceLifecycleState.CREATED),),
    )
    invalid_resolver = replace(resolver, scenarios=created_scenarios)
    with pytest.raises(RelationshipIntegrityError):
        invalid_resolver.validate(candidate)
    report = CandidateEngine(invalid_resolver).generate("scenario-1", (CandidateType.LONG,))
    assert report.audit.validation_failures == 1
    assert not report.candidates.items
    missing_report = CandidateEngine(resolver).generate("missing", (CandidateType.LONG,))
    assert missing_report.audit.validation_failures == 1


def test_snapshot_round_trip_is_byte_identical_and_strict() -> None:
    report = CandidateEngine(_resolver()).generate(
        "scenario-1", (CandidateType.LONG,), graph_node_ids=("candidate",)
    )
    encoded = report.snapshot.to_json()
    restored = CandidateSnapshot.from_json(encoded)
    assert restored == report.snapshot
    assert restored.to_json() == encoded
    assert hash(restored)
    for invalid in (
        "not-json",
        "[]",
        json.dumps({"version": True, "digest": "0" * 64, "candidates": [], "graph_links": []}),
        json.dumps({"version": 1, "digest": "0" * 64, "candidates": {}, "graph_links": []}),
        json.dumps({"version": 1, "digest": "0" * 64, "candidates": [], "graph_links": [["x"]]}),
    ):
        with pytest.raises(RelationshipIntegrityError):
            CandidateSnapshot.from_json(invalid)
    with pytest.raises(RelationshipIntegrityError):
        CandidateSnapshot(report.candidates, CandidateDigest("0" * 64))
    with pytest.raises(RelationshipIntegrityError):
        CandidateSnapshot(report.candidates, report.snapshot.digest, 0)

    payload = json.loads(encoded)
    malformed_values: tuple[tuple[str, object], ...] = (
        ("version", "1"),
        ("digest", 1),
        ("candidates", None),
        ("graph_links", None),
    )
    for key, value in malformed_values:
        malformed = dict(payload)
        malformed[key] = value
        with pytest.raises(RelationshipIntegrityError):
            CandidateSnapshot.from_json(json.dumps(malformed))

    malformed_candidate_values: tuple[tuple[str, object], ...] = (
        ("candidate_id", 1),
        ("confidence", []),
        ("constraints", {}),
        ("arguments", [1]),
        ("confidence", {"value": "high", "level": "high"}),
        ("uncertainty", {"value": True}),
    )
    for key, value in malformed_candidate_values:
        malformed = json.loads(encoded)
        malformed["candidates"][0][key] = value
        with pytest.raises(RelationshipIntegrityError):
            CandidateSnapshot.from_json(json.dumps(malformed))

    malformed = json.loads(encoded)
    malformed["candidates"][0]["constraints"] = [None]
    with pytest.raises(RelationshipIntegrityError):
        CandidateSnapshot.from_json(json.dumps(malformed))
    for accepted, mandatory in (("yes", True), (True, "yes"), (True, True)):
        malformed = json.loads(encoded)
        malformed["candidates"][0]["constraints"] = [
            {
                "constraint_id": "constraint-1",
                "constraint_type": "risk",
                "accepted": accepted,
                "mandatory": mandatory,
                "reason": "test",
            }
        ]
        with pytest.raises(RelationshipIntegrityError):
            CandidateSnapshot.from_json(json.dumps(malformed))


def test_diagnostics_and_duplicate_generation_are_observable() -> None:
    resolver, candidate = _candidate()
    registry = CandidateRegistry().register(candidate, resolver, ("candidate",))
    engine = CandidateEngine(resolver, registry)
    report = engine.generate(
        "scenario-1",
        (CandidateType.LONG, CandidateType.WAIT),
        graph_node_ids=("candidate",),
    )
    assert report.audit.generated == 2
    assert report.audit.duplicates == 1
    assert report.audit.registered == 1
    assert report.audit.statistics.total == 2
    mismatched = CandidateSnapshot.capture(CandidateCollection())
    assert (
        "snapshot_registry_mismatch"
        in CandidateDiagnostics.inspect(registry, resolver, mismatched).issues
    )
    invalid = replace(candidate, content_digest=DecisionDigest("0" * 64))
    raw = CandidateRegistry((_CandidateEntry(invalid, CandidateLifecycleState.AVAILABLE, ()),))
    assert CandidateDiagnostics.inspect(raw, resolver).issues == (
        f"invalid_references:{candidate.candidate_id}",
    )

    malformed_entry = object.__new__(_CandidateEntry)
    object.__setattr__(
        malformed_entry,
        "candidate",
        replace(candidate, candidate_type="bad"),  # type: ignore[arg-type]
    )
    object.__setattr__(malformed_entry, "state", "bad")
    object.__setattr__(malformed_entry, "graph_node_ids", ())
    malformed_registry = CandidateRegistry((malformed_entry,))
    issues = CandidateDiagnostics.inspect(malformed_registry, resolver).issues
    assert f"invalid_type:{candidate.candidate_id}" in issues
    assert f"invalid_lifecycle:{candidate.candidate_id}" in issues

    duplicate_registry = object.__new__(CandidateRegistry)
    duplicate_entry = _CandidateEntry(candidate, CandidateLifecycleState.AVAILABLE, ("candidate",))
    object.__setattr__(duplicate_registry, "entries", (duplicate_entry, duplicate_entry))
    assert (
        "duplicate_candidate_identifiers"
        in CandidateDiagnostics.inspect(duplicate_registry, resolver).issues
    )

    bad_snapshot = CandidateSnapshot.capture(registry.collection())
    object.__setattr__(bad_snapshot, "digest", CandidateDigest("0" * 64))
    assert (
        "snapshot_digest_mismatch"
        in CandidateDiagnostics.inspect(registry, resolver, bad_snapshot).issues
    )
