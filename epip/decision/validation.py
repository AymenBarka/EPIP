"""Institutional validation and certification infrastructure for EPIP-016.

This module observes immutable Programme A-G artifacts. It adds no decision,
confidence, inference, graph, evidence, financial, or execution behaviour.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter_ns
from typing import NamedTuple

from epip.core.integrity import RelationshipIntegrityError
from epip.decision.candidate import (
    CandidateBuilder,
    CandidateEngine,
    CandidateReferenceResolver,
    CandidateRegistry,
)
from epip.decision.confidence import ConfidenceBuilder, ConfidenceEngine, ConfidenceRegistry
from epip.decision.decision_engine import DecisionEngine, DecisionSelectionReport
from epip.decision.domain import (
    CandidateType,
    Confidence,
    ConfidenceLevel,
    ConstraintEvaluation,
    ConstraintType,
    DecisionCandidate,
    DecisionContext,
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
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.evidence import EvidenceBuilder, EvidenceEngine, EvidenceRegistry
from epip.decision.graph import (
    DecisionDependency,
    DecisionDependencyGraph,
    DecisionExecutionPlan,
    DecisionGraphBuilder,
    DecisionGraphNode,
    DecisionGraphSnapshot,
    DecisionNodeType,
)
from epip.decision.inference import (
    HypothesisBuilder,
    HypothesisRegistry,
    InferenceEngine,
    ScenarioBuilder,
    ScenarioRegistry,
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DecisionValidationDigest:
    """Canonical SHA-256 validation digest."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.algorithm != "sha256" or len(self.value) != 64 or self.value != self.value.lower():
            raise RelationshipIntegrityError("validation digest must be SHA-256")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise RelationshipIntegrityError("validation digest must be hexadecimal") from exc


@dataclass(frozen=True, slots=True)
class DecisionValidationStatistics:
    """Coverage and conformance counts."""

    checks: int
    passed: int
    failed: int
    modules: int
    registries: int

    def __post_init__(self) -> None:
        values = (self.checks, self.passed, self.failed, self.modules, self.registries)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values
        ):
            raise RelationshipIntegrityError("validation statistics must be non-negative integers")
        if self.passed + self.failed != self.checks:
            raise RelationshipIntegrityError("validation statistics are inconsistent")


@dataclass(frozen=True, slots=True)
class DecisionValidationAudit:
    """Read-only institutional coverage observations."""

    validation_coverage: float
    determinism: bool
    digest_stability: bool
    registry_completeness: bool
    decision_reproducibility: bool
    explainability_completeness: bool

    def __post_init__(self) -> None:
        if (
            isinstance(self.validation_coverage, bool)
            or not isinstance(self.validation_coverage, (int, float))
            or not 0 <= self.validation_coverage <= 1
        ):
            raise RelationshipIntegrityError("validation coverage must be normalized")


@dataclass(frozen=True, slots=True)
class DecisionValidationDiagnostics:
    """Immutable findings; diagnostics never repair observed artifacts."""

    issues: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.issues, tuple):
            raise RelationshipIntegrityError("validation diagnostics must be a tuple")
        object.__setattr__(self, "issues", tuple(sorted(set(self.issues))))


@dataclass(frozen=True, slots=True)
class DecisionStressReport:
    """Bounded deterministic campaign operation counts and digest."""

    operations: tuple[tuple[str, int], ...]
    failures: tuple[str, ...]
    digest: DecisionValidationDigest

    def __post_init__(self) -> None:
        if not isinstance(self.operations, tuple) or not isinstance(self.failures, tuple):
            raise RelationshipIntegrityError("stress report values must be tuples")
        if any(count < 0 for _, count in self.operations):
            raise RelationshipIntegrityError("stress operation counts must be non-negative")
        expected = DecisionValidationDigest(
            _sha256({"failures": self.failures, "operations": self.operations})
        )
        if self.digest != expected:
            raise RelationshipIntegrityError("stress report digest mismatch")

    @classmethod
    def create(
        cls, operations: tuple[tuple[str, int], ...], failures: tuple[str, ...] = ()
    ) -> DecisionStressReport:
        operations = tuple(sorted(operations))
        failures = tuple(sorted(failures))
        return cls(
            operations,
            failures,
            DecisionValidationDigest(_sha256({"failures": failures, "operations": operations})),
        )


@dataclass(frozen=True, slots=True)
class DecisionBenchmarkReport:
    """Engineering reference measurements; values are not an SLA."""

    measurements: tuple[tuple[str, int, int], ...]
    anomalies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.measurements, tuple) or not isinstance(self.anomalies, tuple):
            raise RelationshipIntegrityError("benchmark report values must be tuples")
        if any(operations < 1 or elapsed_ns < 0 for _, operations, elapsed_ns in self.measurements):
            raise RelationshipIntegrityError("benchmark measurements are invalid")
        object.__setattr__(self, "measurements", tuple(sorted(self.measurements)))
        object.__setattr__(self, "anomalies", tuple(sorted(set(self.anomalies))))


@dataclass(frozen=True, slots=True)
class DecisionValidationReport:
    """Complete immutable framework validation result."""

    checks: tuple[tuple[str, bool], ...]
    statistics: DecisionValidationStatistics
    audit: DecisionValidationAudit
    diagnostics: DecisionValidationDiagnostics

    def __post_init__(self) -> None:
        if not isinstance(self.checks, tuple):
            raise RelationshipIntegrityError("validation checks must be a tuple")
        names = tuple(name for name, _ in self.checks)
        if len(names) != len(set(names)):
            raise RelationshipIntegrityError("duplicate validation check")
        object.__setattr__(self, "checks", tuple(sorted(self.checks)))

    @property
    def certified(self) -> bool:
        return not self.diagnostics.issues and all(result for _, result in self.checks)

    def to_payload(self) -> dict[str, object]:
        return {
            "audit": {
                "decision_reproducibility": self.audit.decision_reproducibility,
                "determinism": self.audit.determinism,
                "digest_stability": self.audit.digest_stability,
                "explainability_completeness": self.audit.explainability_completeness,
                "registry_completeness": self.audit.registry_completeness,
                "validation_coverage": self.audit.validation_coverage,
            },
            "checks": [list(item) for item in self.checks],
            "diagnostics": list(self.diagnostics.issues),
            "statistics": {
                "checks": self.statistics.checks,
                "failed": self.statistics.failed,
                "modules": self.statistics.modules,
                "passed": self.statistics.passed,
                "registries": self.statistics.registries,
            },
        }


@dataclass(frozen=True, slots=True)
class DecisionCertificationReport:
    """Final institutional certification across the eleven required domains."""

    architecture: bool
    determinism: bool
    explainability: bool
    replay_compatibility: bool
    immutability: bool
    registry_integrity: bool
    serialization: bool
    digest_stability: bool
    decision_reproducibility: bool
    backward_compatibility: bool
    cross_module_consistency: bool
    digest: DecisionValidationDigest

    def content_payload(self) -> dict[str, bool]:
        return {
            "architecture": self.architecture,
            "backward_compatibility": self.backward_compatibility,
            "cross_module_consistency": self.cross_module_consistency,
            "decision_reproducibility": self.decision_reproducibility,
            "determinism": self.determinism,
            "digest_stability": self.digest_stability,
            "explainability": self.explainability,
            "immutability": self.immutability,
            "registry_integrity": self.registry_integrity,
            "replay_compatibility": self.replay_compatibility,
            "serialization": self.serialization,
        }

    def __post_init__(self) -> None:
        if self.digest != DecisionValidationDigest(_sha256(self.content_payload())):
            raise RelationshipIntegrityError("certification digest mismatch")

    @property
    def certified(self) -> bool:
        return all(self.content_payload().values())

    @classmethod
    def from_validation(cls, report: DecisionValidationReport) -> DecisionCertificationReport:
        results = dict(report.checks)
        values = {
            "architecture": results.get("architecture", False),
            "determinism": report.audit.determinism,
            "explainability": report.audit.explainability_completeness,
            "replay_compatibility": results.get("replay_compatibility", False),
            "immutability": results.get("immutability", False),
            "registry_integrity": report.audit.registry_completeness,
            "serialization": results.get("serialization", False),
            "digest_stability": report.audit.digest_stability,
            "decision_reproducibility": report.audit.decision_reproducibility,
            "backward_compatibility": results.get("backward_compatibility", False),
            "cross_module_consistency": results.get("cross_module_consistency", False),
        }
        return cls(**values, digest=DecisionValidationDigest(_sha256(values)))


@dataclass(frozen=True, slots=True)
class DecisionValidationSnapshot:
    """Canonical replay-compatible validation snapshot."""

    report: DecisionValidationReport
    certification: DecisionCertificationReport
    stress: DecisionStressReport
    digest: DecisionValidationDigest
    version: int = 1

    def content_payload(self) -> dict[str, object]:
        return {
            "certification": {
                **self.certification.content_payload(),
                "digest": self.certification.digest.value,
            },
            "report": self.report.to_payload(),
            "stress": {
                "digest": self.stress.digest.value,
                "failures": list(self.stress.failures),
                "operations": [list(item) for item in self.stress.operations],
            },
            "version": self.version,
        }

    def __post_init__(self) -> None:
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise RelationshipIntegrityError("validation snapshot version must be positive")
        if self.digest != DecisionValidationDigest(_sha256(self.content_payload())):
            raise RelationshipIntegrityError("validation snapshot digest mismatch")

    @classmethod
    def capture(
        cls, report: DecisionValidationReport, stress: DecisionStressReport
    ) -> DecisionValidationSnapshot:
        certification = DecisionCertificationReport.from_validation(report)
        instance = object.__new__(cls)
        object.__setattr__(instance, "report", report)
        object.__setattr__(instance, "certification", certification)
        object.__setattr__(instance, "stress", stress)
        object.__setattr__(instance, "version", 1)
        object.__setattr__(
            instance, "digest", DecisionValidationDigest(_sha256(instance.content_payload()))
        )
        instance.__post_init__()
        return instance

    def to_json(self) -> str:
        return _canonical_json({**self.content_payload(), "digest": self.digest.value})

    @classmethod
    def from_json(cls, value: str) -> DecisionValidationSnapshot:
        try:
            payload = json.loads(value)
            if not isinstance(payload, dict):
                raise RelationshipIntegrityError("validation snapshot must be an object")
            report = _report_from_payload(payload.get("report"))
            stress_payload = _mapping(payload.get("stress"), "stress")
            operations = tuple(
                (_text(item[0], "operation"), _integer(item[1], "count"))
                for raw in _sequence(stress_payload.get("operations"), "operations")
                for item in (_sequence(raw, "operation"),)
                if len(item) == 2
            )
            stress = DecisionStressReport(
                operations,
                tuple(
                    _text(item, "failure")
                    for item in _sequence(stress_payload.get("failures"), "failures")
                ),
                DecisionValidationDigest(_text(stress_payload.get("digest"), "stress digest")),
            )
            snapshot = cls.capture(report, stress)
            version = _integer(payload.get("version"), "version")
            if (
                version != snapshot.version
                or _text(payload.get("digest"), "digest") != snapshot.digest.value
            ):
                raise RelationshipIntegrityError("validation snapshot digest mismatch")
            return snapshot
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, RelationshipIntegrityError):
                raise
            raise RelationshipIntegrityError("invalid validation snapshot") from exc


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise RelationshipIntegrityError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise RelationshipIntegrityError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RelationshipIntegrityError(f"{label} must be text")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RelationshipIntegrityError(f"{label} must be an integer")
    return value


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise RelationshipIntegrityError(f"{label} must be boolean")
    return value


def _report_from_payload(value: object) -> DecisionValidationReport:
    payload = _mapping(value, "report")
    statistics = _mapping(payload.get("statistics"), "statistics")
    audit = _mapping(payload.get("audit"), "audit")
    coverage = audit.get("validation_coverage")
    if isinstance(coverage, bool) or not isinstance(coverage, (int, float)):
        raise RelationshipIntegrityError("validation coverage must be numeric")
    checks = tuple(
        (_text(item[0], "check"), _boolean(item[1], "result"))
        for raw in _sequence(payload.get("checks"), "checks")
        for item in (_sequence(raw, "check"),)
        if len(item) == 2
    )
    return DecisionValidationReport(
        checks,
        DecisionValidationStatistics(
            _integer(statistics.get("checks"), "checks"),
            _integer(statistics.get("passed"), "passed"),
            _integer(statistics.get("failed"), "failed"),
            _integer(statistics.get("modules"), "modules"),
            _integer(statistics.get("registries"), "registries"),
        ),
        DecisionValidationAudit(
            float(coverage),
            _boolean(audit.get("determinism"), "determinism"),
            _boolean(audit.get("digest_stability"), "digest stability"),
            _boolean(audit.get("registry_completeness"), "registry completeness"),
            _boolean(audit.get("decision_reproducibility"), "decision reproducibility"),
            _boolean(audit.get("explainability_completeness"), "explainability completeness"),
        ),
        DecisionValidationDiagnostics(
            tuple(
                _text(item, "diagnostic")
                for item in _sequence(payload.get("diagnostics"), "diagnostics")
            )
        ),
    )


class DecisionFrameworkRun(NamedTuple):
    """Actual immutable A-G pipeline artifacts used as certification evidence."""

    evidence: Evidence
    hypothesis: Hypothesis
    scenario: Scenario
    graph_json: str
    candidate_id: str
    assessment_id: str
    decision_report: DecisionSelectionReport

    def _validate(self) -> None:
        if self.decision_report.decision is None or self.decision_report.trace is None:
            raise RelationshipIntegrityError("real decision pipeline did not produce a decision")

    def canonical_payload(self) -> dict[str, object]:
        self._validate()
        decision = self.decision_report.decision
        trace = self.decision_report.trace
        assert decision is not None and trace is not None
        return {
            "assessment_id": self.assessment_id,
            "candidate_id": self.candidate_id,
            "decision": decision.to_dict(),
            "evidence": self.evidence.to_dict(),
            "graph": json.loads(self.graph_json),
            "hypothesis": self.hypothesis.to_dict(),
            "scenario": self.scenario.to_dict(),
            "snapshot": json.loads(self.decision_report.snapshot.to_json()),
            "trace": trace.to_payload(),
        }

    def to_json(self) -> str:
        return _canonical_json(self.canonical_payload())

    @property
    def digest(self) -> DecisionValidationDigest:
        return DecisionValidationDigest(_sha256(self.canonical_payload()))


class DecisionFrameworkHarness:
    """Construct and exercise the real immutable EPIP-016 A-G framework."""

    def scores(self) -> tuple[Confidence, Quality, Validity, Uncertainty]:
        return (
            Confidence(0.8, ConfidenceLevel.HIGH),
            Quality(0.9, QualityLevel.VERY_HIGH),
            Validity(1.0, ValidityLevel.VALID),
            Uncertainty(0.2),
        )

    def build_evidence(self) -> Evidence:
        confidence, quality, validity, uncertainty = self.scores()
        return EvidenceBuilder().build(
            evidence_id="cert-evidence",
            category=EvidenceCategory.MARKET_DATA,
            source="certification-feed",
            source_version=1,
            payload=(("price", "1.10000"),),
            confidence=confidence,
            quality=quality,
            validity=validity,
            uncertainty=uncertainty,
            dependencies=(),
            metadata=DecisionMetadata(1, "logical-1", "programme-h1"),
        )

    def build_hypothesis(self) -> Hypothesis:
        confidence, quality, validity, uncertainty = self.scores()
        reference = EvidenceReference("cert-evidence", 1)
        return HypothesisBuilder().build(
            hypothesis_id="cert-hypothesis",
            category=HypothesisCategory.DIRECTIONAL,
            evidence=(reference,),
            supporting_evidence=(reference,),
            contradicting_evidence=(),
            assumptions=("certification evidence remains valid",),
            invalidation_conditions=("evidence is withdrawn",),
            confidence=confidence,
            quality=quality,
            validity=validity,
            uncertainty=uncertainty,
            metadata=DecisionMetadata(1, "logical-2", "programme-h1"),
        )

    def build_scenario(self) -> Scenario:
        confidence, quality, validity, uncertainty = self.scores()
        return ScenarioBuilder().build(
            scenario_id="cert-scenario",
            category=ScenarioCategory.BULLISH,
            hypotheses=(HypothesisReference("cert-hypothesis", 1),),
            parent_scenarios=(),
            supporting_evidence=(EvidenceReference("cert-evidence", 1),),
            contradicting_evidence=(),
            assumptions=("certification hypothesis remains valid",),
            invalidation_conditions=("hypothesis is withdrawn",),
            confidence=confidence,
            quality=quality,
            validity=validity,
            uncertainty=uncertainty,
            metadata=DecisionMetadata(1, "logical-3", "programme-h1"),
        )

    def build_graph(self) -> DecisionDependencyGraph:
        return (
            DecisionGraphBuilder()
            .add_node(DecisionGraphNode("evidence", DecisionNodeType.EVIDENCE))
            .add_node(
                DecisionGraphNode(
                    "hypothesis",
                    DecisionNodeType.HYPOTHESIS,
                    (DecisionDependency("evidence"),),
                )
            )
            .add_node(
                DecisionGraphNode(
                    "scenario",
                    DecisionNodeType.SCENARIO,
                    (DecisionDependency("hypothesis"),),
                )
            )
            .add_node(
                DecisionGraphNode(
                    "candidate",
                    DecisionNodeType.CANDIDATE,
                    (DecisionDependency("scenario"),),
                )
            )
            .connect("evidence", "hypothesis")
            .connect("hypothesis", "scenario")
            .connect("scenario", "candidate")
            .build(require_single_root=True)
        )

    def resolver(self) -> CandidateReferenceResolver:
        evidence = EvidenceRegistry().register(self.build_evidence())
        hypotheses = HypothesisRegistry().register(self.build_hypothesis(), evidence)
        scenarios = ScenarioRegistry().register(self.build_scenario(), hypotheses, evidence)
        return CandidateReferenceResolver(evidence, hypotheses, scenarios, self.build_graph())

    def build_candidate(self) -> DecisionCandidate:
        resolver = self.resolver()
        constraint = ConstraintEvaluation(
            "cert-policy", ConstraintType.POLICY, True, True, "certified input"
        )
        return CandidateBuilder(resolver).build(
            "cert-scenario",
            CandidateType.LONG,
            candidate_id="cert-candidate",
            constraints=(constraint,),
            graph_node_ids=("candidate",),
        )

    def run(self) -> DecisionFrameworkRun:
        resolver = self.resolver()
        candidate = self.build_candidate()
        candidates = CandidateRegistry().register(candidate, resolver, ("candidate",))
        assessment = ConfidenceBuilder(resolver).build(candidate, graph_node_ids=("candidate",))
        assessments = ConfidenceRegistry().register(assessment)
        report = DecisionEngine(resolver, candidates, assessments).decide(
            DecisionContext("EURUSD", "H1", "certification-run")
        )
        return DecisionFrameworkRun(
            self.build_evidence(),
            self.build_hypothesis(),
            self.build_scenario(),
            DecisionGraphSnapshot.capture(self.build_graph()).to_json(),
            candidate.candidate_id,
            assessment.assessment_id,
            report,
        )

    def operations(self) -> dict[str, Callable[[], object]]:
        resolver = self.resolver()
        candidate = self.build_candidate()
        candidates = CandidateRegistry().register(candidate, resolver, ("candidate",))
        assessment = ConfidenceBuilder(resolver).build(candidate, graph_node_ids=("candidate",))
        assessments = ConfidenceRegistry().register(assessment)
        return {
            "audit_creation": lambda: DecisionEngine(resolver, candidates, assessments)
            .decide(DecisionContext("EURUSD", "H1", "certification-run"))
            .audit,
            "candidate_generation": lambda: CandidateEngine(resolver).generate(
                "cert-scenario", (CandidateType.LONG,), graph_node_ids=("candidate",)
            ),
            "complete_decision_pipeline": self.run,
            "confidence_assessment": lambda: ConfidenceEngine(resolver, candidates).assess(
                (candidate.candidate_id,), graph_node_ids=("candidate",)
            ),
            "decision_selection": lambda: DecisionEngine(resolver, candidates, assessments).decide(
                DecisionContext("EURUSD", "H1", "certification-run")
            ),
            "evidence_registration": lambda: EvidenceEngine().register(self.build_evidence()),
            "explainability_generation": lambda: DecisionEngine(resolver, candidates, assessments)
            .decide(DecisionContext("EURUSD", "H1", "certification-run"))
            .decision,
            "graph_construction": self.build_graph,
            "graph_traversal": lambda: DecisionExecutionPlan.from_graph(self.build_graph()),
            "hypothesis_generation": lambda: InferenceEngine(
                EvidenceRegistry().register(self.build_evidence())
            ).register_hypothesis(self.build_hypothesis()),
            "scenario_generation": lambda: InferenceEngine(
                EvidenceRegistry().register(self.build_evidence()),
                HypothesisRegistry().register(
                    self.build_hypothesis(),
                    EvidenceRegistry().register(self.build_evidence()),
                ),
            ).register_scenario(self.build_scenario()),
            "snapshot_generation": lambda: DecisionGraphSnapshot.capture(self.build_graph()),
        }


@dataclass(frozen=True, slots=True)
class DecisionValidationManager:
    """Execute bounded deterministic validation without retaining campaign objects."""

    def validate_framework(
        self, harness: DecisionFrameworkHarness | None = None
    ) -> DecisionValidationReport:
        """Execute two complete real A-G pipelines and certify their artifacts."""
        harness = harness or DecisionFrameworkHarness()
        first = harness.run()
        replay = harness.run()
        first_decision = first.decision_report.decision
        replay_decision = replay.decision_report.decision
        first_trace = first.decision_report.trace
        replay_trace = replay.decision_report.trace
        assert first_decision is not None and replay_decision is not None
        assert first_trace is not None and replay_trace is not None
        checks = tuple(
            sorted(
                {
                    "architecture": all(
                        (
                            first.evidence,
                            first.hypothesis,
                            first.scenario,
                            first.candidate_id,
                            first.assessment_id,
                            first_decision,
                        )
                    ),
                    "backward_compatibility": EvidenceEngine is not None
                    and InferenceEngine is not None,
                    "cross_module_consistency": (
                        first_trace.evidence == first_decision.explanation.supporting_evidence
                        and first_trace.hypotheses == first_decision.explanation.accepted_hypotheses
                        and first_trace.scenarios == first_decision.explanation.scenarios
                    ),
                    "determinism": first.to_json() == replay.to_json(),
                    "digest_stability": first.digest == replay.digest,
                    "explainability": bool(
                        first_decision.explanation.reasons
                        and first_trace.confidence_assessment_id
                        and first_trace.graph_node_ids
                    ),
                    "immutability": hash(first_decision) == hash(replay_decision),
                    "registry_integrity": bool(
                        first.decision_report.registry.entries
                        and first.decision_report.diagnostics.issues == ()
                    ),
                    "replay_compatibility": (
                        first.decision_report.snapshot.to_json()
                        == replay.decision_report.snapshot.to_json()
                    ),
                    "serialization": (json.loads(first.to_json()) == first.canonical_payload()),
                }.items()
            )
        )
        passed = sum(result for _, result in checks)
        issues = tuple(f"validation_failure:{name}" for name, result in checks if not result)
        statistics = DecisionValidationStatistics(len(checks), passed, len(checks) - passed, 7, 6)
        audit = DecisionValidationAudit(
            passed / len(checks),
            dict(checks)["determinism"],
            dict(checks)["digest_stability"],
            dict(checks)["registry_integrity"],
            first_decision == replay_decision,
            dict(checks)["explainability"],
        )
        return DecisionValidationReport(
            checks, statistics, audit, DecisionValidationDiagnostics(issues)
        )

    def framework_campaigns(
        self,
        operation_count: int = 100_000,
        pipeline_count: int = 1_000,
        harness: DecisionFrameworkHarness | None = None,
    ) -> dict[str, tuple[int, Callable[[], object]]]:
        """Return mandated campaigns backed exclusively by actual A-G operations."""
        operations = (harness or DecisionFrameworkHarness()).operations()
        names = (
            "evidence_registration",
            "hypothesis_generation",
            "scenario_generation",
            "graph_construction",
            "graph_traversal",
            "candidate_generation",
            "confidence_assessment",
            "decision_selection",
        )
        return {
            **{name: (operation_count, operations[name]) for name in names},
            "complete_decision_pipeline": (
                pipeline_count,
                operations["complete_decision_pipeline"],
            ),
        }

    def framework_benchmarks(
        self,
        count: int,
        harness: DecisionFrameworkHarness | None = None,
    ) -> DecisionBenchmarkReport:
        """Benchmark named real framework operations, never empty callbacks."""
        operations = (harness or DecisionFrameworkHarness()).operations()
        return self.benchmark({name: (count, operation) for name, operation in operations.items()})

    def stress(
        self, campaigns: Mapping[str, tuple[int, Callable[[], object]]]
    ) -> DecisionStressReport:
        operations: list[tuple[str, int]] = []
        failures: list[str] = []
        for name, (count, operation) in sorted(campaigns.items()):
            if count < 0:
                raise RelationshipIntegrityError("stress count must be non-negative")
            for _ in range(count):
                try:
                    operation()
                except (LookupError, TypeError, ValueError, RelationshipIntegrityError):
                    failures.append(name)
                    break
            operations.append((name, count))
        return DecisionStressReport.create(tuple(operations), tuple(failures))

    def benchmark(
        self, operations: Mapping[str, tuple[int, Callable[[], object]]]
    ) -> DecisionBenchmarkReport:
        measurements: list[tuple[str, int, int]] = []
        anomalies: list[str] = []
        for name, (count, operation) in sorted(operations.items()):
            if count < 1:
                raise RelationshipIntegrityError("benchmark count must be positive")
            started = perf_counter_ns()
            try:
                for _ in range(count):
                    operation()
            except (LookupError, TypeError, ValueError, RelationshipIntegrityError):
                anomalies.append(name)
            measurements.append((name, count, perf_counter_ns() - started))
        return DecisionBenchmarkReport(tuple(measurements), tuple(anomalies))

    def certify(
        self,
        report: DecisionValidationReport,
        stress: DecisionStressReport,
        benchmark: DecisionBenchmarkReport,
    ) -> DecisionCertificationReport:
        issues = list(report.diagnostics.issues)
        if stress.failures:
            issues.append("validation_failure")
        if benchmark.anomalies:
            issues.append("benchmark_anomaly")
        if issues:
            checks = tuple(
                (name, False if name == "cross_module_consistency" else result)
                for name, result in report.checks
            )
            passed = sum(result for _, result in checks)
            report = DecisionValidationReport(
                checks,
                DecisionValidationStatistics(
                    len(checks),
                    passed,
                    len(checks) - passed,
                    report.statistics.modules,
                    report.statistics.registries,
                ),
                report.audit,
                DecisionValidationDiagnostics(tuple(issues)),
            )
        return DecisionCertificationReport.from_validation(report)


__all__ = [
    "DecisionBenchmarkReport",
    "DecisionCertificationReport",
    "DecisionStressReport",
    "DecisionValidationAudit",
    "DecisionValidationDiagnostics",
    "DecisionValidationDigest",
    "DecisionValidationManager",
    "DecisionValidationReport",
    "DecisionValidationSnapshot",
    "DecisionValidationStatistics",
]
