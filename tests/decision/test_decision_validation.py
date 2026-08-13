"""Real-framework institutional validation and certification tests."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from epip.core.integrity import RelationshipIntegrityError
from epip.decision.candidate import CandidateRegistry
from epip.decision.confidence import ConfidenceRegistry
from epip.decision.decision_engine import DecisionEngine
from epip.decision.domain import DecisionContext, EvidenceReference
from epip.decision.evidence import EvidenceRegistry
from epip.decision.graph import DecisionGraphBuilder, DecisionGraphNode, DecisionNodeType
from epip.decision.inference import HypothesisRegistry, ScenarioRegistry
from epip.decision.validation import (
    DecisionBenchmarkReport,
    DecisionCertificationReport,
    DecisionFrameworkHarness,
    DecisionFrameworkRun,
    DecisionStressReport,
    DecisionValidationDiagnostics,
    DecisionValidationDigest,
    DecisionValidationManager,
    DecisionValidationSnapshot,
    DecisionValidationStatistics,
)


def test_real_pipeline_replay_certifies_every_a_g_artifact() -> None:
    harness = DecisionFrameworkHarness()
    first = harness.run()
    replay = harness.run()
    assert first.to_json() == replay.to_json()
    assert first.digest == replay.digest
    assert first.decision_report.decision == replay.decision_report.decision
    assert first.decision_report.trace == replay.decision_report.trace
    assert first.decision_report.snapshot == replay.decision_report.snapshot
    assert first.evidence == replay.evidence
    assert first.hypothesis == replay.hypothesis
    assert first.scenario == replay.scenario
    report = DecisionValidationManager().validate_framework(harness)
    assert report.certified and report.statistics.passed == report.statistics.checks
    assert DecisionCertificationReport.from_validation(report).certified
    with pytest.raises(AttributeError):
        first.candidate_id = "changed"  # type: ignore[misc]


def test_real_registries_graph_explanation_and_trace_are_consistent() -> None:
    harness = DecisionFrameworkHarness()
    resolver = harness.resolver()
    assert isinstance(resolver.evidence, EvidenceRegistry)
    assert isinstance(resolver.hypotheses, HypothesisRegistry)
    assert isinstance(resolver.scenarios, ScenarioRegistry)
    assert resolver.graph.nodes
    run = harness.run()
    decision = run.decision_report.decision
    trace = run.decision_report.trace
    assert decision is not None and trace is not None
    assert trace.evidence == decision.explanation.supporting_evidence
    assert trace.hypotheses == decision.explanation.accepted_hypotheses
    assert trace.scenarios == decision.explanation.scenarios
    assert trace.graph_node_ids == ("candidate",)
    assert decision.explanation.constraints
    assert run.decision_report.diagnostics.issues == ()


def test_real_stress_and_benchmark_operations_execute_framework() -> None:
    manager = DecisionValidationManager()
    harness = DecisionFrameworkHarness()
    campaigns = manager.framework_campaigns(2, 1, harness)
    assert set(campaigns) == {
        "evidence_registration",
        "hypothesis_generation",
        "scenario_generation",
        "graph_construction",
        "graph_traversal",
        "candidate_generation",
        "confidence_assessment",
        "decision_selection",
        "complete_decision_pipeline",
    }
    stress = manager.stress(campaigns)
    assert not stress.failures
    assert dict(stress.operations)["evidence_registration"] == 2
    assert dict(stress.operations)["complete_decision_pipeline"] == 1
    benchmarks = manager.framework_benchmarks(1, harness)
    assert not benchmarks.anomalies
    assert {name for name, _, _ in benchmarks.measurements} >= {
        "evidence_registration",
        "hypothesis_generation",
        "scenario_generation",
        "graph_construction",
        "graph_traversal",
        "candidate_generation",
        "confidence_assessment",
        "decision_selection",
        "explainability_generation",
        "snapshot_generation",
        "audit_creation",
    }


def test_fault_injection_uses_real_framework_boundaries() -> None:
    harness = DecisionFrameworkHarness()
    evidence = EvidenceRegistry().register(harness.build_evidence())
    with pytest.raises(RelationshipIntegrityError):
        EvidenceRegistry().register(harness.build_evidence()).register(harness.build_evidence())
    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry().register(harness.build_hypothesis(), EvidenceRegistry())
    with pytest.raises(RelationshipIntegrityError):
        ScenarioRegistry().register(harness.build_scenario(), HypothesisRegistry(), evidence)
    with pytest.raises(ValueError):
        (
            DecisionGraphBuilder()
            .add_node(DecisionGraphNode("only", DecisionNodeType.EVIDENCE))
            .connect("missing", "only")
            .build()
        )
    resolver = harness.resolver()
    candidate = harness.build_candidate()
    candidates = CandidateRegistry().register(candidate, resolver, ("candidate",))
    with pytest.raises(RelationshipIntegrityError):
        candidates.register(candidate, resolver, ("candidate",))
    failed = DecisionEngine(resolver, candidates, ConfidenceRegistry()).decide(
        DecisionContext("EURUSD", "H1", "fault")
    )
    assert failed.decision is None and failed.audit.validation_failures == 1
    malformed = replace(harness.build_hypothesis(), evidence=(EvidenceReference("missing", 1),))
    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry().register(malformed, evidence)


def test_validation_snapshot_and_value_objects_remain_strict() -> None:
    manager = DecisionValidationManager()
    report = manager.validate_framework()
    stress = manager.stress(manager.framework_campaigns(1, 1))
    snapshot = DecisionValidationSnapshot.capture(report, stress)
    restored = DecisionValidationSnapshot.from_json(snapshot.to_json())
    assert restored == snapshot and restored.digest == snapshot.digest
    malformed = json.loads(snapshot.to_json())
    malformed["digest"] = "0" * 64
    with pytest.raises(RelationshipIntegrityError):
        DecisionValidationSnapshot.from_json(json.dumps(malformed))
    for value, algorithm in (
        ("0" * 63, "sha256"),
        ("Z" * 64, "sha256"),
        ("0" * 64, "sha1"),
    ):
        with pytest.raises(RelationshipIntegrityError):
            DecisionValidationDigest(value, algorithm)
    with pytest.raises(RelationshipIntegrityError):
        DecisionValidationStatistics(1, 1, 1, 0, 0)
    assert DecisionValidationDiagnostics(("z", "a", "z")).issues == ("a", "z")


def test_campaign_failures_and_anomalies_prevent_certification() -> None:
    manager = DecisionValidationManager()

    def fault() -> None:
        raise RelationshipIntegrityError("injected real-boundary failure")

    stress = manager.stress({"fault": (2, fault)})
    benchmark = manager.benchmark({"fault": (1, fault)})
    assert stress.failures == benchmark.anomalies == ("fault",)
    certification = manager.certify(manager.validate_framework(), stress, benchmark)
    assert not certification.certified
    with pytest.raises(RelationshipIntegrityError):
        manager.framework_benchmarks(0)
    with pytest.raises(RelationshipIntegrityError):
        DecisionStressReport.create((("bad", -1),))
    with pytest.raises(RelationshipIntegrityError):
        DecisionBenchmarkReport((("bad", 0, 0),))


def test_all_validation_integrity_and_deserialization_failures() -> None:
    manager = DecisionValidationManager()
    report = manager.validate_framework()
    stress = manager.stress(manager.framework_campaigns(1, 1))
    snapshot = DecisionValidationSnapshot.capture(report, stress)
    for value, algorithm in (
        ("g" * 64, "sha256"),
        ("0" * 63, "sha256"),
        ("0" * 64, "sha1"),
    ):
        with pytest.raises(RelationshipIntegrityError):
            DecisionValidationDigest(value, algorithm)
    with pytest.raises(RelationshipIntegrityError):
        DecisionValidationStatistics(-1, 0, 0, 0, 0)
    with pytest.raises(RelationshipIntegrityError):
        replace(report.audit, validation_coverage=2.0)
    with pytest.raises(RelationshipIntegrityError):
        DecisionValidationDiagnostics(["bad"])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        replace(stress, operations=[])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        replace(stress, digest=DecisionValidationDigest("0" * 64))
    with pytest.raises(RelationshipIntegrityError):
        DecisionBenchmarkReport([], ())  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        replace(report, checks=[])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        replace(report, checks=report.checks + (report.checks[0],))
    certification = DecisionCertificationReport.from_validation(report)
    with pytest.raises(RelationshipIntegrityError):
        replace(certification, digest=DecisionValidationDigest("0" * 64))
    with pytest.raises(RelationshipIntegrityError):
        replace(snapshot, version=0)
    with pytest.raises(RelationshipIntegrityError):
        replace(snapshot, digest=DecisionValidationDigest("0" * 64))

    encoded = snapshot.to_json()
    invalid_payloads = ("not-json", "[]", json.dumps({}))
    for value in invalid_payloads:
        with pytest.raises(RelationshipIntegrityError):
            DecisionValidationSnapshot.from_json(value)
    mutations: tuple[tuple[tuple[str, ...], object], ...] = (
        (("report",), []),
        (("stress", "operations"), {}),
        (("stress", "failures", "0"), 1),
        (("report", "checks", "0", "0"), 1),
        (("report", "checks", "0", "1"), "yes"),
        (("report", "statistics", "checks"), True),
        (("report", "audit", "determinism"), "yes"),
        (("report", "audit", "validation_coverage"), True),
    )
    for path, malformed_value in mutations:
        malformed = json.loads(encoded)
        if path == ("stress", "failures", "0"):
            malformed["stress"]["failures"] = ["failure"]
        target = malformed
        for part in path[:-1]:
            target = target[int(part)] if part.isdigit() else target[part]
        final = path[-1]
        if final.isdigit():
            target[int(final)] = malformed_value
        else:
            target[final] = malformed_value
        with pytest.raises(RelationshipIntegrityError):
            DecisionValidationSnapshot.from_json(json.dumps(malformed))
    malformed = json.loads(encoded)
    malformed["digest"] = "0" * 64
    with pytest.raises(RelationshipIntegrityError):
        DecisionValidationSnapshot.from_json(json.dumps(malformed))
    with pytest.raises(RelationshipIntegrityError):
        manager.stress({"negative": (-1, lambda: None)})

    harness = DecisionFrameworkHarness()
    resolver = harness.resolver()
    candidate = harness.build_candidate()
    failed_report = DecisionEngine(
        resolver,
        CandidateRegistry().register(candidate, resolver, ("candidate",)),
        ConfidenceRegistry(),
    ).decide(DecisionContext("EURUSD", "H1", "failed"))
    with pytest.raises(RelationshipIntegrityError):
        DecisionFrameworkRun(
            harness.build_evidence(),
            harness.build_hypothesis(),
            harness.build_scenario(),
            harness.build_graph().to_json(),
            candidate.candidate_id,
            "missing",
            failed_report,
        ).to_json()
    clean_benchmark = manager.framework_benchmarks(1)
    assert manager.certify(report, stress, clean_benchmark).certified
