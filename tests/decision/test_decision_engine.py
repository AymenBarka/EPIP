"""Final decision selection, lifecycle, explanation, and replay tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core import decision_engine
from epip.core.integrity import DataIntegrityError, RelationshipIntegrityError
from epip.decision.candidate import CandidateBuilder, CandidateReferenceResolver, CandidateRegistry
from epip.decision.confidence import ConfidenceBuilder, ConfidenceDigest, ConfidenceRegistry
from epip.decision.decision_engine import (
    DecisionCollection,
    DecisionConstraintEvaluator,
    DecisionDiagnostics,
    DecisionEngine,
    DecisionLifecycleState,
    DecisionRegistry,
    DecisionSelectionReport,
    DecisionSelector,
    DecisionSnapshot,
    DecisionStatistics,
    _content_digest,
    _DecisionEntry,
)
from epip.decision.domain import (
    CandidateReference,
    CandidateType,
    ConstraintEvaluation,
    ConstraintType,
    DecisionCandidate,
    DecisionContext,
    DecisionDigest,
    DecisionType,
)
from tests.decision.test_candidate_engine import _resolver


def _facts(*, rejected_second: bool = False) -> tuple[
    CandidateReferenceResolver,
    DecisionCandidate,
    DecisionCandidate,
    CandidateRegistry,
    ConfidenceRegistry,
]:
    resolver = _resolver()
    accepted = ConstraintEvaluation("policy-a", ConstraintType.POLICY, True, True, "allowed")
    second_constraint = ConstraintEvaluation(
        "policy-b", ConstraintType.POLICY, not rejected_second, True, "declared"
    )
    first = CandidateBuilder(resolver).build(
        "scenario-1",
        CandidateType.LONG,
        candidate_id="candidate-a",
        constraints=(accepted,),
        graph_node_ids=("candidate",),
    )
    second = CandidateBuilder(resolver).build(
        "scenario-1",
        CandidateType.WAIT,
        candidate_id="candidate-b",
        constraints=(second_constraint,),
        graph_node_ids=("candidate",),
    )
    candidates = (
        CandidateRegistry()
        .register(second, resolver, ("candidate",))
        .register(first, resolver, ("candidate",))
    )
    assessments = (
        ConfidenceRegistry()
        .register(ConfidenceBuilder(resolver).build(second, graph_node_ids=("candidate",)))
        .register(ConfidenceBuilder(resolver).build(first, graph_node_ids=("candidate",)))
    )
    return resolver, first, second, candidates, assessments


def _context() -> DecisionContext:
    return DecisionContext("EURUSD", "H1", "decision-run-1")


def _report(*, rejected_second: bool = False) -> DecisionSelectionReport:
    resolver, _, _, candidates, assessments = _facts(rejected_second=rejected_second)
    return DecisionEngine(resolver, candidates, assessments).decide(_context())


def test_selection_is_deterministic_explainable_and_immutable() -> None:
    first = _report()
    second = _report()
    assert first.snapshot.to_json() == second.snapshot.to_json()
    assert first.decision is not None and first.trace is not None
    assert first.decision.candidate.identifier == "candidate-a"
    assert first.decision.decision_type is DecisionType.ENTER
    assert first.decision.explanation.alternatives[0].candidate.identifier == "candidate-b"
    assert first.trace.selected_candidate == first.decision.candidate
    assert first.trace.confidence_assessment_id
    assert first.trace.evidence == first.decision.explanation.supporting_evidence
    assert first.audit.selected_decisions == 1
    assert first.audit.rejected_candidates == 1
    assert first.audit.constraint_applications == 1
    assert first.diagnostics.issues == ()
    assert decision_engine.DecisionEngine is DecisionEngine
    with pytest.raises(FrozenInstanceError):
        first.trace.confidence_assessment_id = "changed"  # type: ignore[misc]


def test_constraints_are_consumed_and_fail_closed() -> None:
    evaluator = DecisionConstraintEvaluator()
    accepted = ConstraintEvaluation("a", ConstraintType.SECURITY, True, True, "ok")
    optional = ConstraintEvaluation("b", ConstraintType.RUNTIME, False, False, "warning")
    rejected = ConstraintEvaluation("c", ConstraintType.COMPLIANCE, False, True, "blocked")
    assert evaluator.evaluate((accepted, optional))
    assert not evaluator.evaluate((rejected,))
    with pytest.raises(RelationshipIntegrityError):
        evaluator.evaluate(())
    with pytest.raises(RelationshipIntegrityError):
        evaluator.evaluate((accepted, accepted))
    report = _report(rejected_second=True)
    assert report.decision is not None
    assert report.decision.explanation.alternatives[0].reason == "mandatory_constraint_rejected"


def test_selector_rejects_missing_confidence_and_no_admissible_candidate() -> None:
    resolver, first, _, candidates, assessments = _facts()
    with pytest.raises(RelationshipIntegrityError):
        DecisionSelector().select(candidates, ConfidenceRegistry())
    duplicate_assessment = replace(assessments.assessments[0])
    object.__setattr__(duplicate_assessment, "assessment_id", "another-assessment")
    object.__setattr__(duplicate_assessment, "digest", ConfidenceDigest.of(duplicate_assessment))
    duplicate_assessments = ConfidenceRegistry(assessments.assessments + (duplicate_assessment,))
    with pytest.raises(RelationshipIntegrityError):
        DecisionSelector().select(candidates, duplicate_assessments)
    rejected = replace(
        first, constraints=(ConstraintEvaluation("x", ConstraintType.POLICY, False, True, "no"),)
    )
    object.__setattr__(rejected, "content_digest", DecisionDigest("0" * 64))
    from epip.decision.candidate import CandidateDigest

    object.__setattr__(
        rejected, "content_digest", DecisionDigest(CandidateDigest.of(rejected).value)
    )
    rejected_registry = CandidateRegistry().register(rejected, resolver, ("candidate",))
    matching = ConfidenceRegistry().register(
        ConfidenceBuilder(resolver).build(rejected, graph_node_ids=("candidate",))
    )
    with pytest.raises(RelationshipIntegrityError):
        DecisionSelector().select(rejected_registry, matching)
    failed = DecisionEngine(resolver, rejected_registry, matching).decide(_context())
    assert failed.decision is None and failed.audit.validation_failures == 1


def test_registry_collection_lifecycle_lookup_and_duplicates() -> None:
    report = _report()
    assert report.decision is not None and report.trace is not None
    registry = DecisionRegistry().register(report.decision, report.trace)
    identifier = report.decision.decision_id
    assert registry.entry(identifier).state is DecisionLifecycleState.AVAILABLE
    assert registry.get(identifier) == report.decision
    assert registry.get("missing") is None
    with pytest.raises(KeyError):
        registry.entry("missing")
    assert registry.by_type(report.decision.decision_type).items == (report.decision,)
    assert registry.by_candidate(report.decision.candidate).items == (report.decision,)
    assert registry.by_digest(report.decision.content_digest).items == (report.decision,)
    collection = registry.collection()
    assert len(collection) == 1 and tuple(collection) == (report.decision,)
    assert collection.get(identifier) == report.decision
    assert collection.get("missing") is None
    assert len(collection.group_by_type()) == 1
    statistics = DecisionStatistics.from_registry(registry)
    assert statistics.total == 1
    assert dict(statistics.by_state)[DecisionLifecycleState.AVAILABLE] == 1
    with pytest.raises(RelationshipIntegrityError):
        registry.register(report.decision, report.trace)
    with pytest.raises(RelationshipIntegrityError):
        registry.transition(identifier, DecisionLifecycleState.ARCHIVED)
    state = registry
    for target in (
        DecisionLifecycleState.SNAPSHOTTED,
        DecisionLifecycleState.ARCHIVED,
        DecisionLifecycleState.DISCARDED,
    ):
        state = state.transition(identifier, target)
    assert state.entry(identifier).state is DecisionLifecycleState.DISCARDED
    with pytest.raises(RelationshipIntegrityError):
        DecisionCollection([report.decision])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        DecisionCollection((report.decision, report.decision))
    with pytest.raises(RelationshipIntegrityError):
        DecisionRegistry((registry.entries[0], registry.entries[0]))


def test_snapshot_serialization_digest_and_strict_validation() -> None:
    snapshot = _report().snapshot
    encoded = snapshot.to_json()
    restored = DecisionSnapshot.from_json(encoded)
    assert restored == snapshot
    assert restored.to_json() == encoded
    assert hash(restored)
    with pytest.raises(RelationshipIntegrityError):
        DecisionSnapshot(snapshot.entries, DecisionDigest("0" * 64))
    with pytest.raises(RelationshipIntegrityError):
        DecisionSnapshot(snapshot.entries, snapshot.digest, 0)
    invalid = (
        "not-json",
        "[]",
        json.dumps({}),
        json.dumps({"version": True, "digest": "0" * 64, "entries": []}),
        json.dumps({"version": 1, "digest": 1, "entries": []}),
        json.dumps({"version": 1, "digest": "0" * 64, "entries": {}}),
    )
    for value in invalid:
        with pytest.raises(RelationshipIntegrityError):
            DecisionSnapshot.from_json(value)
    mutations: tuple[tuple[str, object], ...] = (
        ("decision", []),
        ("trace", []),
        ("state", 1),
    )
    for key, malformed_value in mutations:
        malformed = json.loads(encoded)
        malformed["entries"][0][key] = malformed_value
        with pytest.raises(RelationshipIntegrityError):
            DecisionSnapshot.from_json(json.dumps(malformed))
    nested_mutations: tuple[tuple[tuple[str, ...], object], ...] = (
        (("decision", "explanation", "constraints"), {}),
        (("decision", "metadata", "version"), True),
        (("decision", "explanation", "uncertainty", "value"), True),
        (("decision", "explanation", "constraints", "0", "accepted"), "yes"),
    )
    for path, malformed_value in nested_mutations:
        malformed = json.loads(encoded)
        target = malformed["entries"][0]
        for part in path[:-1]:
            target = target[int(part)] if part.isdigit() else target[part]
        target[path[-1]] = malformed_value
        with pytest.raises(RelationshipIntegrityError):
            DecisionSnapshot.from_json(json.dumps(malformed))
    assert snapshot.entries[0].decision.content_digest == _content_digest(
        snapshot.entries[0].decision
    )
    with pytest.raises(RelationshipIntegrityError):
        _content_digest(object())


def test_duplicate_selection_audit_and_diagnostics() -> None:
    initial = _report()
    assert initial.decision is not None
    resolver, _, _, candidates, assessments = _facts()
    duplicate = DecisionEngine(resolver, candidates, assessments, initial.registry).decide(
        _context()
    )
    assert duplicate.decision is None and duplicate.audit.duplicates == 1
    registry = initial.registry
    mismatch = DecisionSnapshot.capture(DecisionRegistry())
    assert "snapshot_registry_mismatch" in DecisionDiagnostics.inspect(registry, mismatch).issues
    entry = registry.entries[0]
    broken_decision = replace(entry.decision, content_digest=DecisionDigest("0" * 64))
    wrong_trace = replace(entry.trace, selected_candidate=CandidateReference("wrong", 1))
    broken = DecisionRegistry((_DecisionEntry(broken_decision, wrong_trace, entry.state),))
    issues = DecisionDiagnostics.inspect(broken).issues
    assert f"digest_inconsistency:{entry.decision.decision_id}" in issues
    assert f"invalid_references:{entry.decision.decision_id}" in issues
    no_constraints = replace(
        entry.decision,
        explanation=replace(entry.decision.explanation, constraints=()),
    )
    object.__setattr__(no_constraints, "content_digest", _content_digest(no_constraints))
    missing = replace(entry.trace)
    object.__setattr__(missing, "confidence_assessment_id", "")
    raw = DecisionRegistry((_DecisionEntry(no_constraints, missing, entry.state),))
    raw_issues = DecisionDiagnostics.inspect(raw).issues
    assert f"missing_constraints:{entry.decision.decision_id}" in raw_issues
    assert f"missing_confidence:{entry.decision.decision_id}" in raw_issues
    malformed_entry = object.__new__(_DecisionEntry)
    object.__setattr__(malformed_entry, "decision", entry.decision)
    object.__setattr__(malformed_entry, "trace", entry.trace)
    object.__setattr__(malformed_entry, "state", "bad")
    malformed_registry = DecisionRegistry((malformed_entry,))
    assert (
        f"invalid_lifecycle:{entry.decision.decision_id}"
        in DecisionDiagnostics.inspect(malformed_registry).issues
    )
    duplicate_registry = object.__new__(DecisionRegistry)
    object.__setattr__(duplicate_registry, "entries", (entry, entry))
    assert (
        "duplicate_decision_identifiers" in DecisionDiagnostics.inspect(duplicate_registry).issues
    )
    bad_snapshot = DecisionSnapshot.capture(registry)
    object.__setattr__(bad_snapshot, "digest", DecisionDigest("0" * 64))
    assert "snapshot_digest_mismatch" in DecisionDiagnostics.inspect(registry, bad_snapshot).issues


def test_trace_validation() -> None:
    trace = _report().trace
    assert trace is not None and trace.to_payload()
    with pytest.raises(DataIntegrityError):
        replace(trace, confidence_assessment_id="")
    with pytest.raises(RelationshipIntegrityError):
        replace(trace, rejected_candidates=[])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        replace(trace, graph_node_ids=("candidate", "candidate"))
