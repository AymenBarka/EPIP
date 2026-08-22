"""Deterministic A05-E03 observation and validity validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar, NoReturn

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.governance import GovernanceEpoch
from epip.temporal.availability import AvailabilityDecision
from epip.temporal.model import (
    CanonicalInstant,
    CanonicalInterval,
    TemporalAuthorityReference,
    TemporalBoundary,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.timeframe import CanonicalTimeframe


class _ImmutableRecord:
    """Immutable value-record support local to the E03 ownership boundary."""

    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable observation model")

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


def _instant_key(instant: CanonicalInstant) -> tuple[int, str, str, str, str]:
    return (
        instant.value,
        instant.precision,
        instant.time_scale,
        instant.timezone_basis,
        instant.authority_identity,
    )


def _observation_key(
    observation: CanonicalInstant | CanonicalInterval,
) -> tuple[object, ...]:
    if isinstance(observation, CanonicalInstant):
        return ("POINT", _instant_key(observation))
    return (
        "INTERVAL",
        _instant_key(observation.start),
        _instant_key(observation.end),
        observation.boundary_convention.value,
    )


def _observation_end(
    observation: CanonicalInstant | CanonicalInterval,
) -> CanonicalInstant:
    if isinstance(observation, CanonicalInterval):
        return observation.end
    return observation


def _same_basis(left: CanonicalInstant, right: CanonicalInstant) -> bool:
    return (
        left.precision,
        left.time_scale,
        left.timezone_basis,
    ) == (
        right.precision,
        right.time_scale,
        right.timezone_basis,
    )


def _authority_key(
    authority: TemporalAuthorityReference,
) -> tuple[str, str, str, GovernanceEpoch]:
    return (
        authority.authority_role,
        authority.authority_identity,
        authority.authority_version,
        authority.governance_epoch,
    )


class ObservationValidation(_ImmutableRecord):
    """Immutable self-contained E03 observation-validation outcome."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "artifact_identity",
        "boundary_identity",
        "consumer_temporal_boundary",
        "observation",
        "source_observation",
        "is_interval",
        "validity",
        "validity_rule_reference",
        "publication_time",
        "availability_time",
        "knowledge_boundary",
        "visible",
        "provisionally_temporally_eligible",
        "late",
        "closure_state",
        "provisional",
        "consumer_allows_provisional",
        "timeframe_identity",
        "timeframe_version",
        "calendar_identity",
        "calendar_version",
        "governance_epoch",
        "revision_lineage",
        "authority_facts",
        "policy_version",
    )
    _field_names = __slots__

    artifact_identity: str
    boundary_identity: str
    consumer_temporal_boundary: str
    observation: CanonicalInstant | CanonicalInterval
    source_observation: CanonicalInstant | CanonicalInterval
    is_interval: bool
    validity: CanonicalInterval | None
    validity_rule_reference: str | None
    publication_time: CanonicalInstant
    availability_time: CanonicalInstant
    knowledge_boundary: CanonicalInstant
    visible: bool
    provisionally_temporally_eligible: bool
    late: bool
    closure_state: str
    provisional: bool
    consumer_allows_provisional: bool
    timeframe_identity: str | None
    timeframe_version: str | None
    calendar_identity: str | None
    calendar_version: str | None
    governance_epoch: GovernanceEpoch
    revision_lineage: tuple[str, ...]
    authority_facts: tuple[tuple[str, str, str, GovernanceEpoch], ...]
    policy_version: str

    def __init__(
        self,
        artifact_identity: str,
        boundary_identity: str,
        consumer_temporal_boundary: str,
        observation: CanonicalInstant | CanonicalInterval,
        source_observation: CanonicalInstant | CanonicalInterval,
        is_interval: bool,
        validity: CanonicalInterval | None,
        validity_rule_reference: str | None,
        publication_time: CanonicalInstant,
        availability_time: CanonicalInstant,
        knowledge_boundary: CanonicalInstant,
        visible: bool,
        provisionally_temporally_eligible: bool,
        late: bool,
        closure_state: str,
        provisional: bool,
        consumer_allows_provisional: bool,
        timeframe_identity: str | None,
        timeframe_version: str | None,
        calendar_identity: str | None,
        calendar_version: str | None,
        governance_epoch: GovernanceEpoch,
        revision_lineage: tuple[str, ...],
        authority_facts: tuple[tuple[str, str, str, GovernanceEpoch], ...],
        policy_version: str,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "artifact_identity",
            "boundary_identity",
            "consumer_temporal_boundary",
            "closure_state",
            "policy_version",
        ):
            require_text(getattr(self, name), f"observation_validation.{name}")
        if not isinstance(self.observation, (CanonicalInstant, CanonicalInterval)):
            raise DataIntegrityError("observation_validation.observation is invalid")
        if not isinstance(self.source_observation, (CanonicalInstant, CanonicalInterval)):
            raise DataIntegrityError("observation_validation.source_observation is invalid")
        if not isinstance(self.is_interval, bool):
            raise DataIntegrityError("observation_validation.is_interval must be a boolean")
        if self.is_interval != isinstance(self.observation, CanonicalInterval):
            raise DataIntegrityError("observation_validation observation kind is inconsistent")
        if self.observation != self.source_observation:
            raise DataIntegrityError("observation_validation source observation is inconsistent")
        if self.validity is not None and not isinstance(self.validity, CanonicalInterval):
            raise DataIntegrityError("observation_validation.validity is invalid")
        if self.validity_rule_reference is not None:
            require_text(
                self.validity_rule_reference,
                "observation_validation.validity_rule_reference",
            )
        if (self.validity is None) == (self.validity_rule_reference is None):
            raise DataIntegrityError("observation validation requires exactly one validity fact")
        for name in ("publication_time", "availability_time", "knowledge_boundary"):
            if not isinstance(getattr(self, name), CanonicalInstant):
                raise DataIntegrityError(f"observation_validation.{name} is invalid")
        for name in (
            "visible",
            "provisionally_temporally_eligible",
            "late",
            "provisional",
            "consumer_allows_provisional",
        ):
            if not isinstance(getattr(self, name), bool):
                raise DataIntegrityError(f"observation_validation.{name} must be a boolean")
        for identity_name, version_name in (
            ("timeframe_identity", "timeframe_version"),
            ("calendar_identity", "calendar_version"),
        ):
            identity = getattr(self, identity_name)
            version = getattr(self, version_name)
            if identity is not None:
                require_text(identity, f"observation_validation.{identity_name}")
            if version is not None:
                require_text(version, f"observation_validation.{version_name}")
            if (identity is None) != (version is None):
                raise DataIntegrityError(f"{identity_name} and {version_name} must be paired")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("observation_validation.governance_epoch is invalid")
        if not isinstance(self.revision_lineage, tuple):
            raise DataIntegrityError("observation_validation.revision_lineage must be immutable")
        for identity in self.revision_lineage:
            require_text(identity, "observation_validation.revision_lineage")
        if not isinstance(self.authority_facts, tuple) or not self.authority_facts:
            raise MissingFieldError("observation validation requires immutable authority facts")
        for fact in self.authority_facts:
            if (
                not isinstance(fact, tuple)
                or len(fact) != 4
                or not isinstance(fact[3], GovernanceEpoch)
            ):
                raise DataIntegrityError("observation_validation.authority_facts is invalid")
            for value in fact[:3]:
                require_text(value, "observation_validation.authority_facts")
        object.__setattr__(self, "authority_facts", tuple(sorted(self.authority_facts)))
        object.__setattr__(self, "revision_lineage", tuple(sorted(self.revision_lineage)))


def _validation_key(item: ObservationValidation) -> tuple[object, ...]:
    validity_key: tuple[object, ...] = ()
    if item.validity is not None:
        validity_key = (
            _instant_key(item.validity.start),
            _instant_key(item.validity.end),
            item.validity.boundary_convention.value,
        )
    return (
        item.artifact_identity,
        item.boundary_identity,
        item.consumer_temporal_boundary,
        _observation_key(item.observation),
        _observation_key(item.source_observation),
        item.is_interval,
        validity_key,
        item.validity_rule_reference or "",
        _instant_key(item.publication_time),
        _instant_key(item.availability_time),
        _instant_key(item.knowledge_boundary),
        item.visible,
        item.provisionally_temporally_eligible,
        item.late,
        item.closure_state,
        item.provisional,
        item.consumer_allows_provisional,
        item.timeframe_identity or "",
        item.timeframe_version or "",
        item.calendar_identity or "",
        item.calendar_version or "",
        item.governance_epoch.sequence,
        item.revision_lineage,
        tuple(
            (role, identity, version, epoch.sequence)
            for role, identity, version, epoch in item.authority_facts
        ),
        item.policy_version,
    )


class ObservationDiagnostics(_ImmutableRecord):
    """Immutable deterministic E03 outcomes and attributed temporal diagnostics."""

    __slots__ = ("validations", "reasons")  # noqa: RUF023 - semantic field order
    _field_names = __slots__

    validations: tuple[ObservationValidation, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        validations: tuple[ObservationValidation, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.validations, tuple) or any(
            not isinstance(item, ObservationValidation) for item in self.validations
        ):
            raise DataIntegrityError("observation diagnostics require immutable validations")
        if not isinstance(self.reasons, tuple) or any(
            not isinstance(item, TemporalDiagnosticReason) for item in self.reasons
        ):
            raise DataIntegrityError("observation diagnostics require immutable reasons")
        validations = tuple(sorted(self.validations, key=_validation_key))
        if len(set(validations)) != len(validations):
            raise DataIntegrityError("observation diagnostics contain duplicate validations")
        reasons = tuple(
            sorted(
                self.reasons,
                key=lambda item: (
                    item.affected_evidence,
                    item.source_boundary,
                    item.consumer_boundary,
                    item.code.value,
                    item.reason,
                    item.timeframe_identity or "",
                    item.calendar_identity or "",
                    _instant_key(item.knowledge_boundary),
                    item.revision_lineage,
                    item.policy_version,
                ),
            )
        )
        diagnostic_keys: set[tuple[object, ...]] = set()
        for reason in reasons:
            matches = tuple(
                validation
                for validation in validations
                if reason.affected_evidence == validation.artifact_identity
                and reason.source_boundary == validation.boundary_identity
                and reason.consumer_boundary == validation.consumer_temporal_boundary
                and reason.timeframe_identity == validation.timeframe_identity
                and reason.calendar_identity == validation.calendar_identity
                and reason.knowledge_boundary == validation.knowledge_boundary
                and reason.revision_lineage == validation.revision_lineage
                and reason.policy_version == validation.policy_version
            )
            if len(matches) != 1:
                raise DataIntegrityError(
                    "observation diagnostic must bind to exactly one validation"
                )
            key = (
                reason.affected_evidence,
                reason.source_boundary,
                reason.consumer_boundary,
                reason.timeframe_identity,
                reason.calendar_identity,
                reason.knowledge_boundary,
                reason.revision_lineage,
                reason.policy_version,
                reason.code,
            )
            if key in diagnostic_keys:
                raise DataIntegrityError(
                    "observation diagnostics contain duplicate inconsistent bindings"
                )
            diagnostic_keys.add(key)
        object.__setattr__(self, "validations", validations)
        object.__setattr__(self, "reasons", reasons)


class ObservationValidator:
    """Validate E03 observation and validity facts without successor behavior."""

    __slots__ = ()

    @staticmethod
    def _validate_binding(
        boundary: TemporalBoundary,
        availability: AvailabilityDecision,
    ) -> None:
        if (
            availability.boundary_identity != boundary.boundary_identity
            or availability.observation_time != boundary.observation
            or availability.validity != boundary.validity
            or availability.validity_rule_reference != boundary.validity_rule_reference
            or availability.publication_time != boundary.publication
            or availability.availability_time != boundary.availability
            or availability.knowledge_boundary != boundary.knowledge
            or availability.timeframe_identity != boundary.timeframe_identity
            or availability.timeframe_version != boundary.timeframe_version
            or availability.calendar_identity != boundary.calendar_identity
            or availability.calendar_version != boundary.calendar_version
            or tuple(sorted(availability.revision_lineage))
            != tuple(sorted(boundary.revision_lineage))
        ):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "E02 availability outcome does not bind to the temporal boundary",
            )
        if not availability.visible:
            _reject(
                TemporalDiagnosticCode.FUTURE_LEAKAGE,
                "an observation outside the frozen knowledge boundary is unavailable",
            )

    @staticmethod
    def _validate_authority(
        boundary: TemporalBoundary,
        availability: AvailabilityDecision,
    ) -> tuple[tuple[str, str, str, GovernanceEpoch], ...]:
        source = tuple(
            authority
            for authority in boundary.authorities
            if authority.authority_role == "source_authority"
        )
        if len(source) != 1:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "exactly one source authority is mandatory",
            )
        if source[0].governance_epoch != availability.governance_epoch:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "source authority governance epoch does not match E02",
            )
        return tuple(sorted(_authority_key(authority) for authority in boundary.authorities))

    @staticmethod
    def _validate_timeframe(
        boundary: TemporalBoundary,
        timeframe: CanonicalTimeframe | None,
    ) -> None:
        if boundary.timeframe_identity is None:
            if timeframe is not None:
                _reject(
                    TemporalDiagnosticCode.INCOMPATIBLE_TIMEFRAME,
                    "unscoped observation must not receive a timeframe",
                )
            return
        if timeframe is None:
            _reject(
                TemporalDiagnosticCode.MISSING_TIMEFRAME,
                "timeframe-scoped observation requires an E01 outcome",
            )
        assert boundary.timeframe_version is not None
        if (
            timeframe.timeframe_identity != boundary.timeframe_identity
            or timeframe.timeframe_version != boundary.timeframe_version
            or timeframe.calendar_identity != boundary.calendar_identity
            or timeframe.calendar_version != boundary.calendar_version
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPATIBLE_TIMEFRAME,
                "E01 timeframe outcome does not match the observation",
            )

    @staticmethod
    def _validate_source_observation(
        declared: CanonicalInstant | CanonicalInterval,
        source: CanonicalInstant | CanonicalInterval,
    ) -> None:
        if (
            isinstance(source, CanonicalInterval)
            and isinstance(declared, CanonicalInstant)
            and declared == source.end
        ):
            _reject(
                TemporalDiagnosticCode.INVALID_BOUNDARY_CONVENTION,
                "interval-end substitution for an interval observation is forbidden",
            )
        if declared != source:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "source observation timestamp mutation is forbidden",
            )

    @staticmethod
    def _validate_closure(
        observation: CanonicalInstant | CanonicalInterval,
        closure_state: str,
        provisional: bool,
        consumer_allows_provisional: bool,
    ) -> None:
        state = require_text(closure_state, "observation.closure_state")
        if state not in {"POINT", "OPEN", "CLOSED", "FINAL"}:
            raise DataIntegrityError("observation closure state is unsupported")
        if not isinstance(provisional, bool) or not isinstance(consumer_allows_provisional, bool):
            raise DataIntegrityError("observation provisional declarations must be boolean")
        if isinstance(observation, CanonicalInstant):
            if state != "POINT":
                _reject(
                    TemporalDiagnosticCode.INVALID_BOUNDARY_CONVENTION,
                    "point observation requires POINT closure state",
                )
        elif state == "POINT":
            _reject(
                TemporalDiagnosticCode.INVALID_BOUNDARY_CONVENTION,
                "interval observation requires an interval closure state",
            )
        if provisional and (state == "FINAL" or not consumer_allows_provisional):
            _reject(
                TemporalDiagnosticCode.PROVISIONAL_AS_FINAL,
                "provisional observation cannot be represented or consumed as final",
            )
        if not provisional and state == "OPEN":
            _reject(
                TemporalDiagnosticCode.PROVISIONAL_AS_FINAL,
                "open interval must be explicitly provisional",
            )

    @staticmethod
    def _validate_bases(
        boundary: TemporalBoundary,
        source_observation: CanonicalInstant | CanonicalInterval,
        timeframe: CanonicalTimeframe | None,
    ) -> None:
        instants = [
            boundary.publication,
            boundary.availability,
            boundary.knowledge,
            _observation_end(boundary.observation),
            _observation_end(source_observation),
        ]
        if isinstance(boundary.observation, CanonicalInterval):
            instants.append(boundary.observation.start)
        if isinstance(source_observation, CanonicalInterval):
            instants.append(source_observation.start)
        if boundary.validity is not None:
            instants.extend((boundary.validity.start, boundary.validity.end))
        if timeframe is not None:
            instants.extend((timeframe.interval.start, timeframe.interval.end))
        if any(not _same_basis(instants[0], instant) for instant in instants[1:]):
            _reject(
                TemporalDiagnosticCode.INVALID_PRECISION,
                "observation validation requires one canonical temporal basis",
            )

    @classmethod
    def validate(
        cls,
        boundary: TemporalBoundary,
        availability: AvailabilityDecision,
        source_observation: CanonicalInstant | CanonicalInterval,
        closure_state: str,
        provisional: bool,
        consumer_allows_provisional: bool,
        policy_version: str,
        timeframe: CanonicalTimeframe | None = None,
    ) -> ObservationDiagnostics:
        """Validate one admitted observation without completeness or dependency behavior."""

        if not isinstance(boundary, TemporalBoundary):
            raise DataIntegrityError("observation boundary must be a TemporalBoundary")
        if not isinstance(availability, AvailabilityDecision):
            raise DataIntegrityError("observation availability must be an E02 decision")
        if not isinstance(source_observation, (CanonicalInstant, CanonicalInterval)):
            raise DataIntegrityError("source observation must be canonical")
        if timeframe is not None and not isinstance(timeframe, CanonicalTimeframe):
            raise DataIntegrityError("observation timeframe must be a CanonicalTimeframe")
        policy = require_text(policy_version, "observation.policy_version")
        cls._validate_binding(boundary, availability)
        authority_facts = cls._validate_authority(boundary, availability)
        cls._validate_timeframe(boundary, timeframe)
        cls._validate_source_observation(boundary.observation, source_observation)
        cls._validate_closure(
            boundary.observation,
            closure_state,
            provisional,
            consumer_allows_provisional,
        )
        cls._validate_bases(boundary, source_observation, timeframe)

        validation = ObservationValidation(
            availability.artifact_identity,
            boundary.boundary_identity,
            availability.use_identity,
            boundary.observation,
            source_observation,
            isinstance(boundary.observation, CanonicalInterval),
            boundary.validity,
            boundary.validity_rule_reference,
            boundary.publication,
            boundary.availability,
            boundary.knowledge,
            availability.visible,
            availability.provisionally_temporally_eligible,
            availability.late,
            closure_state,
            provisional,
            consumer_allows_provisional,
            boundary.timeframe_identity,
            boundary.timeframe_version,
            boundary.calendar_identity,
            boundary.calendar_version,
            availability.governance_epoch,
            boundary.revision_lineage,
            authority_facts,
            policy,
        )
        reasons: tuple[TemporalDiagnosticReason, ...] = ()
        if availability.late:
            reasons = (
                TemporalDiagnosticReason(
                    TemporalDiagnosticCode.LATE_ARRIVAL,
                    availability.artifact_identity,
                    boundary.boundary_identity,
                    availability.use_identity,
                    boundary.timeframe_identity,
                    boundary.calendar_identity,
                    boundary.knowledge,
                    tuple(sorted(boundary.revision_lineage)),
                    policy,
                    "late arrival preserves the original observation time",
                ),
            )
        return ObservationDiagnostics((validation,), reasons)
