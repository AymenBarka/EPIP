"""Component tests for A05-E01 deterministic timeframe interpretation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.governance import GovernanceEpoch
from epip.temporal.model import (
    CalendarFact,
    CalendarFactKind,
    CalendarFactSet,
    CanonicalInstant,
    CanonicalInterval,
    TemporalAuthorityReference,
    TemporalDiagnosticCode,
)
from epip.temporal.timeframe import (
    CanonicalTimeframe,
    SessionInclusionPolicy,
    TemporalMappingContract,
    TimeframeContract,
    TimeframeDiagnostics,
    TimeframeInterpreter,
    TimeframeKind,
)


def _instant(value: int = 125, **changes: object) -> CanonicalInstant:
    values: dict[str, object] = {
        "value": value,
        "precision": "second",
        "time_scale": "UTC",
        "timezone_basis": "UTC",
        "authority_identity": "clock-1",
    }
    values.update(changes)
    return CanonicalInstant(**values)  # type: ignore[arg-type]


def _temporal_authority(**changes: object) -> TemporalAuthorityReference:
    values: dict[str, object] = {
        "authority_identity": "temporal-authority-1",
        "authority_role": "temporal_architecture_authority",
        "authority_version": "1.0.0",
        "governance_epoch": GovernanceEpoch(5),
    }
    values.update(changes)
    return TemporalAuthorityReference(**values)  # type: ignore[arg-type]


def _calendar_authority(**changes: object) -> TemporalAuthorityReference:
    values: dict[str, object] = {
        "authority_identity": "calendar-authority-1",
        "authority_role": "calendar_authority",
        "authority_version": "2026.1",
        "governance_epoch": GovernanceEpoch(5),
    }
    values.update(changes)
    return TemporalAuthorityReference(**values)  # type: ignore[arg-type]


def _fact(
    identity: str,
    kind: CalendarFactKind,
    start: int,
    end: int,
    **changes: object,
) -> CalendarFact:
    values: dict[str, object] = {
        "fact_identity": identity,
        "kind": kind,
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "interval": CanonicalInterval(_instant(start), _instant(end)),
        "authority": _calendar_authority(),
        "policy_version": "calendar-policy-1",
        "session_identity": (
            identity
            if kind in {CalendarFactKind.SESSION, CalendarFactKind.SHORTENED_SESSION}
            else None
        ),
        "timezone_identity": "Europe/Paris" if kind is CalendarFactKind.TIMEZONE_RULE else None,
        "utc_offset_seconds": 3_600 if kind is CalendarFactKind.TIMEZONE_RULE else None,
        "reason": "exception" if kind is CalendarFactKind.EXCEPTIONAL_INTERVAL else None,
    }
    values.update(changes)
    return CalendarFact(**values)  # type: ignore[arg-type]


def _fact_set(facts: tuple[CalendarFact, ...] | None = None, **changes: object) -> CalendarFactSet:
    values: dict[str, object] = {
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "authority": _calendar_authority(),
        "facts": (
            facts
            if facts is not None
            else (
                _fact("timezone", CalendarFactKind.TIMEZONE_RULE, 0, 1_000),
                _fact("session-a", CalendarFactKind.SESSION, 0, 300),
                _fact("exception", CalendarFactKind.EXCEPTIONAL_INTERVAL, 100, 150),
            )
        ),
    }
    values.update(changes)
    return CalendarFactSet(**values)  # type: ignore[arg-type]


def _duration_contract(
    identity: str = "M1",
    duration: int = 60,
    **changes: object,
) -> TimeframeContract:
    values: dict[str, object] = {
        "timeframe_identity": identity,
        "timeframe_version": "1.0.0",
        "kind": TimeframeKind.DURATION,
        "duration_units": duration,
        "alignment_epoch": _instant(0),
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "session_policy": SessionInclusionPolicy.DECLARED_SESSIONS,
        "calendar_windows": (),
        "authority": _temporal_authority(),
        "policy_version": "timeframe-policy-1",
    }
    values.update(changes)
    return TimeframeContract(**values)  # type: ignore[arg-type]


def _calendar_contract(identity: str = "DAILY", **changes: object) -> TimeframeContract:
    values: dict[str, object] = {
        "timeframe_identity": identity,
        "timeframe_version": "1.0.0",
        "kind": TimeframeKind.CALENDAR,
        "duration_units": None,
        "alignment_epoch": None,
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "session_policy": SessionInclusionPolicy.DECLARED_WINDOWS,
        "calendar_windows": (("session-a", "exception"),),
        "authority": _temporal_authority(),
        "policy_version": "timeframe-policy-1",
    }
    values.update(changes)
    return TimeframeContract(**values)  # type: ignore[arg-type]


def _outcome(**changes: object) -> CanonicalTimeframe:
    values: dict[str, object] = {
        "timeframe_identity": "M1",
        "timeframe_version": "1.0.0",
        "interval": CanonicalInterval(_instant(120), _instant(180)),
        "calendar_identity": "calendar-xpar",
        "calendar_version": "2026.1",
        "session_policy": SessionInclusionPolicy.DECLARED_SESSIONS,
        "calendar_fact_identities": ("session-a", "exception", "timezone"),
        "authority": _temporal_authority(),
        "policy_version": "timeframe-policy-1",
    }
    values.update(changes)
    return CanonicalTimeframe(**values)  # type: ignore[arg-type]


def _mapping(**changes: object) -> TemporalMappingContract:
    values: dict[str, object] = {
        "mapping_identity": "mapping-m1-h1",
        "mapping_version": "1.0.0",
        "source_timeframe_identity": "M1",
        "source_timeframe_version": "1.0.0",
        "target_timeframe_identity": "H1",
        "target_timeframe_version": "1.0.0",
        "alignment_rule": "SOURCE_START_ALIGNED_TO_TARGET",
        "membership_rule": "SOURCE_INTERVAL_INCLUDED_BY_TARGET",
        "closure_requirement": "TARGET_CLOSED",
        "completeness_requirement": "ALL_DECLARED_MEMBERS_PRESENT",
        "visibility_rule": "KNOWLEDGE_BOUNDARY_ADMITTED",
        "revision_propagation_rule": "NEW_PLAN_REQUIRED",
        "conflict_rule": "FAIL_CLOSED",
        "authority": _temporal_authority(),
        "policy_version": "mapping-policy-1",
    }
    values.update(changes)
    return TemporalMappingContract(**values)  # type: ignore[arg-type]


def test_public_production_inventory_is_exact() -> None:
    from epip.temporal import timeframe

    public = {
        name
        for name, value in vars(timeframe).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and value.__module__ == timeframe.__name__
    }
    assert public == {
        "CanonicalTimeframe",
        "SessionInclusionPolicy",
        "TemporalMappingContract",
        "TimeframeContract",
        "TimeframeDiagnostics",
        "TimeframeInterpreter",
        "TimeframeKind",
    }


@pytest.mark.parametrize(
    ("identity", "duration"),
    [("M1", 60), ("M5", 300), ("M15", 900), ("M30", 1_800), ("H1", 3_600), ("H4", 14_400)],
)
def test_all_duration_timeframes_are_interpreted_from_the_declared_epoch(
    identity: str, duration: int
) -> None:
    contract = _duration_contract(
        identity,
        duration,
        session_policy=SessionInclusionPolicy.ALL_CANONICAL_TIME,
    )
    instant = _instant(duration * 2 + duration // 2)
    diagnostics = TimeframeInterpreter.interpret(contract, instant, _fact_set())
    outcome = diagnostics.canonical_timeframes[0]
    assert outcome.timeframe_identity == identity
    assert outcome.interval.start.value == duration * 2
    assert outcome.interval.end.value == duration * 3
    assert outcome.interval.boundary_convention.value == "START_INCLUSIVE_END_EXCLUSIVE"


def test_duration_alignment_is_deterministic_before_and_on_epoch() -> None:
    contract = _duration_contract(session_policy=SessionInclusionPolicy.ALL_CANONICAL_TIME)
    empty = _fact_set(())
    before = TimeframeInterpreter.interpret(contract, _instant(-1), empty)
    boundary = TimeframeInterpreter.interpret(contract, _instant(0), empty)
    assert before.canonical_timeframes[0].interval == CanonicalInterval(_instant(-60), _instant(0))
    assert boundary.canonical_timeframes[0].interval == CanonicalInterval(_instant(0), _instant(60))


@pytest.mark.parametrize(
    ("precision", "units_per_second"),
    [
        ("second", 1),
        ("millisecond", 1_000),
        ("microsecond", 1_000_000),
        ("nanosecond", 1_000_000_000),
    ],
)
def test_duration_preserves_declared_canonical_precision(
    precision: str,
    units_per_second: int,
) -> None:
    epoch = _instant(0, precision=precision)
    contract = _duration_contract(
        alignment_epoch=epoch,
        session_policy=SessionInclusionPolicy.ALL_CANONICAL_TIME,
    )
    instant = _instant(125 * units_per_second, precision=precision)
    result = TimeframeInterpreter.interpret(contract, instant, _fact_set(()))
    interval = result.canonical_timeframes[0].interval
    assert interval.start == _instant(120 * units_per_second, precision=precision)
    assert interval.end == _instant(180 * units_per_second, precision=precision)


def test_unsupported_duration_precision_fails_closed() -> None:
    contract = _duration_contract(
        alignment_epoch=_instant(0, precision="market-tick"),
        session_policy=SessionInclusionPolicy.ALL_CANONICAL_TIME,
    )
    with pytest.raises(DataIntegrityError, match="INVALID_PRECISION"):
        TimeframeInterpreter.interpret(
            contract,
            _instant(125, precision="market-tick"),
            _fact_set(()),
        )


@pytest.mark.parametrize("identity", ["DAILY", "WEEKLY", "MONTHLY"])
def test_all_calendar_timeframes_use_authoritative_declared_windows(identity: str) -> None:
    contract = _calendar_contract(identity)
    diagnostics = TimeframeInterpreter.interpret(contract, _instant(125), _fact_set())
    outcome = diagnostics.canonical_timeframes[0]
    assert outcome.timeframe_identity == identity
    assert outcome.interval == CanonicalInterval(_instant(0), _instant(300))
    assert outcome.calendar_fact_identities == ("exception", "session-a")


def test_shortened_session_and_timezone_facts_are_preserved() -> None:
    facts = _fact_set(
        (
            _fact("short", CalendarFactKind.SHORTENED_SESSION, 0, 200),
            _fact("tz", CalendarFactKind.TIMEZONE_RULE, 0, 200),
        )
    )
    contract = _calendar_contract(calendar_windows=(("tz", "short"),))
    result = TimeframeInterpreter.interpret(contract, _instant(100), facts)
    assert result.canonical_timeframes[0].calendar_fact_identities == ("short", "tz")


def test_contract_and_calendar_window_permutations_are_canonical() -> None:
    windows = (("session-b",), ("exception", "session-a"))
    facts = _fact_set(
        (
            _fact("session-a", CalendarFactKind.SESSION, 0, 300),
            _fact("exception", CalendarFactKind.EXCEPTIONAL_INTERVAL, 100, 150),
            _fact("session-b", CalendarFactKind.SESSION, 300, 600),
        )
    )
    expected_contract = _calendar_contract(calendar_windows=windows)
    expected = TimeframeInterpreter.interpret(expected_contract, _instant(125), facts)
    for outer in permutations(windows):
        permuted = tuple(tuple(reversed(window)) for window in outer)
        contract = _calendar_contract(calendar_windows=permuted)
        actual = TimeframeInterpreter.interpret(contract, _instant(125), facts)
        assert contract == expected_contract
        assert hash(contract) == hash(expected_contract)
        assert actual == expected
        assert hash(actual) == hash(expected)


def test_repeated_interpretation_preserves_inputs_and_outputs() -> None:
    contract = _duration_contract()
    instant = _instant()
    facts = _fact_set()
    snapshots = (hash(contract), hash(instant), hash(facts))
    results = tuple(TimeframeInterpreter.interpret(contract, instant, facts) for _ in range(5))
    assert all(result == results[0] for result in results)
    assert all(hash(result) == hash(results[0]) for result in results)
    assert snapshots == (hash(contract), hash(instant), hash(facts))


@pytest.mark.parametrize(
    "changes",
    [
        {"timeframe_identity": ""},
        {"timeframe_version": ""},
        {"calendar_identity": ""},
        {"calendar_version": ""},
        {"policy_version": ""},
        {"kind": cast(Any, "DURATION")},
        {"session_policy": cast(Any, "DECLARED_SESSIONS")},
        {"authority": cast(Any, object())},
        {"authority": _calendar_authority()},
        {"calendar_windows": cast(Any, [])},
        {"calendar_windows": (("session-a", "session-a"),)},
        {"calendar_windows": ((),)},
        {"calendar_windows": (("session-a",), ("session-a",))},
        {"calendar_windows": (("session-a",), ("session-a", "exception"))},
    ],
)
def test_contract_rejects_invalid_common_facts(changes: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        cast(Any, _duration_contract)(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"timeframe_identity": "M2"},
        {"duration_units": None},
        {"duration_units": True},
        {"duration_units": 0},
        {"duration_units": 61},
        {"alignment_epoch": None},
        {"calendar_windows": (("session-a",),)},
        {"session_policy": SessionInclusionPolicy.DECLARED_WINDOWS},
    ],
)
def test_duration_contract_fails_closed_on_unsupported_declarations(
    changes: dict[str, object],
) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        cast(Any, _duration_contract)(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"timeframe_identity": "YEARLY"},
        {"duration_units": 60},
        {"alignment_epoch": _instant(0)},
        {"session_policy": SessionInclusionPolicy.ALL_CANONICAL_TIME},
        {"calendar_windows": ()},
    ],
)
def test_calendar_contract_fails_closed_on_unsupported_declarations(
    changes: dict[str, object],
) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        cast(Any, _calendar_contract)(**changes)


def test_interpret_rejects_invalid_inputs_and_calendar_binding() -> None:
    with pytest.raises(DataIntegrityError, match="contract is invalid"):
        TimeframeInterpreter.interpret(cast(Any, object()), _instant(), _fact_set())
    with pytest.raises(DataIntegrityError, match="INVALID_CANONICAL_INSTANT"):
        TimeframeInterpreter.interpret(_duration_contract(), cast(Any, object()), _fact_set())
    with pytest.raises(DataIntegrityError, match="CalendarFactSet"):
        TimeframeInterpreter.interpret(_duration_contract(), _instant(), cast(Any, object()))
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_CALENDAR"):
        TimeframeInterpreter.interpret(
            _duration_contract(),
            _instant(),
            _fact_set((), calendar_version="other"),
        )


def test_calendar_authority_and_canonical_basis_fail_closed() -> None:
    unauthorized = _fact_set(
        (),
        authority=_calendar_authority(authority_role="source_authority"),
    )
    with pytest.raises(DataIntegrityError, match="Calendar Authority"):
        TimeframeInterpreter.interpret(_duration_contract(), _instant(), unauthorized)
    with pytest.raises(DataIntegrityError, match="INVALID_PRECISION"):
        TimeframeInterpreter.interpret(
            _duration_contract(alignment_epoch=_instant(0, precision="millisecond")),
            _instant(),
            _fact_set(),
        )


def test_session_and_closure_policies_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="UNKNOWN_SESSION"):
        TimeframeInterpreter.interpret(_duration_contract(), _instant(), _fact_set(()))
    closed = _fact_set((_fact("closed", CalendarFactKind.MARKET_CLOSURE, 100, 200),))
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_CALENDAR"):
        TimeframeInterpreter.interpret(
            _duration_contract(session_policy=SessionInclusionPolicy.ALL_CANONICAL_TIME),
            _instant(),
            closed,
        )


def test_calendar_windows_fail_closed_when_missing_ambiguous_or_closed() -> None:
    with pytest.raises(DataIntegrityError, match="UNKNOWN_CALENDAR"):
        TimeframeInterpreter.interpret(
            _calendar_contract(calendar_windows=(("absent",),)),
            _instant(),
            _fact_set(),
        )
    with pytest.raises(DataIntegrityError, match="MISSING_INTERVAL"):
        TimeframeInterpreter.interpret(_calendar_contract(), _instant(500), _fact_set())
    overlapping = _fact_set(
        (
            _fact("session-a", CalendarFactKind.SESSION, 0, 300),
            _fact("session-b", CalendarFactKind.SESSION, 100, 400),
        )
    )
    with pytest.raises(DataIntegrityError, match="UNEXPECTED_INTERVAL_OVERLAP"):
        TimeframeInterpreter.interpret(
            _calendar_contract(calendar_windows=(("session-a",), ("session-b",))),
            _instant(),
            overlapping,
        )
    closed = _fact_set((_fact("closed", CalendarFactKind.HOLIDAY, 100, 200),))
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_CALENDAR"):
        TimeframeInterpreter.interpret(
            _calendar_contract(calendar_windows=(("closed",),)),
            _instant(),
            closed,
        )


def test_calendar_window_rejects_mixed_canonical_bases() -> None:
    facts = _fact_set(
        (
            _fact("session-a", CalendarFactKind.SESSION, 0, 300),
            _fact(
                "session-b",
                CalendarFactKind.SESSION,
                300,
                600,
                interval=CanonicalInterval(
                    _instant(300, authority_identity="clock-2"),
                    _instant(600, authority_identity="clock-2"),
                ),
            ),
        )
    )
    contract = _calendar_contract(calendar_windows=(("session-a", "session-b"),))
    with pytest.raises(DataIntegrityError, match="INVALID_PRECISION"):
        TimeframeInterpreter.interpret(contract, _instant(), facts)


def test_mapping_production_preserves_every_authoritative_rule() -> None:
    source = _duration_contract()
    target = _duration_contract("H1", 3_600)
    first = TimeframeInterpreter.produce_mapping(
        source,
        target,
        mapping_identity="mapping-m1-h1",
        mapping_version="1.0.0",
        alignment_rule="SOURCE_START_ALIGNED_TO_TARGET",
        membership_rule="SOURCE_INTERVAL_INCLUDED_BY_TARGET",
        closure_requirement="TARGET_CLOSED",
        completeness_requirement="ALL_DECLARED_MEMBERS_PRESENT",
        visibility_rule="KNOWLEDGE_BOUNDARY_ADMITTED",
        revision_propagation_rule="NEW_PLAN_REQUIRED",
        conflict_rule="FAIL_CLOSED",
        authority=_temporal_authority(),
        policy_version="mapping-policy-1",
    )
    second = TimeframeInterpreter.produce_mapping(
        source,
        target,
        mapping_identity="mapping-m1-h1",
        mapping_version="1.0.0",
        alignment_rule="SOURCE_START_ALIGNED_TO_TARGET",
        membership_rule="SOURCE_INTERVAL_INCLUDED_BY_TARGET",
        closure_requirement="TARGET_CLOSED",
        completeness_requirement="ALL_DECLARED_MEMBERS_PRESENT",
        visibility_rule="KNOWLEDGE_BOUNDARY_ADMITTED",
        revision_propagation_rule="NEW_PLAN_REQUIRED",
        conflict_rule="FAIL_CLOSED",
        authority=_temporal_authority(),
        policy_version="mapping-policy-1",
    )
    assert first == second and hash(first) == hash(second)
    assert first.mapping_contracts == (_mapping(),)


def test_mapping_rejects_invalid_endpoints_authority_and_identity() -> None:
    source = _duration_contract()
    target = _duration_contract("H1", 3_600)
    arguments: dict[str, object] = {
        "mapping_identity": "mapping-m1-h1",
        "mapping_version": "1.0.0",
        "alignment_rule": "aligned",
        "membership_rule": "included",
        "closure_requirement": "closed",
        "completeness_requirement": "complete",
        "visibility_rule": "visible",
        "revision_propagation_rule": "new-plan",
        "conflict_rule": "fail",
        "authority": _temporal_authority(),
        "policy_version": "1.0.0",
    }
    with pytest.raises(DataIntegrityError, match="mapping endpoints"):
        TimeframeInterpreter.produce_mapping(cast(Any, object()), target, **arguments)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="temporal architecture authority"):
        TimeframeInterpreter.produce_mapping(
            source,
            target,
            **{**arguments, "authority": _calendar_authority()},  # type: ignore[arg-type]
        )
    other_authority = _temporal_authority(authority_identity="other")
    with pytest.raises(DataIntegrityError, match="does not bind"):
        TimeframeInterpreter.produce_mapping(
            source,
            target,
            **{**arguments, "authority": other_authority},  # type: ignore[arg-type]
        )
    with pytest.raises(DataIntegrityError, match="different timeframe"):
        TimeframeInterpreter.produce_mapping(source, source, **arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field",
    [
        "mapping_identity",
        "mapping_version",
        "source_timeframe_identity",
        "source_timeframe_version",
        "target_timeframe_identity",
        "target_timeframe_version",
        "alignment_rule",
        "membership_rule",
        "closure_requirement",
        "completeness_requirement",
        "visibility_rule",
        "revision_propagation_rule",
        "conflict_rule",
        "policy_version",
    ],
)
def test_mapping_contract_rejects_missing_text(field: str) -> None:
    with pytest.raises(DataIntegrityError):
        _mapping(**{field: ""})


def test_mapping_contract_rejects_invalid_authority() -> None:
    with pytest.raises(DataIntegrityError):
        _mapping(authority=cast(Any, object()))


@pytest.mark.parametrize(
    "changes",
    [
        {"timeframe_identity": ""},
        {"timeframe_version": ""},
        {"interval": cast(Any, object())},
        {"calendar_identity": ""},
        {"calendar_version": ""},
        {"session_policy": cast(Any, "DECLARED_SESSIONS")},
        {"calendar_fact_identities": cast(Any, [])},
        {"calendar_fact_identities": ("session-a", "session-a")},
        {"authority": cast(Any, object())},
        {"policy_version": ""},
    ],
)
def test_canonical_outcome_rejects_invalid_context(changes: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError):
        _outcome(**changes)


def test_diagnostics_are_canonical_immutable_hashable_and_permutation_invariant() -> None:
    outcomes = (_outcome(), _outcome(timeframe_identity="M5"))
    mappings = (_mapping(), _mapping(mapping_identity="mapping-m5-h1"))
    expected = TimeframeDiagnostics(
        outcomes,
        mappings,
        (TemporalDiagnosticCode.UNKNOWN_TIMEFRAME, TemporalDiagnosticCode.MISSING_INTERVAL),
        ("unknown", "missing"),
    )
    for outcome_order in permutations(outcomes):
        for mapping_order in permutations(mappings):
            actual = TimeframeDiagnostics(
                outcome_order,
                mapping_order,
                tuple(reversed(expected.codes)),
                tuple(reversed(expected.reasons)),
            )
            assert actual == expected
            assert hash(actual) == hash(expected)
    with pytest.raises(FrozenInstanceError):
        expected.codes = ()


def test_equal_partial_key_outcomes_have_total_canonical_ordering() -> None:
    utc = _outcome(
        interval=CanonicalInterval(
            _instant(120, time_scale="UTC"),
            _instant(180, time_scale="UTC"),
        )
    )
    tai = _outcome(
        interval=CanonicalInterval(
            _instant(120, time_scale="TAI"),
            _instant(180, time_scale="TAI"),
        )
    )
    expected = TimeframeDiagnostics((utc, tai), ())
    actual = TimeframeDiagnostics((tai, utc), ())
    assert actual == expected
    assert hash(actual) == hash(expected)
    assert actual.canonical_timeframes == expected.canonical_timeframes


def test_equal_partial_key_mappings_have_total_canonical_ordering() -> None:
    aligned = _mapping(alignment_rule="ALIGNED")
    contained = _mapping(alignment_rule="CONTAINED")
    expected = TimeframeDiagnostics((), (aligned, contained))
    actual = TimeframeDiagnostics((), (contained, aligned))
    assert actual == expected
    assert hash(actual) == hash(expected)
    assert actual.mapping_contracts == expected.mapping_contracts


def test_equal_code_diagnostic_pairs_have_total_canonical_ordering() -> None:
    code = TemporalDiagnosticCode.UNKNOWN_TIMEFRAME
    expected = TimeframeDiagnostics((), (), (code, code), ("alpha", "beta"))
    actual = TimeframeDiagnostics((), (), (code, code), ("beta", "alpha"))
    assert actual == expected
    assert hash(actual) == hash(expected)
    assert tuple(zip(actual.codes, actual.reasons)) == (
        (code, "alpha"),
        (code, "beta"),
    )


def test_corrected_canonicalization_is_identical_across_repeated_permutations() -> None:
    outcomes = (
        _outcome(),
        _outcome(interval=CanonicalInterval(_instant(120), _instant(181))),
    )
    mappings = (_mapping(alignment_rule="A"), _mapping(alignment_rule="B"))
    results = tuple(
        TimeframeDiagnostics(
            tuple(reversed(outcomes)) if index % 2 else outcomes,
            tuple(reversed(mappings)) if index % 2 else mappings,
            (
                TemporalDiagnosticCode.UNKNOWN_TIMEFRAME,
                TemporalDiagnosticCode.UNKNOWN_TIMEFRAME,
            ),
            ("beta", "alpha") if index % 2 else ("alpha", "beta"),
        )
        for index in range(6)
    )
    assert all(item == results[0] for item in results)
    assert all(hash(item) == hash(results[0]) for item in results)


@pytest.mark.parametrize(
    "call",
    [
        lambda: TimeframeDiagnostics(cast(Any, []), ()),
        lambda: TimeframeDiagnostics((cast(Any, object()),), ()),
        lambda: TimeframeDiagnostics((), cast(Any, [])),
        lambda: TimeframeDiagnostics((), (cast(Any, object()),)),
        lambda: TimeframeDiagnostics((), (), cast(Any, []), ()),
        lambda: TimeframeDiagnostics((), (), (cast(Any, "UNKNOWN"),), ("reason",)),
        lambda: TimeframeDiagnostics((), (), (), cast(Any, [])),
        lambda: TimeframeDiagnostics((), (), (), ("",)),
        lambda: TimeframeDiagnostics((), (), (TemporalDiagnosticCode.UNKNOWN_TIMEFRAME,), ()),
        lambda: TimeframeDiagnostics((_outcome(), _outcome()), ()),
        lambda: TimeframeDiagnostics((), (_mapping(), _mapping())),
    ],
)
def test_diagnostics_reject_invalid_or_duplicate_context(call: object) -> None:
    with pytest.raises(DataIntegrityError):
        cast(Any, call)()


def test_all_outputs_are_immutable_and_hashable() -> None:
    values: tuple[object, ...] = (
        _duration_contract(),
        _outcome(),
        _mapping(),
        TimeframeDiagnostics((_outcome(),), (_mapping(),)),
    )
    assert all(hash(value) for value in values)
    assert _duration_contract() != object()
    for value in values:
        with pytest.raises(FrozenInstanceError):
            cast(Any, value).policy_version = "changed"


def test_e01_contains_no_successor_or_predecessor_responsibilities() -> None:
    from epip.temporal import timeframe

    forbidden = {
        "AvailabilityAnalyzer",
        "ObservationValidator",
        "CompletenessValidator",
        "TemporalDependencyValidator",
        "RevisionValidator",
        "ReplayCompatibilityValidator",
        "TemporalCertification",
        "TemporalClosure",
        "EvidenceProducer",
        "DependencyGraphBuilder",
    }
    assert forbidden.isdisjoint(vars(timeframe))
