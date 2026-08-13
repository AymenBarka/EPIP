"""Tests for the deterministic EPIP-016 structural inference engine."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core import inference_engine
from epip.core.integrity import RelationshipIntegrityError
from epip.decision.domain import (
    Confidence,
    ConfidenceLevel,
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
from epip.decision.inference import (
    HypothesisBuilder,
    HypothesisCollection,
    HypothesisRegistry,
    InferenceCollection,
    InferenceDiagnostics,
    InferenceDigest,
    InferenceEngine,
    InferenceLifecycleState,
    InferenceSnapshot,
    InferenceValidator,
    ScenarioBuilder,
    ScenarioCollection,
    ScenarioRegistry,
    _HypothesisEntry,
    _ScenarioEntry,
)


def _scores() -> tuple[Confidence, Quality, Validity, Uncertainty]:
    return (
        Confidence(0.8, ConfidenceLevel.HIGH),
        Quality(0.9, QualityLevel.VERY_HIGH),
        Validity(1.0, ValidityLevel.VALID),
        Uncertainty(0.2),
    )


def _evidence(identifier: str = "evidence-1") -> Evidence:
    confidence, quality, validity, uncertainty = _scores()
    return EvidenceBuilder().build(
        evidence_id=identifier,
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


def _hypothesis(identifier: str = "hypothesis-1", evidence_id: str = "evidence-1") -> Hypothesis:
    confidence, quality, validity, uncertainty = _scores()
    reference = EvidenceReference(evidence_id, 1)
    return HypothesisBuilder().build(
        hypothesis_id=identifier,
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


def _scenario(
    identifier: str = "scenario-1",
    hypothesis_id: str = "hypothesis-1",
    *,
    parents: tuple[ScenarioReference, ...] = (),
) -> Scenario:
    confidence, quality, validity, uncertainty = _scores()
    return ScenarioBuilder().build(
        scenario_id=identifier,
        category=ScenarioCategory.BULLISH,
        hypotheses=(HypothesisReference(hypothesis_id, 1),),
        parent_scenarios=parents,
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


def _registries() -> tuple[EvidenceRegistry, HypothesisRegistry, ScenarioRegistry]:
    evidence = EvidenceRegistry().register(_evidence())
    hypotheses = HypothesisRegistry().register(_hypothesis(), evidence)
    scenarios = ScenarioRegistry().register(_scenario(), hypotheses, evidence)
    return evidence, hypotheses, scenarios


def test_public_module_and_digest_are_deterministic() -> None:
    assert inference_engine.InferenceEngine is InferenceEngine
    assert InferenceDigest.from_value({"b": 2, "a": 1}) == InferenceDigest.from_value(
        {"a": 1, "b": 2}
    )
    with pytest.raises(RelationshipIntegrityError):
        InferenceDigest("0" * 63)
    with pytest.raises(RelationshipIntegrityError):
        InferenceDigest("z" * 64)
    with pytest.raises(RelationshipIntegrityError):
        InferenceDigest("0" * 64, "sha1")


def test_builders_are_deterministic_and_models_are_immutable() -> None:
    first = _hypothesis()
    second = _hypothesis()
    assert first == second
    assert first.content_digest == second.content_digest
    assert len(first.content_digest.value) == 64
    with pytest.raises(FrozenInstanceError):
        setattr(first, "hypothesis_id", "changed")  # noqa: B010
    scenario = _scenario()
    assert scenario.ranking_inputs == ()
    assert scenario.content_digest == _scenario().content_digest


def test_collections_are_ordered_immutable_unique_and_queryable() -> None:
    one = _hypothesis("a")
    two = replace(_hypothesis("b"), category=HypothesisCategory.STRUCTURAL)
    hypotheses = InferenceCollection((two, one))
    assert HypothesisCollection is InferenceCollection
    assert tuple(hypotheses) == (one, two)
    assert hypotheses.get("a") == one
    assert hypotheses.get("missing") is None
    assert hypotheses.by_category(HypothesisCategory.STRUCTURAL).items == (two,)
    assert hypotheses.by_evidence(EvidenceReference("evidence-1", 1)).items == (one, two)
    assert len(hypotheses.group_by_category()) == 2
    with pytest.raises(RelationshipIntegrityError):
        InferenceCollection([one])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        InferenceCollection((one, one))

    first = _scenario("a")
    second = replace(_scenario("b"), category=ScenarioCategory.NEUTRAL)
    scenarios = ScenarioCollection((second, first))
    assert tuple(scenarios) == (first, second)
    assert scenarios.get("missing") is None
    assert scenarios.by_category(ScenarioCategory.NEUTRAL).items == (second,)
    assert scenarios.by_hypothesis(HypothesisReference("hypothesis-1", 1)).items == (
        first,
        second,
    )
    assert len(scenarios.group_by_category()) == 2
    with pytest.raises(RelationshipIntegrityError):
        ScenarioCollection((first, first))


def test_registries_enforce_lifecycle_and_all_indexes() -> None:
    evidence, hypotheses, scenarios = _registries()
    hypothesis = hypotheses.get("hypothesis-1")
    scenario = scenarios.get("scenario-1")
    assert hypothesis is not None and scenario is not None
    assert hypotheses.entry("hypothesis-1").state is InferenceLifecycleState.REGISTERED
    assert scenarios.entry("scenario-1").state is InferenceLifecycleState.REGISTERED
    assert hypotheses.by_reference(HypothesisReference("hypothesis-1", 1)) == hypothesis
    assert hypotheses.by_reference(HypothesisReference("hypothesis-1", 2)) is None
    assert hypotheses.by_type(type(hypothesis)).items == (hypothesis,)
    assert hypotheses.by_category(HypothesisCategory.DIRECTIONAL).items == (hypothesis,)
    assert hypotheses.by_evidence(EvidenceReference("evidence-1", 1)).items == (hypothesis,)
    assert hypotheses.by_digest(hypothesis.content_digest) == hypothesis
    assert hypotheses.by_digest(hypothesis.content_digest.value) == hypothesis
    assert scenarios.by_reference(ScenarioReference("scenario-1", 1)) == scenario
    assert scenarios.by_type(type(scenario)).items == (scenario,)
    assert scenarios.by_category(ScenarioCategory.BULLISH).items == (scenario,)
    assert scenarios.by_hypothesis(HypothesisReference("hypothesis-1", 1)).items == (scenario,)
    assert scenarios.by_evidence(EvidenceReference("evidence-1", 1)).items == (scenario,)
    assert scenarios.by_digest(scenario.content_digest) == scenario
    assert not scenarios.by_scenario(ScenarioReference("scenario-1", 1)).items
    with pytest.raises(KeyError):
        hypotheses.entry("missing")
    with pytest.raises(RelationshipIntegrityError):
        hypotheses.register(hypothesis, evidence)
    with pytest.raises(RelationshipIntegrityError):
        scenarios.register(scenario, hypotheses, evidence)
    with pytest.raises(RelationshipIntegrityError):
        hypotheses.transition("hypothesis-1", InferenceLifecycleState.ARCHIVED)

    hypotheses = hypotheses.transition("hypothesis-1", InferenceLifecycleState.AVAILABLE)
    hypotheses = hypotheses.transition("hypothesis-1", InferenceLifecycleState.SNAPSHOTTED)
    hypotheses = hypotheses.transition("hypothesis-1", InferenceLifecycleState.ARCHIVED)
    hypotheses = hypotheses.transition("hypothesis-1", InferenceLifecycleState.DISCARDED)
    assert hypotheses.entry("hypothesis-1").state is InferenceLifecycleState.DISCARDED


def test_parent_scenario_lookup_and_structural_validation() -> None:
    evidence, hypotheses, scenarios = _registries()
    child = _scenario("scenario-2", parents=(ScenarioReference("scenario-1", 1),))
    scenarios = scenarios.register(child, hypotheses, evidence)
    assert scenarios.by_scenario(ScenarioReference("scenario-1", 1)).items == (child,)
    with pytest.raises(RelationshipIntegrityError):
        scenarios.register(
            _scenario("self", parents=(ScenarioReference("self", 1),)),
            hypotheses,
            evidence,
        )
    with pytest.raises(RelationshipIntegrityError):
        ScenarioRegistry().register(_scenario(), HypothesisRegistry(), evidence)
    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry().register(_hypothesis(evidence_id="unknown"), evidence)

    ranked = replace(child, ranking_inputs=(("rank", 1.0),))
    with pytest.raises(RelationshipIntegrityError):
        InferenceValidator().validate_scenario(ranked, hypotheses, scenarios, evidence)
    tampered = replace(_hypothesis(), content_digest=DecisionDigest("f" * 64))
    with pytest.raises(RelationshipIntegrityError):
        InferenceValidator().validate_hypothesis(tampered, evidence)


def test_engine_snapshot_round_trip_audit_diagnostics_and_rejections() -> None:
    evidence = EvidenceRegistry().register(_evidence())
    engine = InferenceEngine(evidence).register_hypothesis(_hypothesis())
    engine = engine.make_hypothesis_available("hypothesis-1")
    engine = engine.register_scenario(_scenario())
    engine = engine.make_scenario_available("scenario-1")
    engine, snapshot = engine.snapshot("snapshot-1")
    assert engine.hypotheses.entry("hypothesis-1").state is InferenceLifecycleState.SNAPSHOTTED
    assert engine.scenarios.entry("scenario-1").state is InferenceLifecycleState.SNAPSHOTTED
    encoded = snapshot.to_json()
    assert InferenceSnapshot.from_json(encoded) == snapshot
    assert InferenceSnapshot.from_json(encoded).to_json() == encoded
    assert engine.audit().statistics.hypotheses == 1
    assert engine.audit().statistics.scenarios == 1
    assert InferenceDiagnostics().inspect(engine) == ()

    rejected, accepted = engine.try_register_hypothesis(_hypothesis())
    assert not accepted
    assert rejected.audit().statistics.rejections == 1
    assert InferenceDiagnostics().inspect(rejected)
    rejected, accepted = rejected.try_register_scenario(_scenario())
    assert not accepted
    assert len(rejected.rejection_messages) == 2

    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot.from_json(encoded.replace("snapshot-1", "tampered"))
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot.from_json("[]")
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot.from_json("{}")


def test_deserialization_rejects_every_malformed_structural_shape() -> None:
    evidence = EvidenceRegistry().register(_evidence())
    engine = InferenceEngine(evidence).register_hypothesis(_hypothesis())
    engine = engine.make_hypothesis_available("hypothesis-1")
    engine = engine.register_scenario(_scenario())
    engine = engine.make_scenario_available("scenario-1")
    _, snapshot = engine.snapshot("snapshot-invalid-shapes")
    payload = snapshot.to_json()

    malformed = (
        payload.replace('"hypotheses":[', '"hypotheses":{', 1),
        payload.replace('"version":1', '"version":true', 1),
        payload.replace('"ranking_inputs":[]', '"ranking_inputs":[["weight"]]', 1),
        payload.replace('"ranking_inputs":[]', '"ranking_inputs":[true]', 1),
        payload.replace('"confidence":{"level"', '"confidence":true,"unused":{"level"', 1),
        payload.replace('"digest":{"algorithm"', '"digest":[],"unused":{"algorithm"', 1),
    )
    for encoded in malformed:
        with pytest.raises(RelationshipIntegrityError):
            InferenceSnapshot.from_json(encoded)

    valid_ranking = json.loads(payload)
    valid_ranking["scenarios"][0]["value"]["ranking_inputs"] = [["weight", 1.0]]
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot.from_json(json.dumps(valid_ranking))

    boolean_ranking = json.loads(payload)
    boolean_ranking["scenarios"][0]["value"]["ranking_inputs"] = [["weight", True]]
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot.from_json(json.dumps(boolean_ranking))


def test_collections_and_registries_reject_invalid_container_members() -> None:
    hypothesis = _hypothesis()
    scenario = _scenario()
    with pytest.raises(RelationshipIntegrityError):
        InferenceCollection((scenario,))  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        ScenarioCollection([scenario])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        ScenarioCollection((hypothesis,))  # type: ignore[arg-type]

    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry([])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry((object(),))  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry(
            (
                _HypothesisEntry(hypothesis, InferenceLifecycleState.REGISTERED),
                _HypothesisEntry(hypothesis, InferenceLifecycleState.REGISTERED),
            )
        )
    with pytest.raises(RelationshipIntegrityError):
        HypothesisRegistry((_HypothesisEntry(hypothesis, "invalid"),))  # type: ignore[arg-type]

    with pytest.raises(RelationshipIntegrityError):
        ScenarioRegistry([])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        ScenarioRegistry((object(),))  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        ScenarioRegistry(
            (
                _ScenarioEntry(scenario, InferenceLifecycleState.REGISTERED),
                _ScenarioEntry(scenario, InferenceLifecycleState.REGISTERED),
            )
        )
    with pytest.raises(RelationshipIntegrityError):
        ScenarioRegistry((_ScenarioEntry(scenario, "invalid"),))  # type: ignore[arg-type]


def test_validator_rejects_all_invalid_hypothesis_relationships() -> None:
    evidence = EvidenceRegistry().register(_evidence())
    reference = EvidenceReference("evidence-1", 1)
    unknown = EvidenceReference("unknown", 1)
    validator = InferenceValidator()
    invalid = (
        replace(_hypothesis(), evidence=(reference, reference)),
        replace(_hypothesis(), supporting_evidence=(unknown,)),
        replace(_hypothesis(), contradicting_evidence=(unknown,)),
        replace(
            _hypothesis(),
            supporting_evidence=(reference,),
            contradicting_evidence=(reference,),
        ),
    )
    for hypothesis in invalid:
        with pytest.raises(RelationshipIntegrityError):
            validator.validate_hypothesis(hypothesis, evidence)


def test_validator_rejects_all_invalid_scenario_relationships() -> None:
    evidence, hypotheses, scenarios = _registries()
    hypothesis = HypothesisReference("hypothesis-1", 1)
    parent = ScenarioReference("scenario-1", 1)
    evidence_reference = EvidenceReference("evidence-1", 1)
    validator = InferenceValidator()
    self_parent = _scenario("self-parent")
    object.__setattr__(
        self_parent,
        "parent_scenarios",
        (ScenarioReference("self-parent", 1),),
    )
    invalid = (
        replace(_scenario("duplicate-h"), hypotheses=(hypothesis, hypothesis)),
        replace(_scenario("duplicate-p"), parent_scenarios=(parent, parent)),
        self_parent,
        replace(_scenario("unknown-p"), parent_scenarios=(ScenarioReference("missing", 1),)),
        replace(_scenario("unknown-e"), supporting_evidence=(EvidenceReference("missing", 1),)),
        replace(
            _scenario("overlap"),
            supporting_evidence=(evidence_reference,),
            contradicting_evidence=(evidence_reference,),
        ),
        replace(_scenario("digest"), content_digest=DecisionDigest("e" * 64)),
    )
    for scenario in invalid:
        with pytest.raises(RelationshipIntegrityError):
            validator.validate_scenario(scenario, hypotheses, scenarios, evidence)


def test_scenario_registry_errors_and_snapshot_shape_validation() -> None:
    evidence, hypotheses, scenarios = _registries()
    with pytest.raises(RelationshipIntegrityError):
        scenarios.transition("scenario-1", InferenceLifecycleState.ARCHIVED)
    with pytest.raises(KeyError):
        scenarios.entry("missing")

    digest = InferenceDigest.from_value({})
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot("snapshot", 1, [], (), digest)  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot(
            "snapshot",
            1,
            ((_scenario(), InferenceLifecycleState.REGISTERED),),  # type: ignore[arg-type]
            (),
            digest,
        )

    unchanged, snapshot = InferenceEngine(evidence, hypotheses, scenarios).snapshot(
        "registered-snapshot"
    )
    assert unchanged.hypotheses == hypotheses
    assert unchanged.scenarios == scenarios
    assert snapshot.hypotheses[0][1] is InferenceLifecycleState.REGISTERED
    assert snapshot.scenarios[0][1] is InferenceLifecycleState.REGISTERED
    with pytest.raises(RelationshipIntegrityError):
        InferenceSnapshot(
            "snapshot",
            1,
            (),
            ((_hypothesis(), InferenceLifecycleState.REGISTERED),),  # type: ignore[arg-type]
            digest,
        )


def test_diagnostics_report_corrupt_hypothesis_and_scenario_entries() -> None:
    evidence, _hypotheses, _scenarios = _registries()
    bad_hypothesis = replace(_hypothesis(), content_digest=DecisionDigest("a" * 64))
    bad_scenario = replace(_scenario(), content_digest=DecisionDigest("b" * 64))
    corrupt_hypotheses = object.__new__(HypothesisRegistry)
    object.__setattr__(
        corrupt_hypotheses,
        "entries",
        (_HypothesisEntry(bad_hypothesis, InferenceLifecycleState.REGISTERED),),
    )
    corrupt_scenarios = object.__new__(ScenarioRegistry)
    object.__setattr__(
        corrupt_scenarios,
        "entries",
        (_ScenarioEntry(bad_scenario, InferenceLifecycleState.REGISTERED),),
    )
    engine = InferenceEngine(evidence, corrupt_hypotheses, corrupt_scenarios)
    issues = InferenceDiagnostics().inspect(engine)
    assert len(issues) == 2
    assert "hypothesis-1" in issues[0]
    assert "scenario-1" in issues[1]
