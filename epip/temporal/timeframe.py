"""Deterministic A05-E01 timeframe interpretation and mapping facts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum
from typing import ClassVar, NoReturn

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.temporal.model import (
    CalendarFact,
    CalendarFactKind,
    CalendarFactSet,
    CanonicalInstant,
    CanonicalInterval,
    TemporalAuthorityReference,
    TemporalDiagnosticCode,
)


class _ImmutableRecord:
    """Immutable value-record support local to the E01 ownership boundary."""

    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable timeframe model")

    def _initialize(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _ImmutableRecord)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


def _reject(code: TemporalDiagnosticCode, reason: str) -> NoReturn:
    raise DataIntegrityError(f"{code.value}: {reason}")


def _require_text(value: object, field: str) -> str:
    return require_text(value, field)


def _require_positive_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DataIntegrityError(f"{field} must be a positive integer")
    return value


def _require_authority(value: object, field: str) -> TemporalAuthorityReference:
    if not isinstance(value, TemporalAuthorityReference):
        raise DataIntegrityError(f"{field} must be a TemporalAuthorityReference")
    if value.authority_role != "temporal_architecture_authority":
        raise DataIntegrityError(f"{field} must belong to the temporal architecture authority")
    return value


def _require_string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    for item in value:
        _require_text(item, field)
    if len(set(value)) != len(value):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return tuple(sorted(value))


def _require_calendar_windows(
    value: object,
) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("timeframe.calendar_windows must be an immutable tuple")
    windows: list[tuple[str, ...]] = []
    for window in value:
        canonical = _require_string_tuple(window, "timeframe.calendar_window")
        if not canonical:
            raise MissingFieldError("timeframe calendar windows must not be empty")
        windows.append(canonical)
    if len(set(windows)) != len(windows):
        raise DataIntegrityError("timeframe calendar windows must not contain duplicates")
    flattened = tuple(identity for window in windows for identity in window)
    if len(set(flattened)) != len(flattened):
        raise DataIntegrityError("calendar facts must belong to exactly one timeframe window")
    return tuple(sorted(windows))


def _instant_basis(instant: CanonicalInstant) -> tuple[str, str, str, str]:
    return (
        instant.precision,
        instant.time_scale,
        instant.timezone_basis,
        instant.authority_identity,
    )


def _same_basis(left: CanonicalInstant, right: CanonicalInstant) -> bool:
    return _instant_basis(left) == _instant_basis(right)


def _contains(interval: CanonicalInterval, instant: CanonicalInstant) -> bool:
    return (
        _same_basis(interval.start, instant)
        and interval.start.value <= instant.value < interval.end.value
    )


class TimeframeKind(str, Enum):
    """The two governed ADR-EPIP017-05 timeframe families."""

    DURATION = "DURATION"
    CALENDAR = "CALENDAR"


class SessionInclusionPolicy(str, Enum):
    """Explicit calendar/session inclusion policies interpreted by E01."""

    ALL_CANONICAL_TIME = "ALL_CANONICAL_TIME"
    DECLARED_SESSIONS = "DECLARED_SESSIONS"
    DECLARED_WINDOWS = "DECLARED_WINDOWS"


_DURATION_TIMEFRAMES: dict[str, int] = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1_800,
    "H1": 3_600,
    "H4": 14_400,
}
_CALENDAR_TIMEFRAMES = frozenset({"DAILY", "WEEKLY", "MONTHLY"})
_UNITS_PER_SECOND: dict[str, int] = {
    "second": 1,
    "millisecond": 1_000,
    "microsecond": 1_000_000,
    "nanosecond": 1_000_000_000,
}


def _authority_key(authority: TemporalAuthorityReference) -> tuple[str, str, str, int]:
    return (
        authority.authority_identity,
        authority.authority_role,
        authority.authority_version,
        authority.governance_epoch.sequence,
    )


def _canonical_instant_key(instant: CanonicalInstant) -> tuple[int, str, str, str, str]:
    return (
        instant.value,
        instant.precision,
        instant.time_scale,
        instant.timezone_basis,
        instant.authority_identity,
    )


def _canonical_interval_key(
    interval: CanonicalInterval,
) -> tuple[tuple[int, str, str, str, str], tuple[int, str, str, str, str], str]:
    return (
        _canonical_instant_key(interval.start),
        _canonical_instant_key(interval.end),
        interval.boundary_convention.value,
    )


def _canonical_timeframe_key(item: CanonicalTimeframe) -> tuple[object, ...]:
    return (
        item.timeframe_identity,
        item.timeframe_version,
        _canonical_interval_key(item.interval),
        item.calendar_identity,
        item.calendar_version,
        item.session_policy.value,
        item.calendar_fact_identities,
        _authority_key(item.authority),
        item.policy_version,
    )


def _mapping_key(item: TemporalMappingContract) -> tuple[object, ...]:
    return (
        item.mapping_identity,
        item.mapping_version,
        item.source_timeframe_identity,
        item.source_timeframe_version,
        item.target_timeframe_identity,
        item.target_timeframe_version,
        item.alignment_rule,
        item.membership_rule,
        item.closure_requirement,
        item.completeness_requirement,
        item.visibility_rule,
        item.revision_propagation_rule,
        item.conflict_rule,
        _authority_key(item.authority),
        item.policy_version,
    )


class TimeframeContract(_ImmutableRecord):
    """Immutable declaration of one governed timeframe contract."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "timeframe_identity",
        "timeframe_version",
        "kind",
        "duration_units",
        "alignment_epoch",
        "calendar_identity",
        "calendar_version",
        "session_policy",
        "calendar_windows",
        "authority",
        "policy_version",
    )
    _field_names = __slots__

    timeframe_identity: str
    timeframe_version: str
    kind: TimeframeKind
    duration_units: int | None
    alignment_epoch: CanonicalInstant | None
    calendar_identity: str
    calendar_version: str
    session_policy: SessionInclusionPolicy
    calendar_windows: tuple[tuple[str, ...], ...]
    authority: TemporalAuthorityReference
    policy_version: str

    def __init__(
        self,
        timeframe_identity: str,
        timeframe_version: str,
        kind: TimeframeKind,
        duration_units: int | None,
        alignment_epoch: CanonicalInstant | None,
        calendar_identity: str,
        calendar_version: str,
        session_policy: SessionInclusionPolicy,
        calendar_windows: tuple[tuple[str, ...], ...],
        authority: TemporalAuthorityReference,
        policy_version: str,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "timeframe_identity",
            "timeframe_version",
            "calendar_identity",
            "calendar_version",
            "policy_version",
        ):
            _require_text(getattr(self, name), f"timeframe.{name}")
        if not isinstance(self.kind, TimeframeKind):
            raise DataIntegrityError("timeframe.kind is unsupported")
        if not isinstance(self.session_policy, SessionInclusionPolicy):
            raise DataIntegrityError("timeframe.session_policy is unsupported")
        _require_authority(self.authority, "timeframe.authority")
        canonical_windows = _require_calendar_windows(self.calendar_windows)
        if self.kind is TimeframeKind.DURATION:
            expected = _DURATION_TIMEFRAMES.get(self.timeframe_identity)
            if expected is None:
                _reject(TemporalDiagnosticCode.UNKNOWN_TIMEFRAME, "duration timeframe is unknown")
            if self.duration_units is None:
                raise MissingFieldError("duration timeframe requires duration_units")
            if (
                _require_positive_integer(self.duration_units, "timeframe.duration_units")
                != expected
            ):
                _reject(
                    TemporalDiagnosticCode.INCOMPATIBLE_TIMEFRAME,
                    "duration does not match the governed timeframe identity",
                )
            if not isinstance(self.alignment_epoch, CanonicalInstant):
                raise MissingFieldError("duration timeframe requires a canonical alignment epoch")
            if canonical_windows:
                raise DataIntegrityError("duration timeframe must not declare calendar windows")
            if self.session_policy is SessionInclusionPolicy.DECLARED_WINDOWS:
                raise DataIntegrityError("duration timeframe cannot use declared-window policy")
        else:
            if self.timeframe_identity not in _CALENDAR_TIMEFRAMES:
                _reject(TemporalDiagnosticCode.UNKNOWN_TIMEFRAME, "calendar timeframe is unknown")
            if self.duration_units is not None or self.alignment_epoch is not None:
                raise DataIntegrityError("calendar timeframe must not declare duration alignment")
            if self.session_policy is not SessionInclusionPolicy.DECLARED_WINDOWS:
                raise DataIntegrityError("calendar timeframe requires declared-window policy")
            if not canonical_windows:
                raise MissingFieldError(
                    "calendar timeframe requires authoritative calendar windows"
                )
        object.__setattr__(self, "calendar_windows", canonical_windows)


class CanonicalTimeframe(_ImmutableRecord):
    """One immutable canonical interval determined from a timeframe contract."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "timeframe_identity",
        "timeframe_version",
        "interval",
        "calendar_identity",
        "calendar_version",
        "session_policy",
        "calendar_fact_identities",
        "authority",
        "policy_version",
    )
    _field_names = __slots__

    timeframe_identity: str
    timeframe_version: str
    interval: CanonicalInterval
    calendar_identity: str
    calendar_version: str
    session_policy: SessionInclusionPolicy
    calendar_fact_identities: tuple[str, ...]
    authority: TemporalAuthorityReference
    policy_version: str

    def __init__(
        self,
        timeframe_identity: str,
        timeframe_version: str,
        interval: CanonicalInterval,
        calendar_identity: str,
        calendar_version: str,
        session_policy: SessionInclusionPolicy,
        calendar_fact_identities: tuple[str, ...],
        authority: TemporalAuthorityReference,
        policy_version: str,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "timeframe_identity",
            "timeframe_version",
            "calendar_identity",
            "calendar_version",
            "policy_version",
        ):
            _require_text(getattr(self, name), f"canonical_timeframe.{name}")
        if not isinstance(self.interval, CanonicalInterval):
            raise DataIntegrityError("canonical_timeframe.interval is invalid")
        if not isinstance(self.session_policy, SessionInclusionPolicy):
            raise DataIntegrityError("canonical_timeframe.session_policy is unsupported")
        _require_authority(self.authority, "canonical_timeframe.authority")
        object.__setattr__(
            self,
            "calendar_fact_identities",
            _require_string_tuple(
                self.calendar_fact_identities,
                "canonical_timeframe.calendar_fact_identities",
            ),
        )


class TemporalMappingContract(_ImmutableRecord):
    """Immutable versioned cross-timeframe semantic mapping fact."""

    __slots__ = (  # noqa: RUF023 - semantic field order
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
        "authority",
        "policy_version",
    )
    _field_names = __slots__

    mapping_identity: str
    mapping_version: str
    source_timeframe_identity: str
    source_timeframe_version: str
    target_timeframe_identity: str
    target_timeframe_version: str
    alignment_rule: str
    membership_rule: str
    closure_requirement: str
    completeness_requirement: str
    visibility_rule: str
    revision_propagation_rule: str
    conflict_rule: str
    authority: TemporalAuthorityReference
    policy_version: str

    def __init__(
        self,
        mapping_identity: str,
        mapping_version: str,
        source_timeframe_identity: str,
        source_timeframe_version: str,
        target_timeframe_identity: str,
        target_timeframe_version: str,
        alignment_rule: str,
        membership_rule: str,
        closure_requirement: str,
        completeness_requirement: str,
        visibility_rule: str,
        revision_propagation_rule: str,
        conflict_rule: str,
        authority: TemporalAuthorityReference,
        policy_version: str,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in self._field_names:
            value = getattr(self, name)
            if name == "authority":
                _require_authority(value, "temporal_mapping.authority")
            else:
                _require_text(value, f"temporal_mapping.{name}")
        if (
            self.source_timeframe_identity == self.target_timeframe_identity
            and self.source_timeframe_version == self.target_timeframe_version
        ):
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "mapping endpoints must identify different timeframe contracts",
            )


class TimeframeDiagnostics(_ImmutableRecord):
    """Immutable canonical E01 result and diagnostic context."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "canonical_timeframes",
        "mapping_contracts",
        "codes",
        "reasons",
    )
    _field_names = __slots__

    canonical_timeframes: tuple[CanonicalTimeframe, ...]
    mapping_contracts: tuple[TemporalMappingContract, ...]
    codes: tuple[TemporalDiagnosticCode, ...]
    reasons: tuple[str, ...]

    def __init__(
        self,
        canonical_timeframes: tuple[CanonicalTimeframe, ...],
        mapping_contracts: tuple[TemporalMappingContract, ...],
        codes: tuple[TemporalDiagnosticCode, ...] = (),
        reasons: tuple[str, ...] = (),
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.canonical_timeframes, tuple) or any(
            not isinstance(item, CanonicalTimeframe) for item in self.canonical_timeframes
        ):
            raise DataIntegrityError("timeframe diagnostics require immutable canonical outcomes")
        if not isinstance(self.mapping_contracts, tuple) or any(
            not isinstance(item, TemporalMappingContract) for item in self.mapping_contracts
        ):
            raise DataIntegrityError("timeframe diagnostics require immutable mapping contracts")
        if not isinstance(self.codes, tuple) or any(
            not isinstance(item, TemporalDiagnosticCode) for item in self.codes
        ):
            raise DataIntegrityError("timeframe diagnostics contain unsupported codes")
        if not isinstance(self.reasons, tuple):
            raise DataIntegrityError("timeframe_diagnostics.reasons must be an immutable tuple")
        for reason in self.reasons:
            _require_text(reason, "timeframe_diagnostics.reasons")
        canonical_reasons = self.reasons
        if len(self.codes) != len(canonical_reasons):
            raise DataIntegrityError("timeframe diagnostic codes and reasons must be paired")
        timeframes = tuple(
            sorted(
                self.canonical_timeframes,
                key=_canonical_timeframe_key,
            )
        )
        mappings = tuple(
            sorted(
                self.mapping_contracts,
                key=_mapping_key,
            )
        )
        if len(set(timeframes)) != len(timeframes) or len(set(mappings)) != len(mappings):
            raise DataIntegrityError("timeframe diagnostics must not contain duplicate outcomes")
        paired = tuple(
            sorted(
                zip(self.codes, canonical_reasons),
                key=lambda item: (item[0].value, item[1]),
            )
        )
        object.__setattr__(self, "canonical_timeframes", timeframes)
        object.__setattr__(self, "mapping_contracts", mappings)
        object.__setattr__(self, "codes", tuple(item[0] for item in paired))
        object.__setattr__(self, "reasons", tuple(item[1] for item in paired))


class TimeframeInterpreter:
    """Interpret frozen timeframe declarations without successor-package behavior."""

    __slots__ = ()

    @staticmethod
    def _calendar_facts(
        contract: TimeframeContract,
        facts: CalendarFactSet,
    ) -> dict[str, CalendarFact]:
        if not isinstance(facts, CalendarFactSet):
            raise DataIntegrityError("calendar facts must be an immutable CalendarFactSet")
        if (
            facts.calendar_identity != contract.calendar_identity
            or facts.calendar_version != contract.calendar_version
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPATIBLE_CALENDAR,
                "calendar facts do not match the timeframe contract",
            )
        if facts.authority.authority_role != "calendar_authority":
            _reject(
                TemporalDiagnosticCode.INCOMPATIBLE_CALENDAR,
                "calendar facts do not belong to the Calendar Authority",
            )
        return {fact.fact_identity: fact for fact in facts.facts}

    @staticmethod
    def _duration_interval(
        contract: TimeframeContract,
        instant: CanonicalInstant,
    ) -> CanonicalInterval:
        assert contract.duration_units is not None
        assert contract.alignment_epoch is not None
        epoch = contract.alignment_epoch
        if not _same_basis(epoch, instant):
            _reject(
                TemporalDiagnosticCode.INVALID_PRECISION,
                "observation and alignment epoch use incompatible canonical bases",
            )
        units_per_second = _UNITS_PER_SECOND.get(instant.precision)
        if units_per_second is None:
            _reject(
                TemporalDiagnosticCode.INVALID_PRECISION,
                "canonical precision does not support governed duration timeframes",
            )
        duration = contract.duration_units * units_per_second
        offset = instant.value - epoch.value
        start_value = epoch.value + (offset // duration) * duration
        start = CanonicalInstant(
            start_value,
            instant.precision,
            instant.time_scale,
            instant.timezone_basis,
            instant.authority_identity,
        )
        end = CanonicalInstant(
            start_value + duration,
            instant.precision,
            instant.time_scale,
            instant.timezone_basis,
            instant.authority_identity,
        )
        return CanonicalInterval(start, end)

    @staticmethod
    def _applicable_facts(
        instant: CanonicalInstant,
        facts: tuple[CalendarFact, ...],
    ) -> tuple[CalendarFact, ...]:
        return tuple(fact for fact in facts if _contains(fact.interval, instant))

    @classmethod
    def _interpret_duration(
        cls,
        contract: TimeframeContract,
        instant: CanonicalInstant,
        facts: CalendarFactSet,
    ) -> CanonicalTimeframe:
        fact_index = cls._calendar_facts(contract, facts)
        applicable = cls._applicable_facts(instant, tuple(fact_index.values()))
        if any(
            fact.kind in {CalendarFactKind.HOLIDAY, CalendarFactKind.MARKET_CLOSURE}
            for fact in applicable
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPATIBLE_CALENDAR,
                "observation falls inside an authoritative closed calendar interval",
            )
        if contract.session_policy is SessionInclusionPolicy.DECLARED_SESSIONS and not any(
            fact.kind in {CalendarFactKind.SESSION, CalendarFactKind.SHORTENED_SESSION}
            for fact in applicable
        ):
            _reject(
                TemporalDiagnosticCode.UNKNOWN_SESSION,
                "observation is outside every declared session",
            )
        return CanonicalTimeframe(
            contract.timeframe_identity,
            contract.timeframe_version,
            cls._duration_interval(contract, instant),
            contract.calendar_identity,
            contract.calendar_version,
            contract.session_policy,
            tuple(fact.fact_identity for fact in applicable),
            contract.authority,
            contract.policy_version,
        )

    @classmethod
    def _interpret_calendar(
        cls,
        contract: TimeframeContract,
        instant: CanonicalInstant,
        facts: CalendarFactSet,
    ) -> CanonicalTimeframe:
        fact_index = cls._calendar_facts(contract, facts)
        applicable = cls._applicable_facts(instant, tuple(fact_index.values()))
        if any(
            fact.kind in {CalendarFactKind.HOLIDAY, CalendarFactKind.MARKET_CLOSURE}
            for fact in applicable
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPATIBLE_CALENDAR,
                "observation falls inside an authoritative closed calendar interval",
            )
        windows: list[tuple[tuple[str, ...], tuple[CalendarFact, ...]]] = []
        for identities in contract.calendar_windows:
            try:
                members = tuple(fact_index[identity] for identity in identities)
            except KeyError:
                _reject(
                    TemporalDiagnosticCode.UNKNOWN_CALENDAR,
                    "timeframe window references an absent calendar fact",
                )
            if any(_contains(fact.interval, instant) for fact in members):
                windows.append((identities, members))
        if not windows:
            _reject(
                TemporalDiagnosticCode.MISSING_INTERVAL,
                "no authoritative calendar window contains the observation",
            )
        if len(windows) != 1:
            _reject(
                TemporalDiagnosticCode.UNEXPECTED_INTERVAL_OVERLAP,
                "multiple authoritative calendar windows contain the observation",
            )
        identities, members = windows[0]
        starts = tuple(fact.interval.start for fact in members)
        ends = tuple(fact.interval.end for fact in members)
        if any(not _same_basis(starts[0], item) for item in starts[1:] + ends):
            _reject(
                TemporalDiagnosticCode.INVALID_PRECISION,
                "calendar window facts use incompatible canonical bases",
            )
        start = min(starts, key=lambda item: item.value)
        end = max(ends, key=lambda item: item.value)
        return CanonicalTimeframe(
            contract.timeframe_identity,
            contract.timeframe_version,
            CanonicalInterval(start, end),
            contract.calendar_identity,
            contract.calendar_version,
            contract.session_policy,
            identities,
            contract.authority,
            contract.policy_version,
        )

    @classmethod
    def interpret(
        cls,
        contract: TimeframeContract,
        instant: CanonicalInstant,
        calendar_facts: CalendarFactSet,
    ) -> TimeframeDiagnostics:
        """Determine one canonical interval from frozen authoritative facts."""

        if not isinstance(contract, TimeframeContract):
            raise DataIntegrityError("timeframe contract is invalid")
        if not isinstance(instant, CanonicalInstant):
            _reject(TemporalDiagnosticCode.INVALID_CANONICAL_INSTANT, "observation is invalid")
        if contract.kind is TimeframeKind.DURATION:
            outcome = cls._interpret_duration(contract, instant, calendar_facts)
        else:
            outcome = cls._interpret_calendar(contract, instant, calendar_facts)
        return TimeframeDiagnostics((outcome,), ())

    @staticmethod
    def produce_mapping(
        source: TimeframeContract,
        target: TimeframeContract,
        *,
        mapping_identity: str,
        mapping_version: str,
        alignment_rule: str,
        membership_rule: str,
        closure_requirement: str,
        completeness_requirement: str,
        visibility_rule: str,
        revision_propagation_rule: str,
        conflict_rule: str,
        authority: TemporalAuthorityReference,
        policy_version: str,
    ) -> TimeframeDiagnostics:
        """Produce one immutable mapping fact without evaluating a dependency."""

        if not isinstance(source, TimeframeContract) or not isinstance(target, TimeframeContract):
            raise DataIntegrityError("mapping endpoints must be immutable timeframe contracts")
        admitted_authority = _require_authority(authority, "temporal_mapping.authority")
        if source.authority != admitted_authority or target.authority != admitted_authority:
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "mapping authority does not bind both timeframe contracts",
            )
        mapping = TemporalMappingContract(
            mapping_identity,
            mapping_version,
            source.timeframe_identity,
            source.timeframe_version,
            target.timeframe_identity,
            target.timeframe_version,
            alignment_rule,
            membership_rule,
            closure_requirement,
            completeness_requirement,
            visibility_rule,
            revision_propagation_rule,
            conflict_rule,
            admitted_authority,
            policy_version,
        )
        return TimeframeDiagnostics((), (mapping,))
