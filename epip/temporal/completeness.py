"""Deterministic A05-E04 interval closure and completeness validation."""

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
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.observation import ObservationValidation
from epip.temporal.timeframe import CanonicalTimeframe


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable completeness model")

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


def _interval_key(interval: CanonicalInterval) -> tuple[object, ...]:
    return (
        _instant_key(interval.start),
        _instant_key(interval.end),
        interval.boundary_convention.value,
    )


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


def _require_memberships(
    value: object,
) -> tuple[tuple[str, CanonicalInterval], ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("interval memberships must be an immutable tuple")
    result: list[tuple[str, CanonicalInterval]] = []
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[1], CanonicalInterval)
        ):
            raise DataIntegrityError("interval memberships contain an unsupported fact")
        identity, interval = item
        require_text(identity, "interval_membership.artifact_identity")
        result.append((identity, interval))
    identities = tuple(identity for identity, _ in result)
    if len(set(identities)) != len(identities):
        _reject(
            TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
            "interval membership artifact identities must be unique",
        )
    return tuple(sorted(result, key=lambda item: (item[0], _interval_key(item[1]))))


def _require_closures(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("closure facts must be an immutable tuple")
    result: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DataIntegrityError("closure facts contain an unsupported fact")
        identity, state = item
        require_text(identity, "closure_fact.artifact_identity")
        require_text(state, "closure_fact.state")
        if state not in {"POINT", "OPEN", "CLOSED", "FINAL"}:
            raise DataIntegrityError("closure fact state is unsupported")
        result.append((identity, state))
    identities = tuple(identity for identity, _ in result)
    if len(set(identities)) != len(identities):
        _reject(
            TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
            "closure fact artifact identities must be unique",
        )
    return tuple(sorted(result))


def _require_intervals(value: object, field: str) -> tuple[CanonicalInterval, ...]:
    if not isinstance(value, tuple) or any(
        not isinstance(item, CanonicalInterval) for item in value
    ):
        raise DataIntegrityError(f"{field} must be an immutable interval tuple")
    result = tuple(sorted(value, key=_interval_key))
    if len(set(result)) != len(result):
        _reject(
            TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
            f"{field} must not contain duplicate intervals",
        )
    return result


class CompletenessOutcome(_ImmutableRecord):
    """Immutable self-contained E04 closure and completeness outcome."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "outcome_identity",
        "artifact_identities",
        "source_temporal_boundaries",
        "consumer_temporal_boundaries",
        "knowledge_boundaries",
        "revision_lineages",
        "interval_memberships",
        "required_intervals",
        "closure_facts",
        "watermark_identity",
        "watermark",
        "watermark_authority",
        "watermark_policy_version",
        "required_cardinality",
        "observed_cardinality",
        "declared_complete",
        "complete",
        "provisional",
        "timeframe_identity",
        "timeframe_version",
        "calendar_identity",
        "calendar_version",
        "calendar_fact_identities",
        "governance_epoch",
        "policy_identity",
        "policy_version",
    )
    _field_names = __slots__

    outcome_identity: str
    artifact_identities: tuple[str, ...]
    source_temporal_boundaries: tuple[str, ...]
    consumer_temporal_boundaries: tuple[str, ...]
    knowledge_boundaries: tuple[CanonicalInstant, ...]
    revision_lineages: tuple[tuple[str, ...], ...]
    interval_memberships: tuple[tuple[str, CanonicalInterval], ...]
    required_intervals: tuple[CanonicalInterval, ...]
    closure_facts: tuple[tuple[str, str], ...]
    watermark_identity: str
    watermark: CanonicalInstant
    watermark_authority: TemporalAuthorityReference
    watermark_policy_version: str
    required_cardinality: int | None
    observed_cardinality: int
    declared_complete: bool
    complete: bool
    provisional: bool
    timeframe_identity: str
    timeframe_version: str
    calendar_identity: str
    calendar_version: str
    calendar_fact_identities: tuple[str, ...]
    governance_epoch: GovernanceEpoch
    policy_identity: str
    policy_version: str

    def __init__(
        self,
        outcome_identity: str,
        artifact_identities: tuple[str, ...],
        source_temporal_boundaries: tuple[str, ...],
        consumer_temporal_boundaries: tuple[str, ...],
        knowledge_boundaries: tuple[CanonicalInstant, ...],
        revision_lineages: tuple[tuple[str, ...], ...],
        interval_memberships: tuple[tuple[str, CanonicalInterval], ...],
        required_intervals: tuple[CanonicalInterval, ...],
        closure_facts: tuple[tuple[str, str], ...],
        watermark_identity: str,
        watermark: CanonicalInstant,
        watermark_authority: TemporalAuthorityReference,
        watermark_policy_version: str,
        required_cardinality: int | None,
        observed_cardinality: int,
        declared_complete: bool,
        complete: bool,
        provisional: bool,
        timeframe_identity: str,
        timeframe_version: str,
        calendar_identity: str,
        calendar_version: str,
        calendar_fact_identities: tuple[str, ...],
        governance_epoch: GovernanceEpoch,
        policy_identity: str,
        policy_version: str,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "outcome_identity",
            "watermark_identity",
            "watermark_policy_version",
            "timeframe_identity",
            "timeframe_version",
            "calendar_identity",
            "calendar_version",
            "policy_identity",
            "policy_version",
        ):
            require_text(getattr(self, name), f"completeness_outcome.{name}")
        text_collections = (
            (self.artifact_identities, "artifact_identities"),
            (self.source_temporal_boundaries, "source_temporal_boundaries"),
            (self.consumer_temporal_boundaries, "consumer_temporal_boundaries"),
            (self.calendar_fact_identities, "calendar_fact_identities"),
        )
        for values, field in text_collections:
            if not isinstance(values, tuple):
                raise DataIntegrityError(f"completeness_outcome.{field} must be immutable")
            for value in values:
                require_text(value, f"completeness_outcome.{field}")
            if field in {"artifact_identities", "calendar_fact_identities"} and len(
                set(values)
            ) != len(values):
                raise DataIntegrityError(f"completeness_outcome.{field} must be unique")
        if not self.artifact_identities:
            raise MissingFieldError("completeness outcome requires artifact identities")
        if not isinstance(self.knowledge_boundaries, tuple) or any(
            not isinstance(item, CanonicalInstant) for item in self.knowledge_boundaries
        ):
            raise DataIntegrityError("completeness outcome knowledge boundaries are invalid")
        if not isinstance(self.revision_lineages, tuple) or any(
            not isinstance(lineage, tuple) for lineage in self.revision_lineages
        ):
            raise DataIntegrityError("completeness outcome revision lineages are invalid")
        for lineage in self.revision_lineages:
            for identity in lineage:
                require_text(identity, "completeness_outcome.revision_lineages")
        memberships = _require_memberships(self.interval_memberships)
        required = _require_intervals(self.required_intervals, "required_intervals")
        closures = _require_closures(self.closure_facts)
        if not isinstance(self.watermark, CanonicalInstant):
            raise DataIntegrityError("completeness outcome watermark is invalid")
        if not isinstance(self.watermark_authority, TemporalAuthorityReference):
            raise DataIntegrityError("completeness outcome watermark authority is invalid")
        if self.required_cardinality is not None and (
            isinstance(self.required_cardinality, bool)
            or not isinstance(self.required_cardinality, int)
            or self.required_cardinality < 0
        ):
            raise DataIntegrityError("required cardinality must be a non-negative integer")
        if (
            isinstance(self.observed_cardinality, bool)
            or not isinstance(self.observed_cardinality, int)
            or self.observed_cardinality < 0
        ):
            raise DataIntegrityError("observed cardinality must be a non-negative integer")
        for name in ("declared_complete", "complete", "provisional"):
            if not isinstance(getattr(self, name), bool):
                raise DataIntegrityError(f"completeness_outcome.{name} must be a boolean")
        if self.complete != (self.declared_complete and not self.provisional):
            raise DataIntegrityError("completeness outcome state is inconsistent")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("completeness outcome governance epoch is invalid")
        if len(self.artifact_identities) != self.observed_cardinality:
            raise DataIntegrityError("observed cardinality does not match artifact identities")
        context_lengths = {
            len(self.artifact_identities),
            len(self.source_temporal_boundaries),
            len(self.consumer_temporal_boundaries),
            len(self.knowledge_boundaries),
            len(self.revision_lineages),
            len(memberships),
            len(closures),
        }
        if len(context_lengths) != 1:
            raise DataIntegrityError("completeness outcome artifact context is incomplete")
        contexts = tuple(
            sorted(
                zip(
                    self.artifact_identities,
                    self.source_temporal_boundaries,
                    self.consumer_temporal_boundaries,
                    self.knowledge_boundaries,
                    self.revision_lineages,
                    strict=True,
                ),
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    _instant_key(item[3]),
                    item[4],
                ),
            )
        )
        object.__setattr__(self, "artifact_identities", tuple(item[0] for item in contexts))
        object.__setattr__(self, "source_temporal_boundaries", tuple(item[1] for item in contexts))
        object.__setattr__(
            self, "consumer_temporal_boundaries", tuple(item[2] for item in contexts)
        )
        object.__setattr__(self, "knowledge_boundaries", tuple(item[3] for item in contexts))
        object.__setattr__(self, "revision_lineages", tuple(item[4] for item in contexts))
        object.__setattr__(self, "interval_memberships", memberships)
        object.__setattr__(self, "required_intervals", required)
        object.__setattr__(self, "closure_facts", closures)
        object.__setattr__(
            self, "calendar_fact_identities", tuple(sorted(self.calendar_fact_identities))
        )


def _outcome_key(item: CompletenessOutcome) -> tuple[object, ...]:
    return (
        item.outcome_identity,
        item.artifact_identities,
        item.source_temporal_boundaries,
        item.consumer_temporal_boundaries,
        tuple(_instant_key(value) for value in item.knowledge_boundaries),
        item.revision_lineages,
        tuple(
            (identity, _interval_key(interval)) for identity, interval in item.interval_memberships
        ),
        tuple(_interval_key(interval) for interval in item.required_intervals),
        item.closure_facts,
        item.watermark_identity,
        _instant_key(item.watermark),
        (
            item.watermark_authority.authority_role,
            item.watermark_authority.authority_identity,
            item.watermark_authority.authority_version,
            item.watermark_authority.governance_epoch.sequence,
        ),
        item.watermark_policy_version,
        item.required_cardinality if item.required_cardinality is not None else -1,
        item.observed_cardinality,
        item.declared_complete,
        item.complete,
        item.provisional,
        item.timeframe_identity,
        item.timeframe_version,
        item.calendar_identity,
        item.calendar_version,
        item.calendar_fact_identities,
        item.governance_epoch.sequence,
        item.policy_identity,
        item.policy_version,
    )


class CompletenessDiagnostics(_ImmutableRecord):
    """Immutable deterministic E04 outcomes and attributed diagnostics."""

    __slots__ = ("outcomes", "reasons")
    _field_names = __slots__

    outcomes: tuple[CompletenessOutcome, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        outcomes: tuple[CompletenessOutcome, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.outcomes, tuple) or any(
            not isinstance(item, CompletenessOutcome) for item in self.outcomes
        ):
            raise DataIntegrityError("completeness diagnostics require immutable outcomes")
        if not isinstance(self.reasons, tuple) or any(
            not isinstance(item, TemporalDiagnosticReason) for item in self.reasons
        ):
            raise DataIntegrityError("completeness diagnostics require immutable reasons")
        outcomes = tuple(sorted(self.outcomes, key=_outcome_key))
        if len(set(outcomes)) != len(outcomes):
            raise DataIntegrityError("completeness diagnostics contain duplicate outcomes")
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
        contexts = {
            (
                artifact,
                source,
                consumer,
                knowledge,
                lineage,
                outcome.timeframe_identity,
                outcome.calendar_identity,
                outcome.policy_version,
            )
            for outcome in outcomes
            for artifact, source, consumer, knowledge, lineage in zip(
                outcome.artifact_identities,
                outcome.source_temporal_boundaries,
                outcome.consumer_temporal_boundaries,
                outcome.knowledge_boundaries,
                outcome.revision_lineages,
                strict=True,
            )
        }
        for reason in reasons:
            binding = (
                reason.affected_evidence,
                reason.source_boundary,
                reason.consumer_boundary,
                reason.knowledge_boundary,
                reason.revision_lineage,
                reason.timeframe_identity,
                reason.calendar_identity,
                reason.policy_version,
            )
            if binding not in contexts:
                raise DataIntegrityError("completeness diagnostic reason is not attributable")
        if len(set(reasons)) != len(reasons):
            raise DataIntegrityError("completeness diagnostics contain duplicate reasons")
        object.__setattr__(self, "outcomes", outcomes)
        object.__setattr__(self, "reasons", reasons)


class CompletenessValidator:
    """Validate E04 completeness facts without aggregation or successor behavior."""

    __slots__ = ()

    @staticmethod
    def _bind_predecessors(
        availability: tuple[AvailabilityDecision, ...],
        observations: tuple[ObservationValidation, ...],
    ) -> tuple[tuple[AvailabilityDecision, ObservationValidation], ...]:
        if not isinstance(availability, tuple) or any(
            not isinstance(item, AvailabilityDecision) for item in availability
        ):
            raise DataIntegrityError("availability inputs must be immutable E02 decisions")
        if not isinstance(observations, tuple) or any(
            not isinstance(item, ObservationValidation) for item in observations
        ):
            raise DataIntegrityError("observation inputs must be immutable E03 validations")
        if not observations:
            raise MissingFieldError("completeness validation requires observations")
        pairs: list[tuple[AvailabilityDecision, ObservationValidation]] = []
        for observation in observations:
            matches = tuple(
                decision
                for decision in availability
                if decision.artifact_identity == observation.artifact_identity
                and decision.boundary_identity == observation.boundary_identity
                and decision.use_identity == observation.consumer_temporal_boundary
                and decision.knowledge_boundary == observation.knowledge_boundary
                and decision.revision_lineage == observation.revision_lineage
            )
            if len(matches) != 1:
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "each observation must bind to exactly one E02 decision",
                )
            pairs.append((matches[0], observation))
        pairs.sort(key=lambda item: item[1].artifact_identity)
        identities = tuple(item[1].artifact_identity for item in pairs)
        if len(set(identities)) != len(identities):
            _reject(
                TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
                "duplicate observations are forbidden",
            )
        if len(availability) != len(pairs):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "unbound E02 availability decisions are forbidden",
            )
        return tuple(pairs)

    @staticmethod
    def _validate_timeframe(
        pairs: tuple[tuple[AvailabilityDecision, ObservationValidation], ...],
        timeframe: CanonicalTimeframe,
    ) -> None:
        if not isinstance(timeframe, CanonicalTimeframe):
            raise DataIntegrityError("completeness timeframe must be an E01 outcome")
        if any(
            observation.timeframe_identity != timeframe.timeframe_identity
            or observation.timeframe_version != timeframe.timeframe_version
            or observation.calendar_identity != timeframe.calendar_identity
            or observation.calendar_version != timeframe.calendar_version
            for _, observation in pairs
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPATIBLE_TIMEFRAME,
                "observation timeframe context does not match E01",
            )

    @staticmethod
    def _validate_memberships(
        pairs: tuple[tuple[AvailabilityDecision, ObservationValidation], ...],
        memberships: tuple[tuple[str, CanonicalInterval], ...],
        required: tuple[CanonicalInterval, ...],
    ) -> None:
        identities = tuple(observation.artifact_identity for _, observation in pairs)
        if tuple(identity for identity, _ in memberships) != tuple(sorted(identities)):
            _reject(
                TemporalDiagnosticCode.MISSING_INTERVAL,
                "every observation requires one immutable interval membership",
            )
        for _, observation in pairs:
            interval = dict(memberships)[observation.artifact_identity]
            if isinstance(observation.observation, CanonicalInterval):
                if observation.observation != interval:
                    _reject(
                        TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                        "interval membership does not preserve the observation interval",
                    )
            elif not (interval.start.value <= observation.observation.value < interval.end.value):
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "point observation is outside its declared membership",
                )
        member_intervals = tuple(interval for _, interval in memberships)
        missing = tuple(interval for interval in required if interval not in member_intervals)
        if missing:
            _reject(
                TemporalDiagnosticCode.MISSING_INTERVAL,
                "required interval coverage is incomplete",
            )
        for index, left in enumerate(member_intervals):
            for right in member_intervals[index + 1 :]:
                if max(left.start.value, right.start.value) < min(left.end.value, right.end.value):
                    _reject(
                        TemporalDiagnosticCode.UNEXPECTED_INTERVAL_OVERLAP,
                        "interval memberships overlap unexpectedly",
                    )

    @staticmethod
    def _validate_closures(
        pairs: tuple[tuple[AvailabilityDecision, ObservationValidation], ...],
        closures: tuple[tuple[str, str], ...],
        declared_complete: bool,
        provisional: bool,
    ) -> None:
        identities = tuple(observation.artifact_identity for _, observation in pairs)
        if tuple(identity for identity, _ in closures) != tuple(sorted(identities)):
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "every observation requires one closure fact",
            )
        closure_map = dict(closures)
        for _, observation in pairs:
            if closure_map[observation.artifact_identity] != observation.closure_state:
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "closure fact does not match E03",
                )
        if declared_complete and any(
            state not in {"POINT", "CLOSED", "FINAL"} for _, state in closures
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "open intervals cannot be represented as complete",
            )
        if declared_complete and (
            provisional or any(observation.provisional for _, observation in pairs)
        ):
            _reject(
                TemporalDiagnosticCode.PROVISIONAL_AS_FINAL,
                "provisional observations cannot be represented as complete",
            )

    @staticmethod
    def _validate_watermark(
        pairs: tuple[tuple[AvailabilityDecision, ObservationValidation], ...],
        required: tuple[CanonicalInterval, ...],
        watermark: CanonicalInstant,
        authority: TemporalAuthorityReference,
    ) -> None:
        if not isinstance(watermark, CanonicalInstant):
            raise DataIntegrityError("watermark must be a CanonicalInstant")
        if not isinstance(authority, TemporalAuthorityReference):
            raise DataIntegrityError("watermark authority is invalid")
        if authority.authority_role != "source_boundary_admission_authority":
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "watermark requires source-boundary admission authority",
            )
        epochs = {decision.governance_epoch for decision, _ in pairs}
        if epochs != {authority.governance_epoch}:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "watermark governance epoch does not match predecessors",
            )
        instants = [watermark]
        for interval in required:
            instants.extend((interval.start, interval.end))
        if any(not _same_basis(watermark, instant) for instant in instants[1:]):
            _reject(
                TemporalDiagnosticCode.INVALID_PRECISION,
                "watermark and required intervals must share one canonical basis",
            )
        if required and watermark.value < max(interval.end.value for interval in required):
            _reject(
                TemporalDiagnosticCode.INSUFFICIENT_WATERMARK,
                "watermark does not cover every required interval",
            )
        if any(watermark.value > observation.knowledge_boundary.value for _, observation in pairs):
            _reject(
                TemporalDiagnosticCode.FUTURE_LEAKAGE,
                "watermark exceeds the frozen knowledge boundary",
            )

    @classmethod
    def validate(
        cls,
        outcome_identity: str,
        availability: tuple[AvailabilityDecision, ...],
        observations: tuple[ObservationValidation, ...],
        timeframe: CanonicalTimeframe,
        interval_memberships: tuple[tuple[str, CanonicalInterval], ...],
        required_intervals: tuple[CanonicalInterval, ...],
        closure_facts: tuple[tuple[str, str], ...],
        watermark_identity: str,
        watermark: CanonicalInstant,
        watermark_authority: TemporalAuthorityReference,
        watermark_policy_version: str,
        required_cardinality: int | None,
        declared_complete: bool,
        provisional: bool,
        policy_identity: str,
        policy_version: str,
    ) -> CompletenessDiagnostics:
        """Validate one frozen E04 completeness context without producing data."""

        outcome_id = require_text(outcome_identity, "completeness.outcome_identity")
        watermark_id = require_text(watermark_identity, "completeness.watermark_identity")
        watermark_policy = require_text(
            watermark_policy_version, "completeness.watermark_policy_version"
        )
        policy_id = require_text(policy_identity, "completeness.policy_identity")
        policy = require_text(policy_version, "completeness.policy_version")
        if required_cardinality is not None and (
            isinstance(required_cardinality, bool)
            or not isinstance(required_cardinality, int)
            or required_cardinality < 0
        ):
            raise DataIntegrityError("required cardinality must be a non-negative integer")
        if not isinstance(declared_complete, bool) or not isinstance(provisional, bool):
            raise DataIntegrityError("completeness declarations must be boolean")
        pairs = cls._bind_predecessors(availability, observations)
        cls._validate_timeframe(pairs, timeframe)
        memberships = _require_memberships(interval_memberships)
        required = _require_intervals(required_intervals, "required_intervals")
        closures = _require_closures(closure_facts)
        cls._validate_memberships(pairs, memberships, required)
        cls._validate_closures(pairs, closures, declared_complete, provisional)
        cls._validate_watermark(pairs, required, watermark, watermark_authority)
        if required_cardinality is not None and len(pairs) != required_cardinality:
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "observed cardinality does not match the declared requirement",
            )
        if not declared_complete and not provisional:
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "incomplete final window must not be accepted",
            )
        if any(not decision.provisionally_temporally_eligible for decision, _ in pairs):
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "temporally ineligible observations cannot satisfy completeness",
            )
        outcome = CompletenessOutcome(
            outcome_id,
            tuple(observation.artifact_identity for _, observation in pairs),
            tuple(observation.boundary_identity for _, observation in pairs),
            tuple(observation.consumer_temporal_boundary for _, observation in pairs),
            tuple(observation.knowledge_boundary for _, observation in pairs),
            tuple(observation.revision_lineage for _, observation in pairs),
            memberships,
            required,
            closures,
            watermark_id,
            watermark,
            watermark_authority,
            watermark_policy,
            required_cardinality,
            len(pairs),
            declared_complete,
            declared_complete and not provisional,
            provisional,
            timeframe.timeframe_identity,
            timeframe.timeframe_version,
            timeframe.calendar_identity,
            timeframe.calendar_version,
            timeframe.calendar_fact_identities,
            watermark_authority.governance_epoch,
            policy_id,
            policy,
        )
        reasons: tuple[TemporalDiagnosticReason, ...] = ()
        if provisional:
            reasons = tuple(
                TemporalDiagnosticReason(
                    TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                    observation.artifact_identity,
                    observation.boundary_identity,
                    observation.consumer_temporal_boundary,
                    observation.timeframe_identity,
                    observation.calendar_identity,
                    observation.knowledge_boundary,
                    observation.revision_lineage,
                    policy,
                    "window remains explicitly provisional",
                )
                for _, observation in pairs
            )
        return CompletenessDiagnostics((outcome,), reasons)
