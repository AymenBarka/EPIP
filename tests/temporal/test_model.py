"""Component tests for A05-E00 immutable temporal semantic models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.governance import GovernanceEpoch
from epip.temporal import (
    BoundaryConvention,
    CalendarFact,
    CalendarFactKind,
    CalendarFactSet,
    CanonicalInstant,
    CanonicalInterval,
    TemporalAuthorityReference,
    TemporalBoundary,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
    TemporalDimension,
)


def _instant(value: int = 10, **changes: object) -> CanonicalInstant:
    values: dict[str, object] = {
        "value": value,
        "precision": "nanosecond",
        "time_scale": "UTC",
        "timezone_basis": "UTC",
        "authority_identity": "time-authority-1",
    }
    values.update(changes)
    return CanonicalInstant(**values)  # type: ignore[arg-type]


def _interval(start: int = 10, end: int = 20) -> CanonicalInterval:
    return CanonicalInterval(_instant(start), _instant(end))


def _authority(**changes: object) -> TemporalAuthorityReference:
    values: dict[str, object] = {
        "authority_identity": "calendar-authority-1",
        "authority_role": "calendar_authority",
        "authority_version": "1.0.0",
        "governance_epoch": GovernanceEpoch(4),
    }
    values.update(changes)
    return TemporalAuthorityReference(**values)  # type: ignore[arg-type]


def _fact(kind: CalendarFactKind, suffix: str | None = None, **changes: object) -> CalendarFact:
    marker = suffix or kind.value.lower()
    values: dict[str, object] = {
        "fact_identity": f"fact-{marker}",
        "kind": kind,
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "interval": _interval(),
        "authority": _authority(),
        "policy_version": "calendar-policy-1",
        "session_identity": (
            "session-regular"
            if kind in {CalendarFactKind.SESSION, CalendarFactKind.SHORTENED_SESSION}
            else None
        ),
        "timezone_identity": "Europe/Paris" if kind is CalendarFactKind.TIMEZONE_RULE else None,
        "utc_offset_seconds": 3600 if kind is CalendarFactKind.TIMEZONE_RULE else None,
        "reason": "governed exception" if kind is CalendarFactKind.EXCEPTIONAL_INTERVAL else None,
    }
    values.update(changes)
    return CalendarFact(**values)  # type: ignore[arg-type]


def _facts() -> tuple[CalendarFact, ...]:
    return tuple(_fact(kind) for kind in CalendarFactKind)


def _boundary(**changes: object) -> TemporalBoundary:
    values: dict[str, object] = {
        "boundary_identity": "boundary-1",
        "observation": _interval(0, 10),
        "validity": _interval(0, 20),
        "validity_rule_reference": None,
        "publication": _instant(11),
        "availability": _instant(12),
        "knowledge": _instant(13),
        "revision": None,
        "expiration": None,
        "non_expiring_policy": "non-expiring-policy-1",
        "historical": None,
        "replay": None,
        "timeframe_identity": "H1",
        "timeframe_version": "1.0.0",
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "revision_lineage": ("publication-1",),
        "visibility_constraints": ("closed",),
        "policy_versions": (("availability", "1.0.0"), ("temporal", "1.0.0")),
        "authorities": (
            _authority(),
            _authority(
                authority_identity="source-authority-1",
                authority_role="source_authority",
            ),
        ),
    }
    values.update(changes)
    return TemporalBoundary(**values)  # type: ignore[arg-type]


def test_public_inventory_and_taxonomies_are_exact() -> None:
    from epip import temporal

    assert set(temporal.__all__) == {
        "BoundaryConvention",
        "CalendarFact",
        "CalendarFactKind",
        "CalendarFactSet",
        "CanonicalInstant",
        "CanonicalInterval",
        "TemporalAuthorityReference",
        "TemporalBoundary",
        "TemporalDiagnosticCode",
        "TemporalDiagnosticReason",
        "TemporalDimension",
    }
    assert {item.value for item in TemporalDimension} == {
        "OBSERVATION",
        "VALIDITY",
        "PUBLICATION",
        "AVAILABILITY",
        "KNOWLEDGE",
        "REVISION",
        "EXPIRATION",
        "HISTORICAL",
        "REPLAY",
    }
    assert {item.value for item in CalendarFactKind} == {
        "SESSION",
        "HOLIDAY",
        "TIMEZONE_RULE",
        "SHORTENED_SESSION",
        "MARKET_CLOSURE",
        "EXCEPTIONAL_INTERVAL",
    }
    assert {item.value for item in TemporalDiagnosticCode} == {
        "MISSING_OBSERVATION_TIME",
        "MISSING_PUBLICATION_TIME",
        "MISSING_AVAILABILITY_TIME",
        "MISSING_VALIDITY_TIME",
        "MISSING_REVISION_TIME",
        "MISSING_EXPIRATION_TIME",
        "INVALID_CANONICAL_INSTANT",
        "INVALID_CANONICAL_INTERVAL",
        "INVALID_PRECISION",
        "INVALID_BOUNDARY_CONVENTION",
        "UNKNOWN_TIMEZONE",
        "INCOMPATIBLE_TIMEZONE",
        "UNKNOWN_CALENDAR",
        "INCOMPATIBLE_CALENDAR",
        "UNKNOWN_SESSION",
        "INCOMPATIBLE_SESSION",
        "UNKNOWN_TIMEFRAME",
        "INCOMPATIBLE_TIMEFRAME",
        "LATE_ARRIVAL",
        "DUPLICATE_TEMPORAL_ARTIFACT",
        "CONFLICTING_REVISION",
        "MISSING_INTERVAL",
        "MISSING_TIMEFRAME",
        "UNEXPECTED_INTERVAL_OVERLAP",
        "INCOMPLETE_WINDOW",
        "PROVISIONAL_AS_FINAL",
        "INSUFFICIENT_WATERMARK",
        "STALE_EVIDENCE",
        "EXPIRED_EVIDENCE",
        "FUTURE_DEPENDENCY",
        "FUTURE_LEAKAGE",
        "HISTORICAL_AMBIGUITY",
        "HIDDEN_AGGREGATION",
        "HIDDEN_INHERITANCE",
        "HIDDEN_TIMEFRAME_CONVERSION",
        "REVISION_LINEAGE_VIOLATION",
        "DYNAMIC_AVAILABILITY_MUTATION",
        "CROSS_TIMEFRAME_INCOMPATIBILITY",
        "CROSS_TIMEFRAME_CONFLICT",
    }


def test_canonical_instant_is_immutable_ordered_and_hashable() -> None:
    instant = _instant()
    assert _instant(9).value < instant.value < _instant(11).value
    assert instant == _instant() and hash(instant) == hash(_instant())
    with pytest.raises(FrozenInstanceError):
        instant.value = 11


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"value": True}, DataIntegrityError),
        ({"value": cast(Any, "10")}, DataIntegrityError),
        ({"precision": ""}, DataIntegrityError),
        ({"time_scale": ""}, DataIntegrityError),
        ({"timezone_basis": ""}, DataIntegrityError),
        ({"authority_identity": ""}, DataIntegrityError),
    ],
)
def test_canonical_instant_rejects_invalid_inputs(
    changes: dict[str, object], error: type[Exception]
) -> None:
    with pytest.raises(error):
        cast(Any, _instant)(**changes)


def test_interval_is_half_open_immutable_and_hashable() -> None:
    interval = _interval()
    assert interval.boundary_convention is BoundaryConvention.START_INCLUSIVE_END_EXCLUSIVE
    assert interval == _interval() and hash(interval) == hash(_interval())
    with pytest.raises(FrozenInstanceError):
        interval.end = _instant(30)


@pytest.mark.parametrize(
    "call",
    [
        lambda: CanonicalInterval(cast(Any, object()), _instant()),
        lambda: CanonicalInterval(_instant(), cast(Any, object())),
        lambda: CanonicalInterval(_instant(), _instant(20), cast(Any, "closed")),
        lambda: CanonicalInterval(_instant(), _instant(20, precision="second")),
        lambda: CanonicalInterval(_instant(), _instant(20, time_scale="TAI")),
        lambda: CanonicalInterval(_instant(), _instant(20, timezone_basis="Europe/Paris")),
        lambda: CanonicalInterval(_instant(20), _instant(20)),
        lambda: CanonicalInterval(_instant(20), _instant(10)),
    ],
)
def test_interval_rejects_invalid_or_ambiguous_boundaries(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


@pytest.mark.parametrize(
    "changes",
    [
        {"authority_identity": ""},
        {"authority_role": ""},
        {"authority_version": ""},
        {"governance_epoch": cast(Any, object())},
    ],
)
def test_authority_reference_rejects_invalid_context(changes: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError):
        _authority(**changes)


def test_all_authoritative_calendar_fact_kinds_are_immutable() -> None:
    facts = _facts()
    assert {fact.kind for fact in facts} == set(CalendarFactKind)
    assert all(hash(fact) for fact in facts)
    with pytest.raises(FrozenInstanceError):
        facts[0].reason = "changed"


@pytest.mark.parametrize(
    "changes",
    [
        {"fact_identity": ""},
        {"calendar_identity": ""},
        {"calendar_version": ""},
        {"policy_version": ""},
        {"interval": cast(Any, object())},
        {"authority": cast(Any, object())},
        {"reason": ""},
        {"utc_offset_seconds": True},
    ],
)
def test_calendar_fact_rejects_invalid_common_context(changes: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, _fact)(CalendarFactKind.EXCEPTIONAL_INTERVAL, **changes)


@pytest.mark.parametrize(
    "call",
    [
        lambda: CalendarFact(
            "fact-invalid",
            cast(Any, "SESSION"),
            "calendar-xpar",
            "2026.1",
            _interval(),
            _authority(),
            "calendar-policy-1",
        ),
        lambda: _fact(CalendarFactKind.TIMEZONE_RULE, timezone_identity=None),
        lambda: _fact(CalendarFactKind.TIMEZONE_RULE, utc_offset_seconds=None),
        lambda: _fact(CalendarFactKind.HOLIDAY, timezone_identity="UTC"),
        lambda: _fact(CalendarFactKind.HOLIDAY, utc_offset_seconds=0),
        lambda: _fact(CalendarFactKind.SESSION, session_identity=None),
        lambda: _fact(CalendarFactKind.SHORTENED_SESSION, session_identity=None),
        lambda: _fact(CalendarFactKind.MARKET_CLOSURE, session_identity="session-1"),
    ],
)
def test_calendar_fact_kind_specific_fields_fail_closed(call: object) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        cast(Any, call)()


def test_calendar_fact_set_is_canonical_and_permutation_invariant() -> None:
    facts = _facts()
    expected = CalendarFactSet("calendar-xpar", "2026.1", _authority(), facts)
    for permutation in permutations(facts):
        actual = CalendarFactSet("calendar-xpar", "2026.1", _authority(), permutation)
        assert actual == expected
        assert hash(actual) == hash(expected)
    assert expected.facts == tuple(
        sorted(facts, key=lambda fact: (fact.kind.value, fact.fact_identity))
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda: CalendarFactSet("", "2026.1", _authority(), ()),
        lambda: CalendarFactSet("calendar-xpar", "", _authority(), ()),
        lambda: CalendarFactSet("calendar-xpar", "2026.1", cast(Any, object()), ()),
        lambda: CalendarFactSet("calendar-xpar", "2026.1", _authority(), cast(Any, [])),
        lambda: CalendarFactSet("calendar-xpar", "2026.1", _authority(), (cast(Any, object()),)),
        lambda: CalendarFactSet(
            "calendar-xpar",
            "2026.1",
            _authority(),
            (_fact(CalendarFactKind.HOLIDAY, calendar_identity="other"),),
        ),
        lambda: CalendarFactSet(
            "calendar-xpar",
            "2026.1",
            _authority(),
            (_fact(CalendarFactKind.HOLIDAY), _fact(CalendarFactKind.HOLIDAY)),
        ),
    ],
)
def test_calendar_fact_set_rejects_invalid_or_duplicate_facts(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_temporal_boundary_is_canonical_immutable_and_permutation_invariant() -> None:
    boundary = _boundary()
    permuted = _boundary(
        policy_versions=tuple(reversed(boundary.policy_versions)),
        authorities=tuple(reversed(boundary.authorities)),
    )
    assert boundary == permuted and hash(boundary) == hash(permuted)
    assert boundary.observation != boundary.publication
    with pytest.raises(FrozenInstanceError):
        boundary.knowledge = _instant(20)


@pytest.mark.parametrize(
    "changes",
    [
        {"boundary_identity": ""},
        {"observation": cast(Any, object())},
        {"validity": cast(Any, object())},
        {"validity": None, "validity_rule_reference": None},
        {"validity_rule_reference": "validity-rule-1"},
        {"publication": cast(Any, object())},
        {"availability": cast(Any, object())},
        {"knowledge": cast(Any, object())},
        {"revision": cast(Any, object())},
        {"expiration": cast(Any, object())},
        {"historical": cast(Any, object())},
        {"replay": cast(Any, object())},
        {"expiration": _instant(30)},
        {"expiration": None, "non_expiring_policy": None},
        {"timeframe_identity": "H1", "timeframe_version": None},
        {"calendar_identity": None, "calendar_version": "2026.1"},
        {"revision_lineage": cast(Any, [])},
        {"revision_lineage": ("revision-1", "revision-1")},
        {"visibility_constraints": cast(Any, [])},
        {"policy_versions": cast(Any, [])},
        {"policy_versions": cast(Any, (("temporal",),))},
        {"policy_versions": (("temporal", "1"), ("temporal", "1"))},
        {"policy_versions": ()},
        {"authorities": cast(Any, [])},
        {"authorities": ()},
        {"authorities": (cast(Any, object()),)},
        {"authorities": (_authority(), _authority())},
    ],
)
def test_temporal_boundary_rejects_missing_or_inconsistent_facts(
    changes: dict[str, object],
) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _boundary(**changes)


def test_boundary_accepts_explicit_rules_and_optional_temporal_dimensions() -> None:
    boundary = _boundary(
        validity=None,
        validity_rule_reference="validity-rule-1",
        expiration=_instant(50),
        non_expiring_policy=None,
        revision=_instant(14),
        historical=_instant(40),
        replay=_instant(41),
        timeframe_identity=None,
        timeframe_version=None,
        calendar_identity=None,
        calendar_version=None,
    )
    assert boundary.validity_rule_reference == "validity-rule-1"
    assert boundary.expiration == _instant(50)


def _diagnostic() -> TemporalDiagnosticReason:
    return TemporalDiagnosticReason(
        TemporalDiagnosticCode.FUTURE_LEAKAGE,
        "evidence-1",
        "source-boundary-1",
        "consumer-boundary-1",
        "H1@1.0.0",
        "calendar-xpar@2026.1",
        _instant(13),
        ("publication-1",),
        "temporal-policy-1",
        "availability exceeds knowledge boundary",
    )


def test_temporal_diagnostic_is_self_contained_immutable_and_hashable() -> None:
    diagnostic = _diagnostic()
    assert diagnostic == _diagnostic()
    assert hash(diagnostic) == hash(_diagnostic())
    with pytest.raises(FrozenInstanceError):
        diagnostic.reason = "changed"


@pytest.mark.parametrize(
    "changes",
    [
        {"code": cast(Any, "FUTURE_LEAKAGE")},
        {"affected_evidence": ""},
        {"source_boundary": ""},
        {"consumer_boundary": ""},
        {"policy_version": ""},
        {"reason": ""},
        {"timeframe_identity": ""},
        {"calendar_identity": ""},
        {"knowledge_boundary": cast(Any, object())},
        {"revision_lineage": cast(Any, [])},
    ],
)
def test_temporal_diagnostic_rejects_incomplete_context(changes: dict[str, object]) -> None:
    values: dict[str, object] = {
        "code": TemporalDiagnosticCode.FUTURE_LEAKAGE,
        "affected_evidence": "evidence-1",
        "source_boundary": "source-1",
        "consumer_boundary": "consumer-1",
        "timeframe_identity": None,
        "calendar_identity": None,
        "knowledge_boundary": _instant(),
        "revision_lineage": (),
        "policy_version": "1.0.0",
        "reason": "future leakage",
    }
    values.update(changes)
    with pytest.raises(DataIntegrityError):
        TemporalDiagnosticReason(**values)  # type: ignore[arg-type]


def test_e00_contains_no_successor_behavior() -> None:
    from epip.temporal import model

    forbidden = {
        "TimeframeContract",
        "TemporalMappingContract",
        "AvailabilityEvaluator",
        "ObservationValidator",
        "RevisionValidator",
        "TemporalDependencyValidator",
        "HistoricalVisibilityEvaluator",
        "TemporalCertification",
    }
    assert forbidden.isdisjoint(vars(model))
