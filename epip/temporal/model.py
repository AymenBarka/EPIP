"""Immutable A05-E00 temporal primitives and authoritative calendar facts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum
from typing import ClassVar

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.governance import GovernanceEpoch


class _ImmutableRecord:
    """Small immutable value-record base outside the frozen dataclass inventory."""

    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable temporal model")

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


def _require_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DataIntegrityError(f"{field} must be an integer")
    return value


def _require_optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return require_text(value, field)


def _require_text_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    for item in value:
        require_text(item, field)
    if len(set(value)) != len(value):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return value


def _require_pairs(value: object, field: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    result: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DataIntegrityError(f"{field} must contain immutable pairs")
        left, right = item
        require_text(left, field)
        require_text(right, field)
        result.append((left, right))
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return tuple(sorted(result))


class TemporalDimension(str, Enum):
    """Independent temporal dimensions governed by ADR-EPIP017-05."""

    OBSERVATION = "OBSERVATION"
    VALIDITY = "VALIDITY"
    PUBLICATION = "PUBLICATION"
    AVAILABILITY = "AVAILABILITY"
    KNOWLEDGE = "KNOWLEDGE"
    REVISION = "REVISION"
    EXPIRATION = "EXPIRATION"
    HISTORICAL = "HISTORICAL"
    REPLAY = "REPLAY"


class BoundaryConvention(str, Enum):
    """Supported canonical interval boundary convention."""

    START_INCLUSIVE_END_EXCLUSIVE = "START_INCLUSIVE_END_EXCLUSIVE"


class CalendarFactKind(str, Enum):
    """Authoritative immutable calendar-fact classifications."""

    SESSION = "SESSION"
    HOLIDAY = "HOLIDAY"
    TIMEZONE_RULE = "TIMEZONE_RULE"
    SHORTENED_SESSION = "SHORTENED_SESSION"
    MARKET_CLOSURE = "MARKET_CLOSURE"
    EXCEPTIONAL_INTERVAL = "EXCEPTIONAL_INTERVAL"


class TemporalDiagnosticCode(str, Enum):
    """Stable A05 temporal diagnostic taxonomy required by ADR-EPIP017-05."""

    MISSING_OBSERVATION_TIME = "MISSING_OBSERVATION_TIME"
    MISSING_PUBLICATION_TIME = "MISSING_PUBLICATION_TIME"
    MISSING_AVAILABILITY_TIME = "MISSING_AVAILABILITY_TIME"
    MISSING_VALIDITY_TIME = "MISSING_VALIDITY_TIME"
    MISSING_REVISION_TIME = "MISSING_REVISION_TIME"
    MISSING_EXPIRATION_TIME = "MISSING_EXPIRATION_TIME"
    INVALID_CANONICAL_INSTANT = "INVALID_CANONICAL_INSTANT"
    INVALID_CANONICAL_INTERVAL = "INVALID_CANONICAL_INTERVAL"
    INVALID_PRECISION = "INVALID_PRECISION"
    INVALID_BOUNDARY_CONVENTION = "INVALID_BOUNDARY_CONVENTION"
    UNKNOWN_TIMEZONE = "UNKNOWN_TIMEZONE"
    INCOMPATIBLE_TIMEZONE = "INCOMPATIBLE_TIMEZONE"
    UNKNOWN_CALENDAR = "UNKNOWN_CALENDAR"
    INCOMPATIBLE_CALENDAR = "INCOMPATIBLE_CALENDAR"
    UNKNOWN_SESSION = "UNKNOWN_SESSION"
    INCOMPATIBLE_SESSION = "INCOMPATIBLE_SESSION"
    UNKNOWN_TIMEFRAME = "UNKNOWN_TIMEFRAME"
    INCOMPATIBLE_TIMEFRAME = "INCOMPATIBLE_TIMEFRAME"
    LATE_ARRIVAL = "LATE_ARRIVAL"
    DUPLICATE_TEMPORAL_ARTIFACT = "DUPLICATE_TEMPORAL_ARTIFACT"
    CONFLICTING_REVISION = "CONFLICTING_REVISION"
    MISSING_INTERVAL = "MISSING_INTERVAL"
    MISSING_TIMEFRAME = "MISSING_TIMEFRAME"
    UNEXPECTED_INTERVAL_OVERLAP = "UNEXPECTED_INTERVAL_OVERLAP"
    INCOMPLETE_WINDOW = "INCOMPLETE_WINDOW"
    PROVISIONAL_AS_FINAL = "PROVISIONAL_AS_FINAL"
    INSUFFICIENT_WATERMARK = "INSUFFICIENT_WATERMARK"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    EXPIRED_EVIDENCE = "EXPIRED_EVIDENCE"
    FUTURE_DEPENDENCY = "FUTURE_DEPENDENCY"
    FUTURE_LEAKAGE = "FUTURE_LEAKAGE"
    HISTORICAL_AMBIGUITY = "HISTORICAL_AMBIGUITY"
    HIDDEN_AGGREGATION = "HIDDEN_AGGREGATION"
    HIDDEN_INHERITANCE = "HIDDEN_INHERITANCE"
    HIDDEN_TIMEFRAME_CONVERSION = "HIDDEN_TIMEFRAME_CONVERSION"
    REVISION_LINEAGE_VIOLATION = "REVISION_LINEAGE_VIOLATION"
    DYNAMIC_AVAILABILITY_MUTATION = "DYNAMIC_AVAILABILITY_MUTATION"
    CROSS_TIMEFRAME_INCOMPATIBILITY = "CROSS_TIMEFRAME_INCOMPATIBILITY"
    CROSS_TIMEFRAME_CONFLICT = "CROSS_TIMEFRAME_CONFLICT"


class CanonicalInstant(_ImmutableRecord):
    """One unambiguous position on a governed time scale."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "value",
        "precision",
        "time_scale",
        "timezone_basis",
        "authority_identity",
    )
    _field_names = __slots__

    value: int
    precision: str
    time_scale: str
    timezone_basis: str
    authority_identity: str

    def __init__(
        self,
        value: int,
        precision: str,
        time_scale: str,
        timezone_basis: str,
        authority_identity: str,
    ) -> None:
        self._initialize(
            {
                "value": value,
                "precision": precision,
                "time_scale": time_scale,
                "timezone_basis": timezone_basis,
                "authority_identity": authority_identity,
            }
        )
        self.__post_init__()

    def __post_init__(self) -> None:
        _require_integer(self.value, "canonical_instant.value")
        for name in ("precision", "time_scale", "timezone_basis", "authority_identity"):
            require_text(getattr(self, name), f"canonical_instant.{name}")


class CanonicalInterval(_ImmutableRecord):
    """One non-empty start-inclusive and end-exclusive canonical interval."""

    __slots__ = ("start", "end", "boundary_convention")  # noqa: RUF023
    _field_names = __slots__

    start: CanonicalInstant
    end: CanonicalInstant
    boundary_convention: BoundaryConvention

    def __init__(
        self,
        start: CanonicalInstant,
        end: CanonicalInstant,
        boundary_convention: BoundaryConvention = BoundaryConvention.START_INCLUSIVE_END_EXCLUSIVE,
    ) -> None:
        self._initialize({"start": start, "end": end, "boundary_convention": boundary_convention})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.start, CanonicalInstant) or not isinstance(
            self.end, CanonicalInstant
        ):
            raise DataIntegrityError("canonical_interval endpoints must be CanonicalInstant")
        if not isinstance(self.boundary_convention, BoundaryConvention):
            raise DataIntegrityError("canonical_interval boundary convention is unsupported")
        if (
            self.start.precision != self.end.precision
            or self.start.time_scale != self.end.time_scale
            or self.start.timezone_basis != self.end.timezone_basis
        ):
            raise DataIntegrityError("canonical_interval endpoint bases must match")
        if self.start.value >= self.end.value:
            raise DataIntegrityError("canonical_interval must be non-empty and increasing")


class TemporalAuthorityReference(_ImmutableRecord):
    """Immutable reference to one governed temporal authority."""

    __slots__ = (
        "authority_identity",
        "authority_role",
        "authority_version",
        "governance_epoch",
    )
    _field_names = __slots__

    authority_identity: str
    authority_role: str
    authority_version: str
    governance_epoch: GovernanceEpoch

    def __init__(
        self,
        authority_identity: str,
        authority_role: str,
        authority_version: str,
        governance_epoch: GovernanceEpoch,
    ) -> None:
        self._initialize(
            {
                "authority_identity": authority_identity,
                "authority_role": authority_role,
                "authority_version": authority_version,
                "governance_epoch": governance_epoch,
            }
        )
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in ("authority_identity", "authority_role", "authority_version"):
            require_text(getattr(self, name), f"temporal_authority.{name}")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("temporal_authority.governance_epoch is invalid")


class CalendarFact(_ImmutableRecord):
    """One authority-issued immutable calendar fact without resolution behavior."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "fact_identity",
        "kind",
        "calendar_identity",
        "calendar_version",
        "interval",
        "authority",
        "policy_version",
        "session_identity",
        "timezone_identity",
        "utc_offset_seconds",
        "reason",
    )
    _field_names = __slots__

    fact_identity: str
    kind: CalendarFactKind
    calendar_identity: str
    calendar_version: str
    interval: CanonicalInterval
    authority: TemporalAuthorityReference
    policy_version: str
    session_identity: str | None
    timezone_identity: str | None
    utc_offset_seconds: int | None
    reason: str | None

    def __init__(
        self,
        fact_identity: str,
        kind: CalendarFactKind,
        calendar_identity: str,
        calendar_version: str,
        interval: CanonicalInterval,
        authority: TemporalAuthorityReference,
        policy_version: str,
        session_identity: str | None = None,
        timezone_identity: str | None = None,
        utc_offset_seconds: int | None = None,
        reason: str | None = None,
    ) -> None:
        self._initialize(
            {
                "fact_identity": fact_identity,
                "kind": kind,
                "calendar_identity": calendar_identity,
                "calendar_version": calendar_version,
                "interval": interval,
                "authority": authority,
                "policy_version": policy_version,
                "session_identity": session_identity,
                "timezone_identity": timezone_identity,
                "utc_offset_seconds": utc_offset_seconds,
                "reason": reason,
            }
        )
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "fact_identity",
            "calendar_identity",
            "calendar_version",
            "policy_version",
        ):
            require_text(getattr(self, name), f"calendar_fact.{name}")
        if not isinstance(self.kind, CalendarFactKind):
            raise DataIntegrityError("calendar_fact.kind is unsupported")
        if not isinstance(self.interval, CanonicalInterval):
            raise DataIntegrityError("calendar_fact.interval is invalid")
        if not isinstance(self.authority, TemporalAuthorityReference):
            raise DataIntegrityError("calendar_fact.authority is invalid")
        _require_optional_text(self.session_identity, "calendar_fact.session_identity")
        _require_optional_text(self.timezone_identity, "calendar_fact.timezone_identity")
        _require_optional_text(self.reason, "calendar_fact.reason")
        if self.utc_offset_seconds is not None:
            _require_integer(self.utc_offset_seconds, "calendar_fact.utc_offset_seconds")
        if self.kind is CalendarFactKind.TIMEZONE_RULE:
            if self.timezone_identity is None or self.utc_offset_seconds is None:
                raise MissingFieldError("timezone rules require timezone identity and UTC offset")
        elif self.timezone_identity is not None or self.utc_offset_seconds is not None:
            raise DataIntegrityError("timezone fields are reserved for timezone-rule facts")
        if self.kind in {CalendarFactKind.SESSION, CalendarFactKind.SHORTENED_SESSION}:
            if self.session_identity is None:
                raise MissingFieldError("session facts require session identity")
        elif self.session_identity is not None:
            raise DataIntegrityError("session identity is unsupported for this calendar fact")


class CalendarFactSet(_ImmutableRecord):
    """Canonical immutable collection of facts issued for one calendar contract."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "calendar_identity",
        "calendar_version",
        "authority",
        "facts",
    )
    _field_names = __slots__

    calendar_identity: str
    calendar_version: str
    authority: TemporalAuthorityReference
    facts: tuple[CalendarFact, ...]

    def __init__(
        self,
        calendar_identity: str,
        calendar_version: str,
        authority: TemporalAuthorityReference,
        facts: tuple[CalendarFact, ...],
    ) -> None:
        self._initialize(
            {
                "calendar_identity": calendar_identity,
                "calendar_version": calendar_version,
                "authority": authority,
                "facts": facts,
            }
        )
        self.__post_init__()

    def __post_init__(self) -> None:
        require_text(self.calendar_identity, "calendar_fact_set.calendar_identity")
        require_text(self.calendar_version, "calendar_fact_set.calendar_version")
        if not isinstance(self.authority, TemporalAuthorityReference):
            raise DataIntegrityError("calendar_fact_set.authority is invalid")
        if not isinstance(self.facts, tuple):
            raise DataIntegrityError("calendar_fact_set.facts must be an immutable tuple")
        if any(not isinstance(fact, CalendarFact) for fact in self.facts):
            raise DataIntegrityError("calendar_fact_set contains an unsupported fact")
        if any(
            fact.calendar_identity != self.calendar_identity
            or fact.calendar_version != self.calendar_version
            or fact.authority != self.authority
            for fact in self.facts
        ):
            raise DataIntegrityError("calendar facts must share calendar and authority context")
        identities = tuple(fact.fact_identity for fact in self.facts)
        if len(set(identities)) != len(identities):
            raise DataIntegrityError("calendar fact identities must be unique")
        object.__setattr__(
            self,
            "facts",
            tuple(sorted(self.facts, key=lambda fact: (fact.kind.value, fact.fact_identity))),
        )


class TemporalBoundary(_ImmutableRecord):
    """Immutable independent temporal facts admitted for one artifact or plan."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "boundary_identity",
        "observation",
        "validity",
        "validity_rule_reference",
        "publication",
        "availability",
        "knowledge",
        "revision",
        "expiration",
        "non_expiring_policy",
        "historical",
        "replay",
        "timeframe_identity",
        "timeframe_version",
        "calendar_identity",
        "calendar_version",
        "revision_lineage",
        "visibility_constraints",
        "policy_versions",
        "authorities",
    )
    _field_names = __slots__

    boundary_identity: str
    observation: CanonicalInstant | CanonicalInterval
    validity: CanonicalInterval | None
    validity_rule_reference: str | None
    publication: CanonicalInstant
    availability: CanonicalInstant
    knowledge: CanonicalInstant
    revision: CanonicalInstant | None
    expiration: CanonicalInstant | None
    non_expiring_policy: str | None
    historical: CanonicalInstant | None
    replay: CanonicalInstant | None
    timeframe_identity: str | None
    timeframe_version: str | None
    calendar_identity: str | None
    calendar_version: str | None
    revision_lineage: tuple[str, ...]
    visibility_constraints: tuple[str, ...]
    policy_versions: tuple[tuple[str, str], ...]
    authorities: tuple[TemporalAuthorityReference, ...]

    def __init__(
        self,
        boundary_identity: str,
        observation: CanonicalInstant | CanonicalInterval,
        validity: CanonicalInterval | None,
        validity_rule_reference: str | None,
        publication: CanonicalInstant,
        availability: CanonicalInstant,
        knowledge: CanonicalInstant,
        revision: CanonicalInstant | None,
        expiration: CanonicalInstant | None,
        non_expiring_policy: str | None,
        historical: CanonicalInstant | None,
        replay: CanonicalInstant | None,
        timeframe_identity: str | None,
        timeframe_version: str | None,
        calendar_identity: str | None,
        calendar_version: str | None,
        revision_lineage: tuple[str, ...],
        visibility_constraints: tuple[str, ...],
        policy_versions: tuple[tuple[str, str], ...],
        authorities: tuple[TemporalAuthorityReference, ...],
    ) -> None:
        values = {name: value for name, value in locals().items() if name != "self"}
        self._initialize(values)
        self.__post_init__()

    def __post_init__(self) -> None:
        require_text(self.boundary_identity, "temporal_boundary.boundary_identity")
        if not isinstance(self.observation, (CanonicalInstant, CanonicalInterval)):
            raise DataIntegrityError("temporal_boundary.observation is invalid")
        if self.validity is not None and not isinstance(self.validity, CanonicalInterval):
            raise DataIntegrityError("temporal_boundary.validity is invalid")
        _require_optional_text(
            self.validity_rule_reference,
            "temporal_boundary.validity_rule_reference",
        )
        if (self.validity is None) == (self.validity_rule_reference is None):
            raise DataIntegrityError("exactly one validity fact or rule is required")
        for name in ("publication", "availability", "knowledge"):
            if not isinstance(getattr(self, name), CanonicalInstant):
                raise DataIntegrityError(f"temporal_boundary.{name} is invalid")
        for name in ("revision", "expiration", "historical", "replay"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, CanonicalInstant):
                raise DataIntegrityError(f"temporal_boundary.{name} is invalid")
        _require_optional_text(
            self.non_expiring_policy,
            "temporal_boundary.non_expiring_policy",
        )
        if (self.expiration is None) == (self.non_expiring_policy is None):
            raise DataIntegrityError("exactly one expiration fact or policy is required")
        for identity_name, version_name in (
            ("timeframe_identity", "timeframe_version"),
            ("calendar_identity", "calendar_version"),
        ):
            identity = _require_optional_text(
                getattr(self, identity_name), f"temporal_boundary.{identity_name}"
            )
            version = _require_optional_text(
                getattr(self, version_name), f"temporal_boundary.{version_name}"
            )
            if (identity is None) != (version is None):
                raise DataIntegrityError(f"{identity_name} and {version_name} must be paired")
        _require_text_tuple(self.revision_lineage, "temporal_boundary.revision_lineage")
        _require_text_tuple(
            self.visibility_constraints,
            "temporal_boundary.visibility_constraints",
        )
        canonical_policies = _require_pairs(
            self.policy_versions,
            "temporal_boundary.policy_versions",
        )
        if not canonical_policies:
            raise MissingFieldError("temporal_boundary.policy_versions must not be empty")
        if not isinstance(self.authorities, tuple):
            raise DataIntegrityError("temporal_boundary.authorities must be an immutable tuple")
        if not self.authorities:
            raise MissingFieldError("temporal_boundary.authorities must not be empty")
        if any(not isinstance(item, TemporalAuthorityReference) for item in self.authorities):
            raise DataIntegrityError("temporal_boundary contains an unsupported authority")
        authority_keys = tuple(
            (item.authority_role, item.authority_identity, item.authority_version)
            for item in self.authorities
        )
        if len(set(authority_keys)) != len(authority_keys):
            raise DataIntegrityError("temporal_boundary authorities must be unique")
        object.__setattr__(self, "policy_versions", canonical_policies)
        object.__setattr__(
            self,
            "authorities",
            tuple(
                sorted(
                    self.authorities,
                    key=lambda item: (
                        item.authority_role,
                        item.authority_identity,
                        item.authority_version,
                    ),
                )
            ),
        )


class TemporalDiagnosticReason(_ImmutableRecord):
    """Immutable self-contained temporal diagnostic context."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "code",
        "affected_evidence",
        "source_boundary",
        "consumer_boundary",
        "timeframe_identity",
        "calendar_identity",
        "knowledge_boundary",
        "revision_lineage",
        "policy_version",
        "reason",
    )
    _field_names = __slots__

    code: TemporalDiagnosticCode
    affected_evidence: str
    source_boundary: str
    consumer_boundary: str
    timeframe_identity: str | None
    calendar_identity: str | None
    knowledge_boundary: CanonicalInstant
    revision_lineage: tuple[str, ...]
    policy_version: str
    reason: str

    def __init__(
        self,
        code: TemporalDiagnosticCode,
        affected_evidence: str,
        source_boundary: str,
        consumer_boundary: str,
        timeframe_identity: str | None,
        calendar_identity: str | None,
        knowledge_boundary: CanonicalInstant,
        revision_lineage: tuple[str, ...],
        policy_version: str,
        reason: str,
    ) -> None:
        values = {name: value for name, value in locals().items() if name != "self"}
        self._initialize(values)
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.code, TemporalDiagnosticCode):
            raise DataIntegrityError("temporal_diagnostic.code is invalid")
        for name in (
            "affected_evidence",
            "source_boundary",
            "consumer_boundary",
            "policy_version",
            "reason",
        ):
            require_text(getattr(self, name), f"temporal_diagnostic.{name}")
        _require_optional_text(
            self.timeframe_identity,
            "temporal_diagnostic.timeframe_identity",
        )
        _require_optional_text(
            self.calendar_identity,
            "temporal_diagnostic.calendar_identity",
        )
        if not isinstance(self.knowledge_boundary, CanonicalInstant):
            raise DataIntegrityError("temporal_diagnostic.knowledge_boundary is invalid")
        _require_text_tuple(
            self.revision_lineage,
            "temporal_diagnostic.revision_lineage",
        )
