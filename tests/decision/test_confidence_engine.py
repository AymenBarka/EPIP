"""Confidence assessment, propagation, registry, snapshot, and diagnostics tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core import confidence_engine
from epip.core.integrity import DataIntegrityError, RelationshipIntegrityError
from epip.decision.candidate import CandidateReferenceResolver, CandidateRegistry
from epip.decision.confidence import (
    ConfidenceAssessment,
    ConfidenceBuilder,
    ConfidenceCollection,
    ConfidenceDiagnostics,
    ConfidenceDigest,
    ConfidenceEngine,
    ConfidenceRegistry,
    ConfidenceSnapshot,
    ConfidenceStatistics,
    _confidence_level,
    _quality_level,
    _validity_level,
)
from epip.decision.domain import (
    Confidence,
    ConfidenceLevel,
    DecisionCandidate,
    Quality,
    QualityLevel,
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.models import DecisionScore
from tests.decision.test_candidate_engine import _candidate


def _registered() -> tuple[CandidateReferenceResolver, DecisionCandidate, CandidateRegistry]:
    resolver, candidate = _candidate()
    candidates = CandidateRegistry().register(candidate, resolver, ("candidate",))
    return resolver, candidate, candidates


def _assessment() -> ConfidenceAssessment:
    resolver, candidate, _ = _registered()
    return ConfidenceBuilder(resolver).build(candidate, graph_node_ids=("candidate",))


def test_assessment_creation_propagation_and_legacy_api() -> None:
    resolver, candidate, candidates = _registered()
    assessment = ConfidenceBuilder(resolver).build(candidate, graph_node_ids=("candidate",))
    assert assessment.confidence.value == pytest.approx(0.8)
    assert assessment.quality.value == pytest.approx(0.9)
    assert assessment.validity.value == 1.0
    assert assessment.uncertainty.value == pytest.approx(0.2)
    assert assessment.evidence_coverage == assessment.scenario_consistency == 1.0
    assert assessment.completeness == assessment.traceability == 1.0
    assert assessment.digest == ConfidenceDigest.of(assessment)
    assert hash(assessment)
    assert confidence_engine.ConfidenceEngine is ConfidenceEngine
    assert (
        confidence_engine.ConfidenceCalculator().calculate(DecisionScore(50, 0, 0, 0)).value == 0.5
    )
    with pytest.raises(FrozenInstanceError):
        assessment.assessment_id = "changed"  # type: ignore[misc]
    report = ConfidenceEngine(resolver, candidates).assess(
        (candidate.candidate_id,), graph_node_ids=("candidate",)
    )
    assert report.audit.assessments == 1
    assert report.audit.coverage == 1.0
    assert report.diagnostics.issues == ()
    assert _confidence_level(0.0) is ConfidenceLevel.VERY_LOW
    assert _confidence_level(1.0) is ConfidenceLevel.VERY_HIGH
    assert _quality_level(0.0) is QualityLevel.VERY_LOW
    assert _quality_level(1.0) is QualityLevel.VERY_HIGH
    assert _validity_level(0.0) is ValidityLevel.INVALID
    assert _validity_level(0.2) is ValidityLevel.UNKNOWN
    assert _validity_level(0.8) is ValidityLevel.CONDITIONAL
    assert _validity_level(1.0) is ValidityLevel.VALID


def test_builder_is_deterministic_independent_and_validates_references() -> None:
    resolver, candidate, candidates = _registered()
    first = ConfidenceEngine(resolver, candidates).assess(
        (candidate.candidate_id,), graph_node_ids=("candidate",)
    )
    second = ConfidenceEngine(resolver, candidates).assess(
        (candidate.candidate_id,), graph_node_ids=("candidate",)
    )
    assert first.snapshot.to_json() == second.snapshot.to_json()
    assert first.assessments.items[0].candidate.identifier == candidate.candidate_id
    assert (
        ConfidenceEngine(resolver, candidates).assess((), graph_node_ids=()).audit.assessments == 0
    )
    missing = ConfidenceEngine(resolver, candidates).assess(("missing",))
    assert missing.audit.validation_failures == 1
    invalid = ConfidenceEngine(resolver, candidates).assess(
        (candidate.candidate_id,), graph_node_ids=("missing",)
    )
    assert invalid.audit.validation_failures == 1
    duplicate = ConfidenceEngine(resolver, candidates, first.registry).assess(
        (candidate.candidate_id,), graph_node_ids=("candidate",)
    )
    assert duplicate.audit.duplicates == 1


def test_collection_registry_lookup_grouping_and_statistics() -> None:
    assessment = _assessment()
    second = ConfidenceAssessment.create(
        "confidence-second",
        assessment.candidate,
        Confidence(0.1, ConfidenceLevel.VERY_LOW),
        Quality(0.2, QualityLevel.LOW),
        Validity(0.6, ValidityLevel.CONDITIONAL),
        Uncertainty(0.8),
        0.5,
        0.5,
        0.8,
        0.5,
        (),
    )
    collection = ConfidenceCollection((second, assessment))
    assert len(collection) == 2
    assert tuple(collection) == collection.items
    assert collection.get(assessment.assessment_id) == assessment
    assert collection.get("missing") is None
    assert collection.by_candidate(assessment.candidate).items == collection.items
    assert collection.by_confidence_level(ConfidenceLevel.VERY_LOW).items == (second,)
    assert collection.by_quality_level(QualityLevel.LOW).items == (second,)
    assert collection.by_digest(second.digest).items == (second,)
    assert len(collection.group_by_confidence_level()) == 2
    registry = ConfidenceRegistry().register(second).register(assessment)
    assert registry.get(second.assessment_id) == second
    assert registry.by_candidate(second.candidate).items == collection.items
    assert registry.by_confidence_level(second.confidence.level).items == (second,)
    assert registry.by_quality_level(second.quality.level).items == (second,)
    assert registry.by_digest(second.digest).items == (second,)
    statistics = ConfidenceStatistics.from_registry(registry)
    assert statistics.total == 2
    assert statistics.mean_evidence_coverage == 0.75
    assert ConfidenceStatistics.from_registry(ConfidenceRegistry()).mean_evidence_coverage == 0.0
    with pytest.raises(RelationshipIntegrityError):
        registry.register(second)
    with pytest.raises(RelationshipIntegrityError):
        ConfidenceCollection([second])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        ConfidenceCollection((second, second))


def test_validation_digest_ranges_and_completeness() -> None:
    assessment = _assessment()
    for value, algorithm in (("0" * 63, "sha256"), ("Z" * 64, "sha256"), ("0" * 64, "sha1")):
        with pytest.raises(RelationshipIntegrityError):
            ConfidenceDigest(value, algorithm)
    with pytest.raises(RelationshipIntegrityError):
        ConfidenceDigest("g" * 64)
    with pytest.raises(RelationshipIntegrityError):
        replace(assessment, digest=ConfidenceDigest("0" * 64))
    with pytest.raises(RelationshipIntegrityError):
        replace(assessment, graph_node_ids=["candidate"])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        replace(assessment, graph_node_ids=("candidate", "candidate"))
    for field in ("evidence_coverage", "scenario_consistency", "completeness", "traceability"):
        with pytest.raises(DataIntegrityError):
            replace(assessment, **{field: 2.0})  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(assessment, assessment_id="")


def test_snapshot_serialization_replay_and_strict_input() -> None:
    assessment = _assessment()
    snapshot = ConfidenceSnapshot.capture(ConfidenceCollection((assessment,)))
    encoded = snapshot.to_json()
    restored = ConfidenceSnapshot.from_json(encoded)
    assert restored == snapshot
    assert restored.to_json() == encoded
    assert hash(restored)
    with pytest.raises(RelationshipIntegrityError):
        ConfidenceSnapshot(snapshot.collection, ConfidenceDigest("0" * 64))
    with pytest.raises(RelationshipIntegrityError):
        ConfidenceSnapshot(snapshot.collection, snapshot.digest, 0)
    invalid_values = (
        "not-json",
        "[]",
        json.dumps({}),
        json.dumps({"version": True, "digest": "0" * 64, "assessments": []}),
        json.dumps({"version": 1, "digest": 1, "assessments": []}),
        json.dumps({"version": 1, "digest": "0" * 64, "assessments": {}}),
    )
    for value in invalid_values:
        with pytest.raises(RelationshipIntegrityError):
            ConfidenceSnapshot.from_json(value)
    mutations: tuple[tuple[str, object], ...] = (
        ("candidate", []),
        ("confidence", []),
        ("quality", []),
        ("validity", []),
        ("uncertainty", []),
        ("graph_node_ids", {}),
        ("assessment_id", 1),
        ("evidence_coverage", True),
    )
    for key, malformed_value in mutations:
        malformed = json.loads(encoded)
        malformed["assessments"][0][key] = malformed_value
        with pytest.raises(RelationshipIntegrityError):
            ConfidenceSnapshot.from_json(json.dumps(malformed))
    malformed = json.loads(encoded)
    malformed["assessments"][0]["graph_node_ids"] = [1]
    with pytest.raises(RelationshipIntegrityError):
        ConfidenceSnapshot.from_json(json.dumps(malformed))


def test_diagnostics_detect_inconsistencies_without_correction() -> None:
    resolver, _, candidates = _registered()
    assessment = _assessment()
    registry = ConfidenceRegistry((assessment,))
    mismatch = ConfidenceSnapshot.capture(ConfidenceCollection())
    assert (
        "snapshot_registry_mismatch"
        in ConfidenceDiagnostics.inspect(registry, candidates, resolver, mismatch).issues
    )
    missing_candidates = CandidateRegistry()
    assert ConfidenceDiagnostics.inspect(registry, missing_candidates, resolver).issues == (
        f"missing_candidate:{assessment.assessment_id}",
    )
    invalid = replace(assessment)
    object.__setattr__(invalid, "graph_node_ids", ("missing",))
    object.__setattr__(invalid, "digest", ConfidenceDigest.of(invalid))
    assert (
        f"invalid_references:{assessment.assessment_id}"
        in ConfidenceDiagnostics.inspect(
            ConfidenceRegistry((invalid,)), candidates, resolver
        ).issues
    )
    broken = replace(assessment)
    object.__setattr__(broken, "digest", ConfidenceDigest("0" * 64))
    assert (
        f"digest_inconsistency:{assessment.assessment_id}"
        in ConfidenceDiagnostics.inspect(ConfidenceRegistry((broken,)), candidates, resolver).issues
    )
    invalid_metrics = replace(assessment)
    object.__setattr__(invalid_metrics, "evidence_coverage", 2.0)
    object.__setattr__(invalid_metrics, "completeness", True)
    object.__setattr__(invalid_metrics, "digest", ConfidenceDigest.of(invalid_metrics))
    metric_issues = ConfidenceDiagnostics.inspect(
        ConfidenceRegistry((invalid_metrics,)), candidates, resolver
    ).issues
    assert f"invalid_ranges:{assessment.assessment_id}" in metric_issues
    assert f"invalid_completeness:{assessment.assessment_id}" in metric_issues
    duplicate_registry = object.__new__(ConfidenceRegistry)
    object.__setattr__(duplicate_registry, "assessments", (assessment, assessment))
    assert (
        "duplicate_assessment_identifiers"
        in ConfidenceDiagnostics.inspect(duplicate_registry, candidates, resolver).issues
    )
    snapshot = ConfidenceSnapshot.capture(registry.collection())
    object.__setattr__(snapshot, "digest", ConfidenceDigest("0" * 64))
    assert (
        "snapshot_digest_mismatch"
        in ConfidenceDiagnostics.inspect(registry, candidates, resolver, snapshot).issues
    )
