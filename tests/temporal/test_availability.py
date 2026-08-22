"""Component tests for A05-E02 deterministic availability analysis."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from inspect import signature
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.evidence.candidates import CandidateDiagnostics
from epip.evidence.model import (
    AssumptionMetadata,
    CompletenessMetadata,
    DispositionAxis,
    EvidenceClaim,
    ProvenanceReference,
    QualityMetadata,
    SemanticBoundary,
    SemanticIdentity,
    SemanticState,
    ValidityMetadata,
)
from epip.governance import GovernanceEpoch, RegistryEntry
from epip.temporal.availability import (
    AvailabilityAnalyzer,
    AvailabilityDecision,
    AvailabilityDiagnostics,
    AvailabilityPolicy,
    AvailabilityStatus,
)
from epip.temporal.model import (
    CanonicalInstant,
    CanonicalInterval,
    TemporalAuthorityReference,
    TemporalBoundary,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.timeframe import CanonicalTimeframe, SessionInclusionPolicy


def _instant(value: int = 150, **changes: object) -> CanonicalInstant:
    values: dict[str, object] = {
        "value": value,
        "precision": "second",
        "time_scale": "UTC",
        "timezone_basis": "UTC",
        "authority_identity": "clock-1",
    }
    values.update(changes)
    return CanonicalInstant(**values)  # type: ignore[arg-type]


def _authority(
    role: str,
    identity: str | None = None,
    epoch: int = 5,
) -> TemporalAuthorityReference:
    return TemporalAuthorityReference(
        identity or role,
        role,
        "1.0.0",
        GovernanceEpoch(epoch),
    )


def _authorities() -> tuple[TemporalAuthorityReference, ...]:
    return (
        _authority("source_authority"),
        _authority("source_boundary_admission_authority"),
        _authority("semantic_planning_authority"),
    )


def _claim(**changes: object) -> EvidenceClaim:
    values: dict[str, object] = {
        "evidence_id": "artifact-1",
        "identity": SemanticIdentity("market.structure", "1.0.0", "EURUSD", "H1"),
        "source_identity": "producer-1",
        "implementation_version": "1.0.0",
        "boundary": SemanticBoundary("EURUSD", "H1", "closed", "boundary-1"),
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
        "content_identity": "content-1",
        "disposition": DispositionAxis.ACCEPTED,
    }
    values.update(changes)
    return EvidenceClaim(**values)  # type: ignore[arg-type]


def _entry(**changes: object) -> RegistryEntry:
    values: dict[str, object] = {
        "producer_identity": "producer-1",
        "producer_version": "1.0.0",
        "descriptor_reference": "descriptor-1",
        "owner_identity": "owner-1",
        "producer_contract_version": "1.0.0",
        "implementation_identity": "build-1",
        "capability_references": (("market.structure", "1.0.0"),),
        "trust_standing": "Trusted",
        "certification_records": (),
        "compatibility_decisions": (),
        "lifecycle_standing": "Enabled",
        "governance_provenance": ("admission-1",),
    }
    values.update(changes)
    return RegistryEntry(**values)  # type: ignore[arg-type]


def _governance(entries: tuple[RegistryEntry, ...] | None = None) -> CandidateDiagnostics:
    return CandidateDiagnostics(
        "snapshot-1",
        "manifest-1",
        GovernanceEpoch(5),
        (_entry(),) if entries is None else entries,
        (),
    )


def _boundary(**changes: object) -> TemporalBoundary:
    values: dict[str, object] = {
        "boundary_identity": "boundary-1",
        "observation": _instant(50),
        "validity": CanonicalInterval(_instant(0), _instant(200)),
        "validity_rule_reference": None,
        "publication": _instant(100),
        "availability": _instant(120),
        "knowledge": _instant(150),
        "revision": None,
        "expiration": None,
        "non_expiring_policy": "non-expiring-1",
        "historical": None,
        "replay": None,
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "revision_lineage": ("publication-1",),
        "visibility_constraints": ("admitted",),
        "policy_versions": (("availability", "1.0.0"),),
        "authorities": _authorities(),
    }
    values.update(changes)
    return TemporalBoundary(**values)  # type: ignore[arg-type]


def _policy(**changes: object) -> AvailabilityPolicy:
    values: dict[str, object] = {
        "policy_identity": "availability-policy",
        "policy_version": "1.0.0",
        "use_identity": "consumer-use-1",
        "use_time": _instant(60),
        "freshness_boundary": _instant(40),
        "expected_availability": _instant(130),
        "obsolescence_boundary": None,
        "replacement_identity": None,
        "authority": _authority("semantic_planning_authority"),
    }
    values.update(changes)
    return AvailabilityPolicy(**values)  # type: ignore[arg-type]


def _timeframe(**changes: object) -> CanonicalTimeframe:
    values: dict[str, object] = {
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "interval": CanonicalInterval(_instant(0), _instant(60)),
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "session_policy": SessionInclusionPolicy.ALL_CANONICAL_TIME,
        "calendar_fact_identities": (),
        "authority": _authority("temporal_architecture_authority"),
        "policy_version": "timeframe-policy-1",
    }
    values.update(changes)
    return CanonicalTimeframe(**values)  # type: ignore[arg-type]


def _decision(**changes: object) -> AvailabilityDecision:
    values: dict[str, object] = {
        "artifact_identity": "artifact-1",
        "publication_identity": "artifact-1",
        "content_identity": "content-1",
        "producer_identity": "producer-1",
        "producer_version": "1.0.0",
        "implementation_identity": "build-1",
        "governance_snapshot_identity": "snapshot-1",
        "governance_manifest_reference": "manifest-1",
        "governance_epoch": GovernanceEpoch(5),
        "boundary_identity": "boundary-1",
        "use_identity": "consumer-use-1",
        "publication_time": _instant(100),
        "availability_time": _instant(120),
        "knowledge_boundary": _instant(150),
        "observation_time": _instant(50),
        "use_time": _instant(60),
        "status": AvailabilityStatus.VISIBLE,
        "visible": True,
        "provisionally_temporally_eligible": True,
        "late": False,
        "stale": False,
        "expired": False,
        "obsolete": False,
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "authority_identities": (
            "source_authority",
            "source_boundary_admission_authority",
            "semantic_planning_authority",
        ),
        "policy_identity": "availability-policy",
        "policy_version": "1.0.0",
        "replacement_identity": None,
        "validity": CanonicalInterval(_instant(0), _instant(200)),
        "validity_rule_reference": None,
        "expiration_time": None,
        "non_expiring_policy": "non-expiring-1",
        "freshness_boundary": _instant(40),
        "expected_availability": _instant(130),
        "obsolescence_boundary": None,
        "revision_lineage": ("publication-1",),
        "visibility_constraints": ("admitted",),
        "authority_facts": tuple(
            (
                authority.authority_role,
                authority.authority_identity,
                authority.authority_version,
                authority.governance_epoch,
            )
            for authority in (*_authorities(), _authority("semantic_planning_authority"))
        ),
    }
    values.update(changes)
    return AvailabilityDecision(**values)  # type: ignore[arg-type]


def _reason(
    code: TemporalDiagnosticCode = TemporalDiagnosticCode.LATE_ARRIVAL,
    reason: str = "late",
    **changes: object,
) -> TemporalDiagnosticReason:
    values: dict[str, object] = {
        "code": code,
        "affected_evidence": "artifact-1",
        "source_boundary": "boundary-1",
        "consumer_boundary": "consumer-use-1",
        "timeframe_identity": "M1",
        "calendar_identity": "calendar-xpar",
        "knowledge_boundary": _instant(150),
        "revision_lineage": ("publication-1",),
        "policy_version": "1.0.0",
        "reason": reason,
    }
    values.update(changes)
    return TemporalDiagnosticReason(**values)  # type: ignore[arg-type]


def _evaluate(
    boundary: TemporalBoundary | None = None,
    policy: AvailabilityPolicy | None = None,
    timeframe: CanonicalTimeframe | None = None,
) -> AvailabilityDiagnostics:
    return AvailabilityAnalyzer.evaluate(
        _claim(),
        boundary or _boundary(),
        policy or _policy(),
        _governance(),
        _timeframe() if timeframe is None else timeframe,
    )


def test_public_production_inventory_is_exact() -> None:
    from epip.temporal import availability

    public = {
        name
        for name, value in vars(availability).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and value.__module__ == availability.__name__
    }
    assert public == {
        "AvailabilityAnalyzer",
        "AvailabilityDecision",
        "AvailabilityDiagnostics",
        "AvailabilityPolicy",
        "AvailabilityStatus",
    }


def test_visibility_and_provisional_temporal_eligibility_are_independently_preserved() -> None:
    result = _evaluate()
    decision = result.decisions[0]
    assert decision.status is AvailabilityStatus.VISIBLE
    assert decision.visible is True
    assert decision.provisionally_temporally_eligible is True
    assert decision.publication_time == _instant(100)
    assert decision.availability_time == _instant(120)
    assert decision.knowledge_boundary == _instant(150)
    assert result.reasons == ()


def test_e02_never_produces_final_usability() -> None:
    results = (
        _evaluate(),
        _evaluate(_boundary(availability=_instant(160))),
        _evaluate(policy=_policy(freshness_boundary=_instant(51))),
        _evaluate(_boundary(expiration=_instant(140), non_expiring_policy=None)),
        _evaluate(
            policy=_policy(
                obsolescence_boundary=_instant(140),
                replacement_identity="artifact-2",
            )
        ),
    )
    assert all(
        decision.status is not AvailabilityStatus.USABLE
        for result in results
        for decision in result.decisions
    )
    with pytest.raises(DataIntegrityError, match="status is inconsistent"):
        _decision(status=AvailabilityStatus.USABLE)


def test_successor_owned_facts_are_not_e02_inputs_or_outputs() -> None:
    assert tuple(signature(AvailabilityAnalyzer.evaluate).parameters) == (
        "publication",
        "boundary",
        "policy",
        "governance",
        "timeframe",
    )
    decision = _evaluate().decisions[0]
    for successor_fact in (
        "completeness",
        "temporal_compatibility",
        "dependency_validation",
        "revision_validation",
        "final_usability",
    ):
        assert not hasattr(decision, successor_fact)


def test_governance_candidate_permutations_preserve_provisional_outcome() -> None:
    admitted = _entry()
    unrelated = _entry(
        producer_identity="producer-2",
        producer_version="2.0.0",
        implementation_identity="build-2",
    )
    outcomes = tuple(
        AvailabilityAnalyzer.evaluate(
            _claim(),
            _boundary(),
            _policy(),
            _governance(permutation),
            _timeframe(),
        )
        for permutation in permutations((admitted, unrelated))
    )
    assert all(outcome == outcomes[0] for outcome in outcomes)
    assert all(hash(outcome) == hash(outcomes[0]) for outcome in outcomes)


def test_not_visible_when_publication_or_availability_exceeds_knowledge() -> None:
    for boundary in (
        _boundary(publication=_instant(160), availability=_instant(170)),
        _boundary(availability=_instant(160)),
    ):
        decision = _evaluate(boundary).decisions[0]
        assert decision.status is AvailabilityStatus.NOT_VISIBLE
        assert decision.visible is False
        assert decision.provisionally_temporally_eligible is False


def test_late_arrival_is_diagnostic_and_never_changes_observation_time() -> None:
    boundary = _boundary(observation=CanonicalInterval(_instant(40), _instant(60)))
    result = _evaluate(boundary, _policy(expected_availability=_instant(110)))
    decision = result.decisions[0]
    assert decision.status is AvailabilityStatus.VISIBLE
    assert decision.late is True
    assert decision.observation_time == boundary.observation
    assert tuple(item.code for item in result.reasons) == (TemporalDiagnosticCode.LATE_ARRIVAL,)


def test_stale_uses_only_explicit_freshness_boundary() -> None:
    result = _evaluate(policy=_policy(freshness_boundary=_instant(51)))
    decision = result.decisions[0]
    assert decision.status is AvailabilityStatus.STALE
    assert decision.stale is True and decision.provisionally_temporally_eligible is False
    assert tuple(item.code for item in result.reasons) == (TemporalDiagnosticCode.STALE_EVIDENCE,)


def test_expiration_uses_only_explicit_boundary() -> None:
    boundary = _boundary(
        expiration=_instant(140),
        non_expiring_policy=None,
    )
    result = _evaluate(boundary)
    decision = result.decisions[0]
    assert decision.status is AvailabilityStatus.EXPIRED
    assert decision.expired is True and decision.provisionally_temporally_eligible is False
    assert tuple(item.code for item in result.reasons) == (TemporalDiagnosticCode.EXPIRED_EVIDENCE,)


def test_non_expiring_policy_never_uses_ambient_time() -> None:
    first = _evaluate()
    second = _evaluate()
    assert first == second and hash(first) == hash(second)
    assert first.decisions[0].expired is False


def test_obsolescence_requires_explicit_boundary_and_replacement() -> None:
    policy = _policy(
        obsolescence_boundary=_instant(140),
        replacement_identity="artifact-2",
    )
    result = _evaluate(policy=policy)
    decision = result.decisions[0]
    assert decision.status is AvailabilityStatus.OBSOLETE
    assert decision.obsolete is True
    assert decision.replacement_identity == "artifact-2"
    assert result.reasons == ()


def test_future_obsolescence_does_not_affect_frozen_plan() -> None:
    result = _evaluate(
        policy=_policy(
            obsolescence_boundary=_instant(200),
            replacement_identity="artifact-2",
        )
    )
    assert result.decisions[0].status is AvailabilityStatus.VISIBLE
    assert result.decisions[0].replacement_identity is None


def test_expired_status_has_priority_over_obsolete_and_stale() -> None:
    boundary = _boundary(expiration=_instant(140), non_expiring_policy=None)
    policy = _policy(
        freshness_boundary=_instant(51),
        obsolescence_boundary=_instant(140),
        replacement_identity="artifact-2",
    )
    decision = _evaluate(boundary, policy).decisions[0]
    assert decision.status is AvailabilityStatus.EXPIRED
    assert decision.stale and decision.expired and decision.obsolete


def test_obsolete_status_has_priority_over_stale() -> None:
    policy = _policy(
        freshness_boundary=_instant(51),
        obsolescence_boundary=_instant(140),
        replacement_identity="artifact-2",
    )
    decision = _evaluate(policy=policy).decisions[0]
    assert decision.status is AvailabilityStatus.OBSOLETE


def test_visible_but_not_provisionally_eligible_when_validity_is_not_satisfied() -> None:
    no_rule_result = _evaluate(
        _boundary(validity=None, validity_rule_reference="uninterpreted-validity-rule")
    )
    outside_result = _evaluate(policy=_policy(use_time=_instant(250)))
    for result in (no_rule_result, outside_result):
        decision = result.decisions[0]
        assert decision.status is AvailabilityStatus.VISIBLE
        assert decision.visible is True
        assert decision.provisionally_temporally_eligible is False
        assert tuple(item.code for item in result.reasons) == (
            TemporalDiagnosticCode.MISSING_VALIDITY_TIME,
        )


def test_unscoped_boundary_is_supported_without_timeframe() -> None:
    boundary = _boundary(
        timeframe_identity=None,
        timeframe_version=None,
        calendar_identity=None,
        calendar_version=None,
    )
    result = AvailabilityAnalyzer.evaluate(_claim(), boundary, _policy(), _governance())
    assert result.decisions[0].timeframe_identity is None


def test_e01_timeframe_context_is_preserved() -> None:
    decision = _evaluate().decisions[0]
    assert decision.timeframe_identity == "M1"
    assert decision.timeframe_version == "1.0.0"
    assert decision.calendar_identity == "calendar-xpar"
    assert decision.calendar_version == "2026.1"


@pytest.mark.parametrize(
    "changes",
    [
        {"policy_identity": ""},
        {"policy_version": ""},
        {"use_identity": ""},
        {"use_time": cast(Any, object())},
        {"freshness_boundary": cast(Any, object())},
        {"expected_availability": cast(Any, object())},
        {"obsolescence_boundary": cast(Any, object())},
        {"replacement_identity": ""},
        {"obsolescence_boundary": _instant(140), "replacement_identity": None},
        {"obsolescence_boundary": None, "replacement_identity": "artifact-2"},
        {"authority": cast(Any, object())},
        {"authority": _authority("calendar_authority")},
    ],
)
def test_policy_rejects_invalid_or_incomplete_facts(changes: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, _policy)(**changes)


def test_evaluate_rejects_invalid_top_level_inputs() -> None:
    with pytest.raises(DataIntegrityError):
        AvailabilityAnalyzer.evaluate(cast(Any, ""), _boundary(), _policy(), _governance())
    with pytest.raises(DataIntegrityError, match="TemporalBoundary"):
        AvailabilityAnalyzer.evaluate(_claim(), cast(Any, object()), _policy(), _governance())
    with pytest.raises(DataIntegrityError, match="policy must be immutable"):
        AvailabilityAnalyzer.evaluate(_claim(), _boundary(), cast(Any, object()), _governance())
    with pytest.raises(DataIntegrityError, match="CanonicalTimeframe"):
        AvailabilityAnalyzer.evaluate(
            _claim(), _boundary(), _policy(), _governance(), cast(Any, object())
        )


def test_inferred_publication_identity_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="MISSING_PUBLICATION_TIME"):
        AvailabilityAnalyzer.evaluate(
            cast(Any, "revision-lineage-value"), _boundary(), _policy(), _governance(), _timeframe()
        )


def test_authority_and_governance_epoch_fail_closed() -> None:
    missing_role = _boundary(authorities=(_authority("source_authority"),))
    with pytest.raises(DataIntegrityError, match="HISTORICAL_AMBIGUITY"):
        _evaluate(missing_role)
    with pytest.raises(DataIntegrityError, match="governance epoch"):
        _evaluate(policy=_policy(authority=_authority("semantic_planning_authority", epoch=6)))
    with pytest.raises(DataIntegrityError, match="governance and trust outcome"):
        AvailabilityAnalyzer.evaluate(
            _claim(), _boundary(), _policy(), cast(Any, None), _timeframe()
        )
    with pytest.raises(DataIntegrityError, match="admitted governance and trust outcome"):
        AvailabilityAnalyzer.evaluate(
            _claim(), _boundary(), _policy(), _governance(()), _timeframe()
        )


def test_missing_governance_and_trust_outcomes_fail_closed_independently() -> None:
    with pytest.raises(DataIntegrityError, match="governance and trust outcome"):
        AvailabilityAnalyzer.evaluate(
            _claim(), _boundary(), _policy(), cast(Any, None), _timeframe()
        )
    with pytest.raises(DataIntegrityError, match="admitted governance and trust outcome"):
        AvailabilityAnalyzer.evaluate(
            _claim(), _boundary(), _policy(), _governance(()), _timeframe()
        )


def test_decision_independently_preserves_complete_classification_context() -> None:
    boundary = _boundary()
    policy = _policy()
    result = AvailabilityAnalyzer.evaluate(_claim(), boundary, policy, _governance(), _timeframe())
    decision = result.decisions[0]
    assert (
        decision.publication_identity,
        decision.content_identity,
        decision.producer_identity,
        decision.producer_version,
        decision.implementation_identity,
    ) == ("artifact-1", "content-1", "producer-1", "1.0.0", "build-1")
    assert (
        decision.governance_snapshot_identity,
        decision.governance_manifest_reference,
        decision.governance_epoch,
    ) == ("snapshot-1", "manifest-1", GovernanceEpoch(5))
    assert decision.validity == boundary.validity
    assert decision.non_expiring_policy == boundary.non_expiring_policy
    assert decision.freshness_boundary == policy.freshness_boundary
    assert decision.expected_availability == policy.expected_availability
    assert decision.revision_lineage == boundary.revision_lineage
    assert decision.visibility_constraints == boundary.visibility_constraints
    assert decision.authority_facts


def test_every_diagnostic_is_attributable_to_the_evaluated_decision() -> None:
    result = _evaluate(policy=_policy(expected_availability=_instant(110)))
    decision = result.decisions[0]
    assert result.reasons
    for reason in result.reasons:
        assert reason.affected_evidence == decision.publication_identity
        assert reason.source_boundary == decision.boundary_identity
        assert reason.consumer_boundary == decision.use_identity
        assert reason.knowledge_boundary == decision.knowledge_boundary
        assert reason.policy_version == decision.policy_version


def test_timeframe_scope_fails_closed_when_missing_extra_or_incompatible() -> None:
    with pytest.raises(DataIntegrityError, match="MISSING_TIMEFRAME"):
        AvailabilityAnalyzer.evaluate(_claim(), _boundary(), _policy(), _governance())
    unscoped = _boundary(
        timeframe_identity=None,
        timeframe_version=None,
        calendar_identity=None,
        calendar_version=None,
    )
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_TIMEFRAME"):
        AvailabilityAnalyzer.evaluate(_claim(), unscoped, _policy(), _governance(), _timeframe())
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_TIMEFRAME"):
        _evaluate(timeframe=_timeframe(timeframe_identity="M5"))


def test_incompatible_canonical_bases_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="INVALID_PRECISION"):
        _evaluate(_boundary(availability=_instant(120, precision="nanosecond")))
    with pytest.raises(DataIntegrityError, match="INVALID_PRECISION"):
        _evaluate(policy=_policy(freshness_boundary=_instant(40, time_scale="TAI")))
    with pytest.raises(DataIntegrityError, match="INVALID_PRECISION"):
        _evaluate(
            _boundary(
                validity=CanonicalInterval(
                    _instant(0, precision="nanosecond"),
                    _instant(200, precision="nanosecond"),
                )
            )
        )


def test_distinct_source_authorities_do_not_change_the_canonical_time_basis() -> None:
    boundary = _boundary(
        publication=_instant(100, authority_identity="publication-clock-authority"),
        availability=_instant(120, authority_identity="admission-clock-authority"),
        knowledge=_instant(150, authority_identity="planning-clock-authority"),
    )
    decision = _evaluate(boundary).decisions[0]
    assert decision.status is AvailabilityStatus.VISIBLE


def test_availability_before_publication_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="FUTURE_LEAKAGE"):
        _evaluate(_boundary(publication=_instant(120), availability=_instant(100)))


@pytest.mark.parametrize(
    "changes",
    [
        {"artifact_identity": ""},
        {"publication_identity": ""},
        {"content_identity": ""},
        {"producer_identity": ""},
        {"producer_version": ""},
        {"implementation_identity": ""},
        {"governance_snapshot_identity": ""},
        {"governance_manifest_reference": ""},
        {"governance_epoch": cast(Any, 5)},
        {"boundary_identity": ""},
        {"use_identity": ""},
        {"policy_identity": ""},
        {"policy_version": ""},
        {"publication_time": cast(Any, object())},
        {"availability_time": cast(Any, object())},
        {"knowledge_boundary": cast(Any, object())},
        {"use_time": cast(Any, object())},
        {"observation_time": cast(Any, object())},
        {"status": cast(Any, "USABLE")},
        {"visible": cast(Any, 1)},
        {"provisionally_temporally_eligible": cast(Any, 1)},
        {"late": cast(Any, 1)},
        {"stale": cast(Any, 1)},
        {"expired": cast(Any, 1)},
        {"obsolete": cast(Any, 1)},
        {"timeframe_identity": ""},
        {"timeframe_version": ""},
        {"timeframe_version": None},
        {"calendar_identity": ""},
        {"calendar_version": ""},
        {"calendar_version": None},
        {"authority_identities": cast(Any, [])},
        {"authority_identities": ()},
        {"authority_identities": ("",)},
        {"authority_identities": ("source", "source")},
        {"replacement_identity": ""},
        {"validity": cast(Any, object())},
        {"validity_rule_reference": ""},
        {"expiration_time": cast(Any, object())},
        {"non_expiring_policy": ""},
        {"freshness_boundary": cast(Any, object())},
        {"expected_availability": cast(Any, object())},
        {"obsolescence_boundary": cast(Any, object())},
        {"revision_lineage": cast(Any, [])},
        {"revision_lineage": ("",)},
        {"visibility_constraints": cast(Any, [])},
        {"visibility_constraints": ("",)},
        {"authority_facts": cast(Any, [])},
        {"authority_facts": ()},
        {"authority_facts": (cast(Any, ("role", "identity")),)},
        {"authority_facts": (("", "identity", "1.0.0", GovernanceEpoch(5)),)},
        {
            "visible": False,
            "provisionally_temporally_eligible": True,
            "status": AvailabilityStatus.NOT_VISIBLE,
        },
    ],
)
def test_decision_rejects_invalid_or_inconsistent_context(changes: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _decision(**changes)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        (
            {
                "status": AvailabilityStatus.NOT_VISIBLE,
                "visible": False,
                "provisionally_temporally_eligible": False,
            },
            AvailabilityStatus.NOT_VISIBLE,
        ),
        (
            {
                "status": AvailabilityStatus.EXPIRED,
                "provisionally_temporally_eligible": False,
                "expired": True,
            },
            AvailabilityStatus.EXPIRED,
        ),
        (
            {
                "status": AvailabilityStatus.OBSOLETE,
                "provisionally_temporally_eligible": False,
                "obsolete": True,
            },
            AvailabilityStatus.OBSOLETE,
        ),
        (
            {
                "status": AvailabilityStatus.STALE,
                "provisionally_temporally_eligible": False,
                "stale": True,
            },
            AvailabilityStatus.STALE,
        ),
        (
            {
                "status": AvailabilityStatus.VISIBLE,
                "provisionally_temporally_eligible": False,
            },
            AvailabilityStatus.VISIBLE,
        ),
    ],
)
def test_decision_accepts_each_independent_status(
    changes: dict[str, object], expected: AvailabilityStatus
) -> None:
    assert _decision(**changes).status is expected


def test_decision_canonicalizes_authority_permutations() -> None:
    identities = _decision().authority_identities
    expected = _decision(authority_identities=identities)
    for permutation in permutations(identities):
        actual = _decision(authority_identities=permutation)
        assert actual == expected and hash(actual) == hash(expected)


def test_diagnostics_are_immutable_hashable_and_permutation_invariant() -> None:
    decisions = (_decision(), _decision(artifact_identity="artifact-2"))
    reasons = (
        _reason(),
        _reason(TemporalDiagnosticCode.STALE_EVIDENCE, "stale", affected_evidence="artifact-2"),
    )
    expected = AvailabilityDiagnostics(decisions, reasons)
    actual = AvailabilityDiagnostics(tuple(reversed(decisions)), tuple(reversed(reasons)))
    assert actual == expected and hash(actual) == hash(expected)
    with pytest.raises(FrozenInstanceError):
        actual.reasons = ()


def test_equal_code_diagnostic_pairs_are_canonical() -> None:
    code = TemporalDiagnosticCode.LATE_ARRIVAL
    expected = AvailabilityDiagnostics((), (_reason(code, "alpha"), _reason(code, "beta")))
    actual = AvailabilityDiagnostics((), (_reason(code, "beta"), _reason(code, "alpha")))
    assert actual == expected and hash(actual) == hash(expected)
    assert tuple(item.reason for item in actual.reasons) == ("alpha", "beta")


@pytest.mark.parametrize(
    "call",
    [
        lambda: AvailabilityDiagnostics(cast(Any, [])),
        lambda: AvailabilityDiagnostics((cast(Any, object()),)),
        lambda: AvailabilityDiagnostics((), cast(Any, [])),
        lambda: AvailabilityDiagnostics((), (cast(Any, "LATE"),)),
        lambda: AvailabilityDiagnostics((_decision(), _decision())),
    ],
)
def test_diagnostics_reject_invalid_or_duplicate_context(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_interval_observation_participates_in_total_decision_ordering() -> None:
    instant = _decision()
    interval = _decision(
        artifact_identity="artifact-2",
        observation_time=CanonicalInterval(_instant(40), _instant(50)),
    )
    expected = AvailabilityDiagnostics((instant, interval))
    actual = AvailabilityDiagnostics((interval, instant))
    assert actual == expected and hash(actual) == hash(expected)


def test_outputs_are_immutable_equal_hashable_and_repeatedly_deterministic() -> None:
    policy = _policy()
    decision = _decision()
    diagnostics = AvailabilityDiagnostics((decision,))
    values: tuple[object, ...] = (policy, decision, diagnostics)
    assert all(hash(item) for item in values)
    assert policy != object()
    for item in values:
        with pytest.raises(FrozenInstanceError):
            cast(Any, item).policy_version = "changed"
    results = tuple(_evaluate() for _ in range(5))
    assert all(item == results[0] for item in results)
    assert all(hash(item) == hash(results[0]) for item in results)


def test_predecessor_inputs_remain_unchanged() -> None:
    boundary = _boundary()
    policy = _policy()
    timeframe = _timeframe()
    publication = _claim()
    governance = _governance()
    before = (
        hash(boundary),
        hash(policy),
        hash(timeframe),
        hash(publication),
        hash(governance),
    )
    AvailabilityAnalyzer.evaluate(publication, boundary, policy, governance, timeframe)
    assert before == (
        hash(boundary),
        hash(policy),
        hash(timeframe),
        hash(publication),
        hash(governance),
    )


def test_e02_contains_no_successor_or_unallocated_behaviour() -> None:
    from epip.temporal import availability

    forbidden = {
        "ObservationValidator",
        "CompletenessValidator",
        "RevisionValidator",
        "TemporalDependencyValidator",
        "ReplayCompatibilityValidator",
        "TemporalCertification",
        "TemporalClosure",
        "ProviderExecutor",
        "DependencyGraphBuilder",
    }
    assert forbidden.isdisjoint(vars(availability))
