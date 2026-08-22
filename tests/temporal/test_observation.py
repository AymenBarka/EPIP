"""Component tests for A05-E03 deterministic observation validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.governance import GovernanceEpoch
from epip.temporal.availability import (
    AvailabilityDecision,
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
from epip.temporal.observation import (
    ObservationDiagnostics,
    ObservationValidation,
    ObservationValidator,
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
    role: str = "source_authority",
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
        _authority(),
        _authority("source_boundary_admission_authority"),
        _authority("semantic_planning_authority"),
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
        "policy_versions": (("observation", "1.0.0"),),
        "authorities": _authorities(),
    }
    values.update(changes)
    return TemporalBoundary(**values)  # type: ignore[arg-type]


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


def _authority_facts() -> tuple[tuple[str, str, str, GovernanceEpoch], ...]:
    return tuple(
        (
            authority.authority_role,
            authority.authority_identity,
            authority.authority_version,
            authority.governance_epoch,
        )
        for authority in _authorities()
    )


def _availability(
    boundary: TemporalBoundary | None = None, **changes: object
) -> AvailabilityDecision:
    fact = boundary or _boundary()
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
        "boundary_identity": fact.boundary_identity,
        "use_identity": "consumer-use-1",
        "publication_time": fact.publication,
        "availability_time": fact.availability,
        "knowledge_boundary": fact.knowledge,
        "observation_time": fact.observation,
        "use_time": _instant(60),
        "status": AvailabilityStatus.VISIBLE,
        "visible": True,
        "provisionally_temporally_eligible": True,
        "late": False,
        "stale": False,
        "expired": False,
        "obsolete": False,
        "timeframe_identity": fact.timeframe_identity,
        "timeframe_version": fact.timeframe_version,
        "calendar_identity": fact.calendar_identity,
        "calendar_version": fact.calendar_version,
        "authority_identities": tuple(
            authority.authority_identity for authority in fact.authorities
        ),
        "policy_identity": "availability-policy",
        "policy_version": "1.0.0",
        "replacement_identity": None,
        "validity": fact.validity,
        "validity_rule_reference": fact.validity_rule_reference,
        "expiration_time": fact.expiration,
        "non_expiring_policy": fact.non_expiring_policy,
        "freshness_boundary": _instant(40),
        "expected_availability": _instant(130),
        "obsolescence_boundary": None,
        "revision_lineage": fact.revision_lineage,
        "visibility_constraints": fact.visibility_constraints,
        "authority_facts": _authority_facts(),
    }
    values.update(changes)
    return AvailabilityDecision(**values)  # type: ignore[arg-type]


def _validation(**changes: object) -> ObservationValidation:
    values: dict[str, object] = {
        "artifact_identity": "artifact-1",
        "boundary_identity": "boundary-1",
        "consumer_temporal_boundary": "consumer-use-1",
        "observation": _instant(50),
        "source_observation": _instant(50),
        "is_interval": False,
        "validity": CanonicalInterval(_instant(0), _instant(200)),
        "validity_rule_reference": None,
        "publication_time": _instant(100),
        "availability_time": _instant(120),
        "knowledge_boundary": _instant(150),
        "visible": True,
        "provisionally_temporally_eligible": True,
        "late": False,
        "closure_state": "POINT",
        "provisional": False,
        "consumer_allows_provisional": False,
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "governance_epoch": GovernanceEpoch(5),
        "revision_lineage": ("publication-1",),
        "authority_facts": _authority_facts(),
        "policy_version": "1.0.0",
    }
    values.update(changes)
    return ObservationValidation(**values)  # type: ignore[arg-type]


def _reason(**changes: object) -> TemporalDiagnosticReason:
    values: dict[str, object] = {
        "code": TemporalDiagnosticCode.LATE_ARRIVAL,
        "affected_evidence": "artifact-1",
        "source_boundary": "boundary-1",
        "consumer_boundary": "consumer-use-1",
        "timeframe_identity": "M1",
        "calendar_identity": "calendar-xpar",
        "knowledge_boundary": _instant(150),
        "revision_lineage": ("publication-1",),
        "policy_version": "1.0.0",
        "reason": "late",
    }
    values.update(changes)
    return TemporalDiagnosticReason(**values)  # type: ignore[arg-type]


def _validate(
    boundary: TemporalBoundary | None = None,
    availability: AvailabilityDecision | None = None,
    source: CanonicalInstant | CanonicalInterval | None = None,
    closure_state: str = "POINT",
    provisional: bool = False,
    consumer_allows_provisional: bool = False,
    timeframe: CanonicalTimeframe | None = None,
) -> ObservationDiagnostics:
    fact = boundary or _boundary()
    return ObservationValidator.validate(
        fact,
        availability or _availability(fact),
        source or fact.observation,
        closure_state,
        provisional,
        consumer_allows_provisional,
        "1.0.0",
        _timeframe() if timeframe is None else timeframe,
    )


def test_public_production_inventory_is_exact() -> None:
    from epip.temporal import observation

    public = {
        name
        for name, value in vars(observation).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and value.__module__ == observation.__name__
    }
    assert public == {
        "ObservationDiagnostics",
        "ObservationValidation",
        "ObservationValidator",
    }


def test_point_observation_and_validity_are_preserved() -> None:
    result = _validate()
    validation = result.validations[0]
    assert validation.observation == _instant(50)
    assert validation.source_observation == _instant(50)
    assert validation.is_interval is False
    assert validation.validity == CanonicalInterval(_instant(0), _instant(200))
    assert validation.validity_rule_reference is None
    assert validation.publication_time == _instant(100)
    assert validation.availability_time == _instant(120)
    assert validation.consumer_temporal_boundary == "consumer-use-1"
    assert validation.revision_lineage == ("publication-1",)
    assert result.reasons == ()


def test_validation_independently_preserves_reconstruction_context() -> None:
    boundary = _boundary(revision_lineage=("revision-b", "revision-a"))
    validation = _validate(boundary).validations[0]
    assert validation.consumer_temporal_boundary == "consumer-use-1"
    assert validation.revision_lineage == ("revision-a", "revision-b")
    assert validation.artifact_identity == "artifact-1"
    assert validation.boundary_identity == boundary.boundary_identity
    assert validation.observation == boundary.observation
    assert validation.validity == boundary.validity
    assert validation.publication_time == boundary.publication
    assert validation.availability_time == boundary.availability
    assert validation.knowledge_boundary == boundary.knowledge


def test_revision_lineage_permutations_are_canonical() -> None:
    lineage = ("revision-a", "revision-b")
    expected = _validation(revision_lineage=lineage)
    for permutation in permutations(lineage):
        actual = _validation(revision_lineage=permutation)
        assert actual == expected and hash(actual) == hash(expected)


def test_interval_observation_is_preserved_without_end_substitution() -> None:
    interval = CanonicalInterval(_instant(40), _instant(60))
    boundary = _boundary(observation=interval)
    result = _validate(boundary, closure_state="CLOSED")
    validation = result.validations[0]
    assert validation.observation == interval
    assert validation.is_interval is True
    assert validation.closure_state == "CLOSED"


def test_authorized_validity_rule_is_preserved_without_interpretation() -> None:
    boundary = _boundary(validity=None, validity_rule_reference="producer-validity-rule@1")
    result = _validate(boundary)
    validation = result.validations[0]
    assert validation.validity is None
    assert validation.validity_rule_reference == "producer-validity-rule@1"


def test_late_arrival_preserves_observation_and_attributed_diagnostic() -> None:
    availability = _availability(late=True)
    result = _validate(availability=availability)
    validation = result.validations[0]
    assert validation.late is True
    assert validation.observation == _instant(50)
    assert result.reasons[0].code is TemporalDiagnosticCode.LATE_ARRIVAL
    assert result.reasons[0].affected_evidence == validation.artifact_identity
    assert result.reasons[0].source_boundary == validation.boundary_identity


def test_source_timestamp_mutation_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="timestamp mutation"):
        _validate(source=_instant(51))


def test_interval_end_substitution_fails_closed() -> None:
    source = CanonicalInterval(_instant(40), _instant(60))
    boundary = _boundary(observation=_instant(60))
    with pytest.raises(DataIntegrityError, match="interval-end substitution"):
        _validate(boundary, source=source)


@pytest.mark.parametrize(
    ("closure", "provisional", "allowed", "message"),
    [
        ("FINAL", True, True, "PROVISIONAL_AS_FINAL"),
        ("CLOSED", True, False, "PROVISIONAL_AS_FINAL"),
        ("OPEN", False, False, "PROVISIONAL_AS_FINAL"),
        ("POINT", False, False, "INVALID_BOUNDARY_CONVENTION"),
    ],
)
def test_invalid_interval_closure_and_provisional_states_fail_closed(
    closure: str, provisional: bool, allowed: bool, message: str
) -> None:
    interval = CanonicalInterval(_instant(40), _instant(60))
    boundary = _boundary(observation=interval)
    with pytest.raises(DataIntegrityError, match=message):
        _validate(
            boundary,
            closure_state=closure,
            provisional=provisional,
            consumer_allows_provisional=allowed,
        )


def test_explicitly_authorized_provisional_interval_is_valid() -> None:
    interval = CanonicalInterval(_instant(40), _instant(60))
    boundary = _boundary(observation=interval)
    validation = _validate(
        boundary,
        closure_state="OPEN",
        provisional=True,
        consumer_allows_provisional=True,
    ).validations[0]
    assert validation.provisional and validation.consumer_allows_provisional


def test_point_rejects_interval_closure_state() -> None:
    with pytest.raises(DataIntegrityError, match="point observation"):
        _validate(closure_state="CLOSED")


@pytest.mark.parametrize("closure", ["", "UNKNOWN"])
def test_unsupported_closure_state_fails_closed(closure: str) -> None:
    with pytest.raises(DataIntegrityError):
        _validate(closure_state=closure)


@pytest.mark.parametrize(
    ("provisional", "allowed"),
    [(cast(Any, 1), False), (False, cast(Any, 1))],
)
def test_mutable_or_non_boolean_provisional_declarations_fail_closed(
    provisional: bool, allowed: bool
) -> None:
    with pytest.raises(DataIntegrityError, match="boolean"):
        _validate(provisional=provisional, consumer_allows_provisional=allowed)


def test_e02_binding_mismatch_and_invisibility_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="does not bind"):
        _validate(availability=_availability(boundary_identity="other"))
    with pytest.raises(DataIntegrityError, match="FUTURE_LEAKAGE"):
        _validate(
            availability=_availability(
                visible=False,
                provisionally_temporally_eligible=False,
                status=AvailabilityStatus.NOT_VISIBLE,
            )
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"observation_time": _instant(51)},
        {"validity": CanonicalInterval(_instant(1), _instant(200))},
        {"publication_time": _instant(101)},
        {"availability_time": _instant(121)},
        {"knowledge_boundary": _instant(151)},
        {"timeframe_identity": "M5"},
        {"timeframe_version": "2.0.0"},
        {"calendar_identity": "other-calendar"},
        {"calendar_version": "other-version"},
    ],
)
def test_each_e02_context_mismatch_fails_closed(changes: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError, match="does not bind"):
        _validate(availability=_availability(None, **changes))


def test_validity_rule_binding_mismatch_fails_closed() -> None:
    boundary = _boundary(validity=None, validity_rule_reference="rule@1")
    availability = _availability(boundary, validity_rule_reference="rule@2")
    with pytest.raises(DataIntegrityError, match="does not bind"):
        _validate(boundary, availability)


def test_inconsistent_predecessor_revision_lineage_fails_closed_deterministically() -> None:
    boundary = _boundary(revision_lineage=("revision-b", "revision-a"))
    availability = _availability(boundary, revision_lineage=("different-revision",))
    failures: list[str] = []
    for _ in range(5):
        with pytest.raises(DataIntegrityError, match="does not bind") as raised:
            _validate(boundary, availability)
        failures.append(str(raised.value))
    assert len(set(failures)) == 1


def test_predecessor_revision_lineage_permutations_bind_canonically() -> None:
    lineage = ("revision-a", "revision-b")
    outcomes = tuple(
        _validate(
            _boundary(revision_lineage=permutation),
            _availability(
                _boundary(revision_lineage=permutation),
                revision_lineage=tuple(reversed(permutation)),
            ),
        )
        for permutation in permutations(lineage)
    )
    assert all(outcome == outcomes[0] for outcome in outcomes)
    assert all(hash(outcome) == hash(outcomes[0]) for outcome in outcomes)


def test_source_authority_and_epoch_are_mandatory() -> None:
    missing = _boundary(
        authorities=(
            _authority("source_boundary_admission_authority"),
            _authority("semantic_planning_authority"),
        )
    )
    with pytest.raises(DataIntegrityError, match="source authority"):
        _validate(missing, _availability(missing))
    duplicate = _boundary(
        authorities=(
            _authority(identity="source-1"),
            _authority(identity="source-2"),
            _authority("source_boundary_admission_authority"),
        )
    )
    with pytest.raises(DataIntegrityError, match="source authority"):
        _validate(duplicate, _availability(duplicate))
    with pytest.raises(DataIntegrityError, match="governance epoch"):
        _validate(availability=_availability(governance_epoch=GovernanceEpoch(6)))


def test_timeframe_scope_is_validated_without_mapping_or_membership() -> None:
    with pytest.raises(DataIntegrityError, match="MISSING_TIMEFRAME"):
        ObservationValidator.validate(
            _boundary(),
            _availability(),
            _instant(50),
            "POINT",
            False,
            False,
            "1.0.0",
        )
    unscoped = _boundary(
        timeframe_identity=None,
        timeframe_version=None,
        calendar_identity=None,
        calendar_version=None,
    )
    outcome = ObservationValidator.validate(
        unscoped,
        _availability(unscoped),
        unscoped.observation,
        "POINT",
        False,
        False,
        "1.0.0",
    )
    assert outcome.validations[0].timeframe_identity is None
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_TIMEFRAME"):
        ObservationValidator.validate(
            unscoped,
            _availability(unscoped),
            unscoped.observation,
            "POINT",
            False,
            False,
            "1.0.0",
            _timeframe(),
        )
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_TIMEFRAME"):
        _validate(timeframe=_timeframe(timeframe_identity="M5"))


@pytest.mark.parametrize(
    ("boundary", "source", "timeframe", "diagnostic"),
    [
        (
            _boundary(observation=_instant(50, precision="nanosecond")),
            None,
            None,
            "INVALID_PRECISION",
        ),
        (_boundary(), _instant(50, time_scale="TAI"), None, "HISTORICAL_AMBIGUITY"),
        (
            _boundary(validity=CanonicalInterval(_instant(0), _instant(200))),
            None,
            _timeframe(
                interval=CanonicalInterval(
                    _instant(0, precision="nanosecond"),
                    _instant(60, precision="nanosecond"),
                )
            ),
            "INVALID_PRECISION",
        ),
    ],
)
def test_incompatible_canonical_bases_fail_closed(
    boundary: TemporalBoundary,
    source: CanonicalInstant | CanonicalInterval | None,
    timeframe: CanonicalTimeframe | None,
    diagnostic: str,
) -> None:
    with pytest.raises(DataIntegrityError, match=diagnostic):
        _validate(
            boundary,
            _availability(boundary),
            source or boundary.observation,
            timeframe=timeframe or _timeframe(),
        )


def test_source_authority_identity_does_not_change_canonical_basis() -> None:
    boundary = _boundary(
        observation=_instant(50, authority_identity="source-clock"),
        publication=_instant(100, authority_identity="publication-clock"),
        availability=_instant(120, authority_identity="availability-clock"),
    )
    assert _validate(boundary).validations[0].observation == boundary.observation


@pytest.mark.parametrize(
    "arguments",
    [
        (cast(Any, object()), _availability(), _instant(50), "POINT", False, False, "1"),
        (_boundary(), cast(Any, object()), _instant(50), "POINT", False, False, "1"),
        (_boundary(), _availability(), cast(Any, object()), "POINT", False, False, "1"),
        (_boundary(), _availability(), _instant(50), "POINT", False, False, ""),
        (
            _boundary(),
            _availability(),
            _instant(50),
            "POINT",
            False,
            False,
            "1",
            cast(Any, object()),
        ),
    ],
)
def test_invalid_top_level_inputs_fail_closed(arguments: tuple[object, ...]) -> None:
    with pytest.raises(DataIntegrityError):
        ObservationValidator.validate(*arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "changes",
    [
        {"artifact_identity": ""},
        {"boundary_identity": ""},
        {"consumer_temporal_boundary": ""},
        {"closure_state": ""},
        {"policy_version": ""},
        {"observation": cast(Any, object())},
        {"source_observation": cast(Any, object())},
        {"is_interval": cast(Any, 1)},
        {"is_interval": True},
        {"source_observation": _instant(51)},
        {"validity": cast(Any, object())},
        {"validity_rule_reference": ""},
        {"validity": None, "validity_rule_reference": None},
        {
            "validity": CanonicalInterval(_instant(0), _instant(200)),
            "validity_rule_reference": "rule@1",
        },
        {"publication_time": cast(Any, object())},
        {"availability_time": cast(Any, object())},
        {"knowledge_boundary": cast(Any, object())},
        {"visible": cast(Any, 1)},
        {"provisionally_temporally_eligible": cast(Any, 1)},
        {"late": cast(Any, 1)},
        {"provisional": cast(Any, 1)},
        {"consumer_allows_provisional": cast(Any, 1)},
        {"timeframe_identity": ""},
        {"timeframe_version": ""},
        {"timeframe_version": None},
        {"calendar_identity": ""},
        {"calendar_version": ""},
        {"calendar_version": None},
        {"governance_epoch": cast(Any, 5)},
        {"revision_lineage": cast(Any, [])},
        {"revision_lineage": ("",)},
        {"authority_facts": cast(Any, [])},
        {"authority_facts": ()},
        {"authority_facts": (cast(Any, ("role", "identity")),)},
        {"authority_facts": (("", "identity", "1", GovernanceEpoch(5)),)},
    ],
)
def test_validation_rejects_invalid_or_inconsistent_context(
    changes: dict[str, object],
) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _validation(**changes)


def test_interval_validation_value_is_supported() -> None:
    interval = CanonicalInterval(_instant(40), _instant(60))
    value = _validation(
        observation=interval,
        source_observation=interval,
        is_interval=True,
        closure_state="CLOSED",
    )
    assert value.is_interval


def test_authority_fact_permutations_are_canonical() -> None:
    facts = _authority_facts()
    expected = _validation(authority_facts=facts)
    for permutation in permutations(facts):
        actual = _validation(authority_facts=permutation)
        assert actual == expected
        assert hash(actual) == hash(expected)


def test_diagnostics_are_immutable_hashable_and_permutation_invariant() -> None:
    first = _validation()
    second = _validation(artifact_identity="artifact-2")
    reason_a = _reason(reason="alpha")
    reason_b = _reason(affected_evidence="artifact-2", reason="beta")
    expected = ObservationDiagnostics((first, second), (reason_a, reason_b))
    actual = ObservationDiagnostics((second, first), (reason_b, reason_a))
    assert actual == expected and hash(actual) == hash(expected)
    with pytest.raises(FrozenInstanceError):
        actual.reasons = ()


def test_diagnostics_reject_orphan_and_mismatched_reasons() -> None:
    validation = _validation()
    with pytest.raises(DataIntegrityError, match="exactly one validation"):
        ObservationDiagnostics((), (_reason(),))
    for mismatch in (
        _reason(affected_evidence="other-artifact"),
        _reason(source_boundary="other-boundary"),
        _reason(consumer_boundary="other-consumer"),
        _reason(timeframe_identity="M5"),
        _reason(calendar_identity="other-calendar"),
        _reason(knowledge_boundary=_instant(151)),
        _reason(revision_lineage=("other-revision",)),
        _reason(policy_version="2.0.0"),
    ):
        with pytest.raises(DataIntegrityError, match="exactly one validation"):
            ObservationDiagnostics((validation,), (mismatch,))


def test_diagnostics_reject_duplicate_inconsistent_bindings() -> None:
    validation = _validation()
    first = _reason(reason="first")
    second = _reason(reason="second")
    with pytest.raises(DataIntegrityError, match="duplicate inconsistent bindings"):
        ObservationDiagnostics((validation,), (first, second))


@pytest.mark.parametrize(
    "call",
    [
        lambda: ObservationDiagnostics(cast(Any, [])),
        lambda: ObservationDiagnostics((cast(Any, object()),)),
        lambda: ObservationDiagnostics((), cast(Any, [])),
        lambda: ObservationDiagnostics((), (cast(Any, object()),)),
        lambda: ObservationDiagnostics((_validation(), _validation())),
    ],
)
def test_diagnostics_reject_invalid_and_duplicate_context(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_point_and_interval_participate_in_total_diagnostic_ordering() -> None:
    interval = CanonicalInterval(_instant(40), _instant(60))
    point = _validation()
    interval_value = _validation(
        artifact_identity="artifact-2",
        observation=interval,
        source_observation=interval,
        is_interval=True,
        closure_state="CLOSED",
    )
    expected = ObservationDiagnostics((point, interval_value))
    actual = ObservationDiagnostics((interval_value, point))
    assert actual == expected and hash(actual) == hash(expected)


def test_outputs_are_immutable_equal_hashable_and_repeatedly_deterministic() -> None:
    validation = _validation()
    diagnostics = ObservationDiagnostics((validation,))
    assert validation != object() and diagnostics != object()
    assert hash(validation) and hash(diagnostics)
    for value in (validation, diagnostics):
        with pytest.raises(FrozenInstanceError):
            cast(Any, value).policy_version = "changed"
    outcomes = tuple(_validate() for _ in range(5))
    assert all(outcome == outcomes[0] for outcome in outcomes)
    assert all(hash(outcome) == hash(outcomes[0]) for outcome in outcomes)


def test_predecessor_inputs_remain_unchanged() -> None:
    boundary = _boundary()
    availability = _availability(boundary)
    timeframe = _timeframe()
    before = (hash(boundary), hash(availability), hash(timeframe))
    ObservationValidator.validate(
        boundary,
        availability,
        boundary.observation,
        "POINT",
        False,
        False,
        "1.0.0",
        timeframe,
    )
    assert before == (hash(boundary), hash(availability), hash(timeframe))


def test_e03_contains_no_successor_or_unallocated_behaviour() -> None:
    from epip.temporal import observation

    forbidden = {
        "CompletenessValidator",
        "TemporalDependencyValidator",
        "RevisionValidator",
        "ReplayCompatibilityValidator",
        "TemporalCertification",
        "TemporalClosure",
        "ProviderExecutor",
        "DependencyGraphBuilder",
    }
    assert forbidden.isdisjoint(vars(observation))
