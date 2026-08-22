"""Component tests for A05-E04 deterministic completeness validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.governance import GovernanceEpoch
from epip.temporal.availability import AvailabilityDecision, AvailabilityStatus
from epip.temporal.completeness import (
    CompletenessDiagnostics,
    CompletenessOutcome,
    CompletenessValidator,
)
from epip.temporal.model import (
    CanonicalInstant,
    CanonicalInterval,
    TemporalAuthorityReference,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.observation import ObservationValidation
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


def _interval(start: int = 0, end: int = 60) -> CanonicalInterval:
    return CanonicalInterval(_instant(start), _instant(end))


def _authority(
    role: str = "source_boundary_admission_authority", epoch: int = 5
) -> TemporalAuthorityReference:
    return TemporalAuthorityReference(role, role, "1.0.0", GovernanceEpoch(epoch))


def _authority_facts() -> tuple[tuple[str, str, str, GovernanceEpoch], ...]:
    return (
        ("source_authority", "source_authority", "1.0.0", GovernanceEpoch(5)),
        (
            "source_boundary_admission_authority",
            "source_boundary_admission_authority",
            "1.0.0",
            GovernanceEpoch(5),
        ),
        (
            "semantic_planning_authority",
            "semantic_planning_authority",
            "1.0.0",
            GovernanceEpoch(5),
        ),
    )


def _timeframe(**changes: object) -> CanonicalTimeframe:
    values: dict[str, object] = {
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "interval": _interval(),
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "session_policy": SessionInclusionPolicy.ALL_CANONICAL_TIME,
        "calendar_fact_identities": ("session-1", "holiday-1"),
        "authority": _authority("temporal_architecture_authority"),
        "policy_version": "timeframe-policy-1",
    }
    values.update(changes)
    return CanonicalTimeframe(**values)  # type: ignore[arg-type]


def _availability(identity: str = "artifact-1", **changes: object) -> AvailabilityDecision:
    values: dict[str, object] = {
        "artifact_identity": identity,
        "publication_identity": identity,
        "content_identity": f"content-{identity}",
        "producer_identity": "producer-1",
        "producer_version": "1.0.0",
        "implementation_identity": "build-1",
        "governance_snapshot_identity": "snapshot-1",
        "governance_manifest_reference": "manifest-1",
        "governance_epoch": GovernanceEpoch(5),
        "boundary_identity": f"boundary-{identity}",
        "use_identity": "consumer-use-1",
        "publication_time": _instant(100),
        "availability_time": _instant(120),
        "knowledge_boundary": _instant(300),
        "observation_time": _instant(30),
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
        "authority_identities": tuple(fact[1] for fact in _authority_facts()),
        "policy_identity": "availability-policy",
        "policy_version": "1.0.0",
        "replacement_identity": None,
        "validity": _interval(0, 300),
        "validity_rule_reference": None,
        "expiration_time": None,
        "non_expiring_policy": "non-expiring-1",
        "freshness_boundary": _instant(40),
        "expected_availability": _instant(130),
        "obsolescence_boundary": None,
        "revision_lineage": (f"publication-{identity}",),
        "visibility_constraints": ("admitted",),
        "authority_facts": _authority_facts(),
    }
    values.update(changes)
    return AvailabilityDecision(**values)  # type: ignore[arg-type]


def _observation(
    identity: str = "artifact-1",
    observation: CanonicalInstant | CanonicalInterval | None = None,
    **changes: object,
) -> ObservationValidation:
    value = observation or _instant(30)
    is_interval = isinstance(value, CanonicalInterval)
    values: dict[str, object] = {
        "artifact_identity": identity,
        "boundary_identity": f"boundary-{identity}",
        "consumer_temporal_boundary": "consumer-use-1",
        "observation": value,
        "source_observation": value,
        "is_interval": is_interval,
        "validity": _interval(0, 300),
        "validity_rule_reference": None,
        "publication_time": _instant(100),
        "availability_time": _instant(120),
        "knowledge_boundary": _instant(300),
        "visible": True,
        "provisionally_temporally_eligible": True,
        "late": False,
        "closure_state": "CLOSED" if is_interval else "POINT",
        "provisional": False,
        "consumer_allows_provisional": False,
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "governance_epoch": GovernanceEpoch(5),
        "revision_lineage": (f"publication-{identity}",),
        "authority_facts": _authority_facts(),
        "policy_version": "1.0.0",
    }
    values.update(changes)
    return ObservationValidation(**values)  # type: ignore[arg-type]


def _validate(
    availability: tuple[AvailabilityDecision, ...] | None = None,
    observations: tuple[ObservationValidation, ...] | None = None,
    memberships: tuple[tuple[str, CanonicalInterval], ...] | None = None,
    required: tuple[CanonicalInterval, ...] | None = None,
    closures: tuple[tuple[str, str], ...] | None = None,
    **changes: object,
) -> CompletenessDiagnostics:
    available = (_availability(),) if availability is None else availability
    observed = (_observation(),) if observations is None else observations
    values: dict[str, object] = {
        "outcome_identity": "completeness-1",
        "availability": available,
        "observations": observed,
        "timeframe": _timeframe(),
        "interval_memberships": (
            (("artifact-1", _interval()),) if memberships is None else memberships
        ),
        "required_intervals": (_interval(),) if required is None else required,
        "closure_facts": (("artifact-1", "POINT"),) if closures is None else closures,
        "watermark_identity": "watermark-1",
        "watermark": _instant(60),
        "watermark_authority": _authority(),
        "watermark_policy_version": "watermark-policy-1",
        "required_cardinality": 1,
        "declared_complete": True,
        "provisional": False,
        "policy_identity": "completeness-policy",
        "policy_version": "1.0.0",
    }
    values.update(changes)
    return CompletenessValidator.validate(**values)  # type: ignore[arg-type]


def _outcome(**changes: object) -> CompletenessOutcome:
    original = _validate().outcomes[0]
    values = {name: getattr(original, name) for name in original._field_names}
    values.update(changes)
    return CompletenessOutcome(**values)


def _reason(**changes: object) -> TemporalDiagnosticReason:
    values: dict[str, object] = {
        "code": TemporalDiagnosticCode.INCOMPLETE_WINDOW,
        "affected_evidence": "artifact-1",
        "source_boundary": "boundary-artifact-1",
        "consumer_boundary": "consumer-use-1",
        "timeframe_identity": "M1",
        "calendar_identity": "calendar-xpar",
        "knowledge_boundary": _instant(300),
        "revision_lineage": ("publication-artifact-1",),
        "policy_version": "1.0.0",
        "reason": "window remains explicitly provisional",
    }
    values.update(changes)
    return TemporalDiagnosticReason(**values)  # type: ignore[arg-type]


def test_public_production_inventory_is_exact() -> None:
    from epip.temporal import completeness

    public = {
        name
        for name, value in vars(completeness).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and value.__module__ == completeness.__name__
    }
    assert public == {"CompletenessDiagnostics", "CompletenessOutcome", "CompletenessValidator"}


def test_complete_interval_is_preserved_without_mutating_inputs() -> None:
    interval = _interval()
    availability = (_availability(),)
    observations = (_observation(observation=interval),)
    before = (availability, observations, interval)
    result = _validate(
        availability,
        observations,
        (("artifact-1", interval),),
        (interval,),
        (("artifact-1", "CLOSED"),),
    )
    outcome = result.outcomes[0]
    assert outcome.complete and outcome.declared_complete and not outcome.provisional
    assert outcome.interval_memberships == (("artifact-1", interval),)
    assert outcome.required_intervals == (interval,)
    assert outcome.calendar_fact_identities == ("holiday-1", "session-1")
    assert before == (availability, observations, interval)
    assert result.reasons == ()


def test_provisional_window_is_explicit_and_attributed() -> None:
    observation = _observation(provisional=True, closure_state="OPEN")
    result = _validate(
        observations=(observation,),
        closures=(("artifact-1", "OPEN"),),
        declared_complete=False,
        provisional=True,
    )
    assert not result.outcomes[0].complete
    assert result.outcomes[0].provisional
    assert result.reasons == (_reason(),)


def test_canonical_permutation_repeated_equality_and_hashing() -> None:
    interval_a = _interval(0, 60)
    interval_b = _interval(60, 120)
    available = (_availability("artifact-b"), _availability("artifact-a"))
    observations = (
        _observation("artifact-b", _instant(90)),
        _observation("artifact-a", _instant(30)),
    )
    memberships = (("artifact-b", interval_b), ("artifact-a", interval_a))
    closures = (("artifact-b", "POINT"), ("artifact-a", "POINT"))
    results = {
        _validate(
            tuple(ap),
            tuple(op),
            tuple(mp),
            tuple(rp),
            tuple(cp),
            required_cardinality=2,
            watermark=_instant(120),
        )
        for ap, op, mp, rp, cp in zip(
            permutations(available),
            permutations(observations),
            permutations(memberships),
            permutations((interval_a, interval_b)),
            permutations(closures),
            strict=True,
        )
    }
    assert len(results) == 1
    result = results.pop()
    assert hash(result) == hash(
        _validate(
            available,
            observations,
            memberships,
            (interval_b, interval_a),
            closures,
            required_cardinality=2,
            watermark=_instant(120),
        )
    )
    assert result.outcomes[0].artifact_identities == ("artifact-a", "artifact-b")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"availability": cast(Any, [])}, "availability inputs"),
        ({"observations": cast(Any, [])}, "observation inputs"),
        ({"observations": ()}, "requires observations"),
        ({"timeframe": cast(Any, "M1")}, "must be an E01 outcome"),
        ({"required_cardinality": -1}, "non-negative integer"),
        ({"required_cardinality": cast(Any, True)}, "non-negative integer"),
        ({"declared_complete": cast(Any, 1)}, "must be boolean"),
        ({"provisional": cast(Any, 0)}, "must be boolean"),
        ({"watermark": cast(Any, 60)}, "must be a CanonicalInstant"),
        ({"watermark_authority": cast(Any, "authority")}, "authority is invalid"),
    ],
)
def test_invalid_top_level_inputs_fail_closed(changes: dict[str, object], message: str) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError), match=message):
        _validate(**cast(Any, changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"outcome_identity": ""},
        {"watermark_identity": ""},
        {"watermark_policy_version": ""},
        {"policy_identity": ""},
        {"policy_version": ""},
    ],
)
def test_missing_text_fails_closed(changes: dict[str, object]) -> None:
    with pytest.raises(MissingFieldError):
        _validate(**cast(Any, changes))


def test_predecessor_binding_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="exactly one E02"):
        _validate(availability=(_availability("other"),))
    with pytest.raises(DataIntegrityError, match="unbound E02"):
        _validate(availability=(_availability(), _availability("other")))
    duplicate = _observation()
    with pytest.raises(DataIntegrityError, match="duplicate observations"):
        _validate(
            availability=(_availability(),),
            observations=(duplicate, duplicate),
            required_cardinality=2,
        )


def test_timeframe_binding_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="observation timeframe"):
        _validate(timeframe=_timeframe(timeframe_identity="M5"))


@pytest.mark.parametrize(
    ("memberships", "message"),
    [
        (cast(Any, []), "immutable tuple"),
        (cast(Any, (("artifact-1", "not-an-interval"),)), "unsupported fact"),
        ((("artifact-1", _interval()), ("artifact-1", _interval(60, 120))), "artifact identities"),
        ((("other", _interval()),), "every observation requires"),
    ],
)
def test_membership_fact_validation(
    memberships: tuple[tuple[str, CanonicalInterval], ...], message: str
) -> None:
    with pytest.raises(DataIntegrityError, match=message):
        _validate(memberships=memberships)


def test_membership_semantics_and_required_coverage_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="outside its declared membership"):
        _validate(memberships=(("artifact-1", _interval(60, 120)),))
    interval = _interval()
    with pytest.raises(DataIntegrityError, match="does not preserve"):
        _validate(
            observations=(_observation(observation=interval),),
            memberships=(("artifact-1", _interval(60, 120)),),
            closures=(("artifact-1", "CLOSED"),),
        )
    with pytest.raises(DataIntegrityError, match="coverage is incomplete"):
        _validate(required=(_interval(0, 60), _interval(60, 120)))


def test_duplicate_required_interval_and_overlap_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="immutable interval tuple"):
        _validate(required=cast(Any, []))
    with pytest.raises(DataIntegrityError, match="immutable interval tuple"):
        _validate(required=cast(Any, ("not-an-interval",)))
    with pytest.raises(DataIntegrityError, match="duplicate intervals"):
        _validate(required=(_interval(), _interval()))
    available = (_availability("artifact-a"), _availability("artifact-b"))
    observations = (
        _observation("artifact-a", _instant(30)),
        _observation("artifact-b", _instant(50)),
    )
    with pytest.raises(DataIntegrityError, match="overlap unexpectedly"):
        _validate(
            available,
            observations,
            (("artifact-a", _interval(0, 60)), ("artifact-b", _interval(40, 100))),
            (_interval(0, 60),),
            (("artifact-a", "POINT"), ("artifact-b", "POINT")),
            required_cardinality=2,
            watermark=_instant(100),
        )


@pytest.mark.parametrize(
    ("closures", "message"),
    [
        (cast(Any, []), "immutable tuple"),
        (cast(Any, (("artifact-1",),)), "unsupported fact"),
        ((("artifact-1", "UNKNOWN"),), "state is unsupported"),
        ((("artifact-1", "POINT"), ("artifact-1", "CLOSED")), "artifact identities"),
        ((("other", "POINT"),), "every observation requires"),
        ((("artifact-1", "CLOSED"),), "does not match E03"),
    ],
)
def test_closure_fact_validation(closures: tuple[tuple[str, str], ...], message: str) -> None:
    with pytest.raises(DataIntegrityError, match=message):
        _validate(closures=closures)


def test_open_or_provisional_cannot_be_final() -> None:
    with pytest.raises(DataIntegrityError, match="open intervals"):
        _validate(
            observations=(_observation(closure_state="OPEN"),),
            closures=(("artifact-1", "OPEN"),),
        )
    with pytest.raises(DataIntegrityError, match="provisional observations"):
        _validate(observations=(_observation(provisional=True),))
    with pytest.raises(DataIntegrityError, match="incomplete final"):
        _validate(declared_complete=False)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"watermark_authority": _authority("source_authority")}, "admission authority"),
        ({"watermark_authority": _authority(epoch=6)}, "governance epoch"),
        ({"watermark": _instant(59)}, "does not cover"),
        ({"watermark": _instant(301)}, "frozen knowledge boundary"),
        ({"watermark": _instant(60, precision="millisecond")}, "canonical basis"),
    ],
)
def test_watermark_validation_fails_closed(changes: dict[str, object], message: str) -> None:
    with pytest.raises(DataIntegrityError, match=message):
        _validate(**cast(Any, changes))


def test_cardinality_and_temporal_eligibility_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="observed cardinality"):
        _validate(required_cardinality=2)
    with pytest.raises(DataIntegrityError, match="temporally ineligible"):
        _validate(
            availability=(_availability(provisionally_temporally_eligible=False),),
            observations=(_observation(provisionally_temporally_eligible=False),),
        )


def test_outcome_context_permutation_preserves_association() -> None:
    base = _outcome()
    second = CompletenessOutcome(
        base.outcome_identity,
        ("artifact-b", "artifact-a"),
        ("source-b", "source-a"),
        ("consumer-b", "consumer-a"),
        (_instant(200), _instant(100)),
        (("revision-b",), ("revision-a",)),
        (("artifact-b", _interval(60, 120)), ("artifact-a", _interval())),
        (_interval(60, 120), _interval()),
        (("artifact-b", "POINT"), ("artifact-a", "POINT")),
        base.watermark_identity,
        _instant(120),
        base.watermark_authority,
        base.watermark_policy_version,
        2,
        2,
        True,
        True,
        False,
        base.timeframe_identity,
        base.timeframe_version,
        base.calendar_identity,
        base.calendar_version,
        base.calendar_fact_identities,
        base.governance_epoch,
        base.policy_identity,
        base.policy_version,
    )
    assert second.artifact_identities == ("artifact-a", "artifact-b")
    assert second.source_temporal_boundaries == ("source-a", "source-b")
    assert second.revision_lineages == (("revision-a",), ("revision-b",))


@pytest.mark.parametrize(
    "changes",
    [
        {"artifact_identities": ()},
        {"artifact_identities": cast(Any, [])},
        {"artifact_identities": ("artifact-1", "artifact-1")},
        {"knowledge_boundaries": cast(Any, [])},
        {"knowledge_boundaries": cast(Any, ("now",))},
        {"revision_lineages": cast(Any, [])},
        {"revision_lineages": cast(Any, ("revision",))},
        {"watermark": cast(Any, "now")},
        {"watermark_authority": cast(Any, "authority")},
        {"required_cardinality": cast(Any, True)},
        {"observed_cardinality": cast(Any, True)},
        {"declared_complete": cast(Any, 1)},
        {"complete": False},
        {"governance_epoch": cast(Any, 5)},
        {"observed_cardinality": 2},
        {"source_temporal_boundaries": ()},
    ],
)
def test_outcome_invalid_state_is_rejected(changes: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _outcome(**changes)


def test_diagnostics_are_canonical_attributed_and_immutable() -> None:
    provisional = _validate(
        observations=(_observation(provisional=True, closure_state="OPEN"),),
        closures=(("artifact-1", "OPEN"),),
        declared_complete=False,
        provisional=True,
    )
    diagnostics = CompletenessDiagnostics(
        tuple(reversed(provisional.outcomes)), tuple(reversed(provisional.reasons))
    )
    assert diagnostics == provisional
    assert hash(diagnostics) == hash(provisional)
    with pytest.raises(FrozenInstanceError):
        diagnostics.reasons = ()
    with pytest.raises(DataIntegrityError, match="not attributable"):
        CompletenessDiagnostics(provisional.outcomes, (_reason(affected_evidence="orphan"),))
    with pytest.raises(DataIntegrityError, match="duplicate reasons"):
        CompletenessDiagnostics(provisional.outcomes, (_reason(), _reason()))
    with pytest.raises(DataIntegrityError, match="duplicate outcomes"):
        CompletenessDiagnostics((provisional.outcomes[0], provisional.outcomes[0]))
    with pytest.raises(DataIntegrityError, match="immutable outcomes"):
        CompletenessDiagnostics(cast(Any, []))
    with pytest.raises(DataIntegrityError, match="immutable reasons"):
        CompletenessDiagnostics(provisional.outcomes, cast(Any, []))


def test_outcome_is_immutable_hashable_and_unequal_to_other_types() -> None:
    outcome = _outcome()
    assert outcome == _outcome()
    assert hash(outcome) == hash(_outcome())
    assert outcome != object()
    with pytest.raises(FrozenInstanceError):
        outcome.complete = False


def test_no_successor_responsibilities_are_introduced() -> None:
    forbidden = {
        "aggregate",
        "synthesize",
        "interpolate",
        "forward_fill",
        "select_provider",
        "build_graph",
        "resolve_revision",
        "execute",
        "replay",
        "certify",
        "close_programme",
    }
    assert forbidden.isdisjoint(vars(CompletenessValidator))
