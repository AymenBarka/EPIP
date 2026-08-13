"""Acceptance tests for the EPIP-016 immutable decision vocabulary."""

from dataclasses import FrozenInstanceError, is_dataclass
from typing import Any, cast

import pytest

from epip.core.integrity import (
    DataIntegrityError,
    MissingFieldError,
    RelationshipIntegrityError,
)
from epip.decision import domain as d


def metadata() -> d.DecisionMetadata:
    return d.DecisionMetadata(1, "2026-08-11T00:00:00Z", "test")


def digest() -> d.DecisionDigest:
    return d.DecisionDigest("a" * 64)


def confidence() -> d.Confidence:
    return d.Confidence(0.8, d.ConfidenceLevel.HIGH)


def quality() -> d.Quality:
    return d.Quality(0.9, d.QualityLevel.VERY_HIGH)


def validity() -> d.Validity:
    return d.Validity(1.0, d.ValidityLevel.VALID)


def uncertainty() -> d.Uncertainty:
    return d.Uncertainty(0.2)


def evidence() -> d.Evidence:
    return d.Evidence(
        "e1",
        d.EvidenceCategory.MARKET_DATA,
        "feed",
        1,
        (("price", "1.2"),),
        confidence(),
        quality(),
        validity(),
        uncertainty(),
        (),
        metadata(),
        digest(),
    )


def hypothesis() -> d.Hypothesis:
    ref = d.EvidenceReference("e1")
    return d.Hypothesis(
        "h1",
        d.HypothesisCategory.DIRECTIONAL,
        (ref,),
        (ref,),
        (),
        ("trend",),
        ("break",),
        confidence(),
        quality(),
        validity(),
        uncertainty(),
        metadata(),
        digest(),
    )


def scenario() -> d.Scenario:
    return d.Scenario(
        "s1",
        d.ScenarioCategory.BULLISH,
        (d.HypothesisReference("h1"),),
        (),
        (d.EvidenceReference("e1"),),
        (),
        ("liquid",),
        ("break",),
        (("score", 0.8),),
        confidence(),
        quality(),
        validity(),
        uncertainty(),
        metadata(),
        digest(),
    )


def candidate() -> d.DecisionCandidate:
    return d.DecisionCandidate(
        "c1",
        d.CandidateType.LONG,
        ("trend",),
        (d.EvidenceReference("e1"),),
        (d.HypothesisReference("h1"),),
        (d.ScenarioReference("s1"),),
        (d.ConstraintEvaluation("risk", d.ConstraintType.RISK, True, True, "ok"),),
        confidence(),
        quality(),
        validity(),
        uncertainty(),
        d.DecisionPriority.HIGH,
        ("break",),
        metadata(),
        digest(),
    )


def decision() -> d.Decision:
    reason = d.DecisionReason("R1", "supported", (d.EvidenceReference("e1"),))
    recommendation = d.Recommendation(
        "r1",
        d.RecommendationType.EXECUTE,
        d.CandidateReference("c1"),
        (reason,),
        confidence(),
        metadata(),
        digest(),
    )
    explanation = d.DecisionExplanation(
        d.ExplanationLevel.AUDIT,
        (d.EvidenceReference("e1"),),
        (),
        (d.HypothesisReference("h1"),),
        (),
        (d.ScenarioReference("s1"),),
        (),
        (d.DecisionAlternative(d.CandidateReference("c2"), "weaker"),),
        (reason,),
        uncertainty(),
    )
    return d.Decision(
        "d1",
        d.DecisionType.ENTER,
        d.DecisionStatus.APPROVED,
        d.DecisionPriority.HIGH,
        d.CandidateReference("c1"),
        recommendation,
        explanation,
        d.DecisionContext("EURUSD", "H1", "corr-1"),
        metadata(),
        digest(),
    )


def test_complete_model_is_immutable_canonical_and_deterministic() -> None:
    objects = [evidence(), hypothesis(), scenario(), candidate(), decision()]
    snapshot = d.DecisionSnapshot("snap-1", decision(), metadata(), digest())
    objects.append(snapshot)
    for value in objects:
        assert is_dataclass(value)
        assert hash(value) == hash(value)
        assert value.to_json() == value.to_json()
        assert len(value.deterministic_digest()) == 64
        with pytest.raises(FrozenInstanceError):
            cast(Any, value).content_digest = digest()
    assert decision() == decision()
    assert decision() != object()
    assert decision() != snapshot


@pytest.mark.parametrize(
    "factory",
    [
        lambda: d.Confidence(-0.1, d.ConfidenceLevel.LOW),
        lambda: d.Quality(1.1, d.QualityLevel.HIGH),
        lambda: d.Validity(2.0, d.ValidityLevel.VALID),
        lambda: d.Uncertainty(float("nan")),
    ],
)
def test_scores_reject_invalid_ranges(factory: object) -> None:
    with pytest.raises(DataIntegrityError):
        factory()  # type: ignore[operator]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: d.EvidenceReference(""),
        lambda: d.DecisionMetadata(0, "t", "s"),
        lambda: d.DecisionContext("", "H1", "c"),
        lambda: d.DecisionDigest("a" * 63),
        lambda: d.DecisionDigest("z" * 64),
        lambda: d.DecisionDigest("G" * 64),
        lambda: d.DecisionDigest("A" * 64),
    ],
)
def test_invalid_primitives_fail_fast(factory: object) -> None:
    with pytest.raises(DataIntegrityError):
        factory()  # type: ignore[operator]


def test_relationships_and_collections_are_validated() -> None:
    ref = d.EvidenceReference("e1")
    with pytest.raises(RelationshipIntegrityError):
        d.Hypothesis(
            "h",
            d.HypothesisCategory.DIRECTIONAL,
            (),
            (),
            (),
            (),
            (),
            confidence(),
            quality(),
            validity(),
            uncertainty(),
            metadata(),
            digest(),
        )
    with pytest.raises(RelationshipIntegrityError):
        d.Scenario(
            "s",
            d.ScenarioCategory.NEUTRAL,
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            confidence(),
            quality(),
            validity(),
            uncertainty(),
            metadata(),
            digest(),
        )
    with pytest.raises(RelationshipIntegrityError):
        d.Scenario(
            "s",
            d.ScenarioCategory.NEUTRAL,
            (d.HypothesisReference("h"),),
            (d.ScenarioReference("s"),),
            (),
            (),
            (),
            (),
            (),
            confidence(),
            quality(),
            validity(),
            uncertainty(),
            metadata(),
            digest(),
        )
    with pytest.raises(RelationshipIntegrityError):
        d.Recommendation(
            "r",
            d.RecommendationType.WAIT,
            d.CandidateReference("c"),
            (),
            confidence(),
            metadata(),
            digest(),
        )
    with pytest.raises(RelationshipIntegrityError):
        d.DecisionReason("r", "m", [ref])  # type: ignore[arg-type]
    bad = evidence()
    with pytest.raises(RelationshipIntegrityError):
        d.Evidence(bad.evidence_id, bad.category, bad.source, 1, [("x", "y")], bad.confidence, bad.quality, bad.validity, bad.uncertainty, (), bad.metadata, bad.content_digest)  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        d.Evidence("e", d.EvidenceCategory.MARKET_DATA, "s", 1, (("x",),), confidence(), quality(), validity(), uncertainty(), (), metadata(), digest())  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        d.Evidence(
            "e",
            d.EvidenceCategory.MARKET_DATA,
            "s",
            1,
            (),
            confidence(),
            quality(),
            validity(),
            uncertainty(),
            ("",),
            metadata(),
            digest(),
        )


def test_all_public_enums_and_protocols_are_complete() -> None:
    for name in d.__all__:
        assert getattr(d, name) is not None
    assert d.DecisionType.ENTER.value == "enter"
