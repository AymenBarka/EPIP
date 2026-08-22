"""Deterministic A05-E02 availability and knowledge-boundary analysis."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum
from typing import ClassVar, NoReturn

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.evidence.candidates import CandidateDiagnostics
from epip.evidence.model import EvidenceClaim
from epip.governance import GovernanceEpoch, RegistryEntry
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
    """Immutable value-record support local to the E02 ownership boundary."""

    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable availability model")

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


def _require_optional_instant(value: object, field: str) -> CanonicalInstant | None:
    if value is None:
        return None
    if not isinstance(value, CanonicalInstant):
        raise DataIntegrityError(f"{field} must be a CanonicalInstant")
    return value


def _instant_key(instant: CanonicalInstant) -> tuple[int, str, str, str, str]:
    return (
        instant.value,
        instant.precision,
        instant.time_scale,
        instant.timezone_basis,
        instant.authority_identity,
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


def _observation_end(boundary: TemporalBoundary) -> CanonicalInstant:
    if isinstance(boundary.observation, CanonicalInterval):
        return boundary.observation.end
    return boundary.observation


class AvailabilityStatus(str, Enum):
    """Distinct temporal availability classifications governed by ADR-05."""

    NOT_VISIBLE = "NOT_VISIBLE"
    VISIBLE = "VISIBLE"
    USABLE = "USABLE"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    OBSOLETE = "OBSOLETE"


class AvailabilityPolicy(_ImmutableRecord):
    """Immutable explicit-use policy for one availability evaluation."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "policy_identity",
        "policy_version",
        "use_identity",
        "use_time",
        "freshness_boundary",
        "expected_availability",
        "obsolescence_boundary",
        "replacement_identity",
        "authority",
    )
    _field_names = __slots__

    policy_identity: str
    policy_version: str
    use_identity: str
    use_time: CanonicalInstant
    freshness_boundary: CanonicalInstant | None
    expected_availability: CanonicalInstant | None
    obsolescence_boundary: CanonicalInstant | None
    replacement_identity: str | None
    authority: TemporalAuthorityReference

    def __init__(
        self,
        policy_identity: str,
        policy_version: str,
        use_identity: str,
        use_time: CanonicalInstant,
        freshness_boundary: CanonicalInstant | None,
        expected_availability: CanonicalInstant | None,
        obsolescence_boundary: CanonicalInstant | None,
        replacement_identity: str | None,
        authority: TemporalAuthorityReference,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in ("policy_identity", "policy_version", "use_identity"):
            require_text(getattr(self, name), f"availability_policy.{name}")
        if not isinstance(self.use_time, CanonicalInstant):
            raise DataIntegrityError("availability_policy.use_time must be a CanonicalInstant")
        for name in ("freshness_boundary", "expected_availability", "obsolescence_boundary"):
            _require_optional_instant(getattr(self, name), f"availability_policy.{name}")
        if self.replacement_identity is not None:
            require_text(self.replacement_identity, "availability_policy.replacement_identity")
        if (self.obsolescence_boundary is None) != (self.replacement_identity is None):
            raise DataIntegrityError(
                "obsolescence boundary and replacement identity must be declared together"
            )
        if not isinstance(self.authority, TemporalAuthorityReference):
            raise DataIntegrityError("availability_policy.authority is invalid")
        if self.authority.authority_role != "semantic_planning_authority":
            raise DataIntegrityError(
                "availability policy must belong to the semantic planning authority"
            )


class AvailabilityDecision(_ImmutableRecord):
    """Immutable independent availability classifications for one artifact and use."""

    __slots__ = (  # noqa: RUF023 - semantic field order
        "artifact_identity",
        "publication_identity",
        "content_identity",
        "producer_identity",
        "producer_version",
        "implementation_identity",
        "governance_snapshot_identity",
        "governance_manifest_reference",
        "governance_epoch",
        "boundary_identity",
        "use_identity",
        "publication_time",
        "availability_time",
        "knowledge_boundary",
        "observation_time",
        "use_time",
        "status",
        "visible",
        "provisionally_temporally_eligible",
        "late",
        "stale",
        "expired",
        "obsolete",
        "timeframe_identity",
        "timeframe_version",
        "calendar_identity",
        "calendar_version",
        "authority_identities",
        "policy_identity",
        "policy_version",
        "replacement_identity",
        "validity",
        "validity_rule_reference",
        "expiration_time",
        "non_expiring_policy",
        "freshness_boundary",
        "expected_availability",
        "obsolescence_boundary",
        "revision_lineage",
        "visibility_constraints",
        "authority_facts",
    )
    _field_names = __slots__

    artifact_identity: str
    publication_identity: str
    content_identity: str
    producer_identity: str
    producer_version: str
    implementation_identity: str
    governance_snapshot_identity: str
    governance_manifest_reference: str
    governance_epoch: GovernanceEpoch
    boundary_identity: str
    use_identity: str
    publication_time: CanonicalInstant
    availability_time: CanonicalInstant
    knowledge_boundary: CanonicalInstant
    observation_time: CanonicalInstant | CanonicalInterval
    use_time: CanonicalInstant
    status: AvailabilityStatus
    visible: bool
    provisionally_temporally_eligible: bool
    late: bool
    stale: bool
    expired: bool
    obsolete: bool
    timeframe_identity: str | None
    timeframe_version: str | None
    calendar_identity: str | None
    calendar_version: str | None
    authority_identities: tuple[str, ...]
    policy_identity: str
    policy_version: str
    replacement_identity: str | None
    validity: CanonicalInterval | None
    validity_rule_reference: str | None
    expiration_time: CanonicalInstant | None
    non_expiring_policy: str | None
    freshness_boundary: CanonicalInstant | None
    expected_availability: CanonicalInstant | None
    obsolescence_boundary: CanonicalInstant | None
    revision_lineage: tuple[str, ...]
    visibility_constraints: tuple[str, ...]
    authority_facts: tuple[tuple[str, str, str, GovernanceEpoch], ...]

    def __init__(
        self,
        artifact_identity: str,
        publication_identity: str,
        content_identity: str,
        producer_identity: str,
        producer_version: str,
        implementation_identity: str,
        governance_snapshot_identity: str,
        governance_manifest_reference: str,
        governance_epoch: GovernanceEpoch,
        boundary_identity: str,
        use_identity: str,
        publication_time: CanonicalInstant,
        availability_time: CanonicalInstant,
        knowledge_boundary: CanonicalInstant,
        observation_time: CanonicalInstant | CanonicalInterval,
        use_time: CanonicalInstant,
        status: AvailabilityStatus,
        visible: bool,
        provisionally_temporally_eligible: bool,
        late: bool,
        stale: bool,
        expired: bool,
        obsolete: bool,
        timeframe_identity: str | None,
        timeframe_version: str | None,
        calendar_identity: str | None,
        calendar_version: str | None,
        authority_identities: tuple[str, ...],
        policy_identity: str,
        policy_version: str,
        replacement_identity: str | None,
        validity: CanonicalInterval | None,
        validity_rule_reference: str | None,
        expiration_time: CanonicalInstant | None,
        non_expiring_policy: str | None,
        freshness_boundary: CanonicalInstant | None,
        expected_availability: CanonicalInstant | None,
        obsolescence_boundary: CanonicalInstant | None,
        revision_lineage: tuple[str, ...],
        visibility_constraints: tuple[str, ...],
        authority_facts: tuple[tuple[str, str, str, GovernanceEpoch], ...],
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "artifact_identity",
            "publication_identity",
            "content_identity",
            "producer_identity",
            "producer_version",
            "implementation_identity",
            "governance_snapshot_identity",
            "governance_manifest_reference",
            "boundary_identity",
            "use_identity",
            "policy_identity",
            "policy_version",
        ):
            require_text(getattr(self, name), f"availability_decision.{name}")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("availability_decision.governance_epoch is invalid")
        for name in ("publication_time", "availability_time", "knowledge_boundary", "use_time"):
            if not isinstance(getattr(self, name), CanonicalInstant):
                raise DataIntegrityError(f"availability_decision.{name} is invalid")
        if not isinstance(self.observation_time, (CanonicalInstant, CanonicalInterval)):
            raise DataIntegrityError("availability_decision.observation_time is invalid")
        if not isinstance(self.status, AvailabilityStatus):
            raise DataIntegrityError("availability_decision.status is invalid")
        for name in (
            "visible",
            "provisionally_temporally_eligible",
            "late",
            "stale",
            "expired",
            "obsolete",
        ):
            if not isinstance(getattr(self, name), bool):
                raise DataIntegrityError(f"availability_decision.{name} must be a boolean")
        for identity_name, version_name in (
            ("timeframe_identity", "timeframe_version"),
            ("calendar_identity", "calendar_version"),
        ):
            identity = getattr(self, identity_name)
            version = getattr(self, version_name)
            if identity is not None:
                require_text(identity, f"availability_decision.{identity_name}")
            if version is not None:
                require_text(version, f"availability_decision.{version_name}")
            if (identity is None) != (version is None):
                raise DataIntegrityError(f"{identity_name} and {version_name} must be paired")
        if not isinstance(self.authority_identities, tuple) or not self.authority_identities:
            raise MissingFieldError("availability decision requires immutable authority identities")
        for identity in self.authority_identities:
            require_text(identity, "availability_decision.authority_identities")
        if len(set(self.authority_identities)) != len(self.authority_identities):
            raise DataIntegrityError("availability authority identities must be unique")
        if self.replacement_identity is not None:
            require_text(self.replacement_identity, "availability_decision.replacement_identity")
        if self.validity is not None and not isinstance(self.validity, CanonicalInterval):
            raise DataIntegrityError("availability_decision.validity is invalid")
        for name in (
            "validity_rule_reference",
            "non_expiring_policy",
        ):
            value = getattr(self, name)
            if value is not None:
                require_text(value, f"availability_decision.{name}")
        for name in (
            "expiration_time",
            "freshness_boundary",
            "expected_availability",
            "obsolescence_boundary",
        ):
            _require_optional_instant(getattr(self, name), f"availability_decision.{name}")
        for name in ("revision_lineage", "visibility_constraints"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise DataIntegrityError(f"availability_decision.{name} must be immutable")
            for value in values:
                require_text(value, f"availability_decision.{name}")
        if not isinstance(self.authority_facts, tuple) or not self.authority_facts:
            raise MissingFieldError("availability decision requires immutable authority facts")
        for fact in self.authority_facts:
            if (
                not isinstance(fact, tuple)
                or len(fact) != 4
                or not isinstance(fact[3], GovernanceEpoch)
            ):
                raise DataIntegrityError("availability_decision.authority_facts is invalid")
            for value in fact[:3]:
                require_text(value, "availability_decision.authority_facts")
        expected_eligibility = (
            self.visible and not self.stale and not self.expired and not self.obsolete
        )
        if self.provisionally_temporally_eligible and not expected_eligibility:
            raise DataIntegrityError(
                "availability decision contains inconsistent provisional eligibility"
            )
        expected_status = _status_for(
            self.visible,
            self.stale,
            self.expired,
            self.obsolete,
        )
        if self.status is not expected_status:
            raise DataIntegrityError("availability decision status is inconsistent")
        object.__setattr__(self, "authority_identities", tuple(sorted(self.authority_identities)))
        object.__setattr__(self, "revision_lineage", tuple(sorted(self.revision_lineage)))
        object.__setattr__(
            self, "visibility_constraints", tuple(sorted(self.visibility_constraints))
        )
        object.__setattr__(self, "authority_facts", tuple(sorted(self.authority_facts)))


def _status_for(
    visible: bool,
    stale: bool,
    expired: bool,
    obsolete: bool,
) -> AvailabilityStatus:
    if not visible:
        return AvailabilityStatus.NOT_VISIBLE
    if expired:
        return AvailabilityStatus.EXPIRED
    if obsolete:
        return AvailabilityStatus.OBSOLETE
    if stale:
        return AvailabilityStatus.STALE
    return AvailabilityStatus.VISIBLE


def _decision_key(item: AvailabilityDecision) -> tuple[object, ...]:
    observation_key: tuple[object, ...]
    if isinstance(item.observation_time, CanonicalInterval):
        observation_key = (
            "INTERVAL",
            _instant_key(item.observation_time.start),
            _instant_key(item.observation_time.end),
            item.observation_time.boundary_convention.value,
        )
    else:
        observation_key = ("INSTANT", _instant_key(item.observation_time))
    return (
        item.artifact_identity,
        item.publication_identity,
        item.content_identity,
        item.producer_identity,
        item.producer_version,
        item.implementation_identity,
        item.governance_snapshot_identity,
        item.governance_manifest_reference,
        item.governance_epoch.sequence,
        item.boundary_identity,
        item.use_identity,
        _instant_key(item.publication_time),
        _instant_key(item.availability_time),
        _instant_key(item.knowledge_boundary),
        observation_key,
        _instant_key(item.use_time),
        item.status.value,
        item.visible,
        item.provisionally_temporally_eligible,
        item.late,
        item.stale,
        item.expired,
        item.obsolete,
        item.timeframe_identity or "",
        item.timeframe_version or "",
        item.calendar_identity or "",
        item.calendar_version or "",
        item.authority_identities,
        item.policy_identity,
        item.policy_version,
        item.replacement_identity or "",
        (
            (
                _instant_key(item.validity.start),
                _instant_key(item.validity.end),
                item.validity.boundary_convention.value,
            )
            if item.validity is not None
            else ()
        ),
        item.validity_rule_reference or "",
        _instant_key(item.expiration_time) if item.expiration_time is not None else (),
        item.non_expiring_policy or "",
        _instant_key(item.freshness_boundary) if item.freshness_boundary is not None else (),
        _instant_key(item.expected_availability) if item.expected_availability is not None else (),
        _instant_key(item.obsolescence_boundary) if item.obsolescence_boundary is not None else (),
        item.revision_lineage,
        item.visibility_constraints,
        tuple(
            (role, identity, version, epoch.sequence)
            for role, identity, version, epoch in item.authority_facts
        ),
    )


class AvailabilityDiagnostics(_ImmutableRecord):
    """Immutable deterministic E02 decisions and diagnostic pairs."""

    __slots__ = ("decisions", "reasons")
    _field_names = __slots__

    decisions: tuple[AvailabilityDecision, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        decisions: tuple[AvailabilityDecision, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.decisions, tuple) or any(
            not isinstance(item, AvailabilityDecision) for item in self.decisions
        ):
            raise DataIntegrityError("availability diagnostics require immutable decisions")
        if not isinstance(self.reasons, tuple) or any(
            not isinstance(item, TemporalDiagnosticReason) for item in self.reasons
        ):
            raise DataIntegrityError("availability diagnostics require immutable temporal reasons")
        decisions = tuple(sorted(self.decisions, key=_decision_key))
        if len(set(decisions)) != len(decisions):
            raise DataIntegrityError(
                "availability diagnostics must not contain duplicate decisions"
            )
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
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(self, "reasons", reasons)


class AvailabilityAnalyzer:
    """Evaluate availability from frozen facts without successor responsibilities."""

    __slots__ = ()

    @staticmethod
    def _validate_authority(
        boundary: TemporalBoundary,
        policy: AvailabilityPolicy,
        governance: CandidateDiagnostics,
        publication: EvidenceClaim,
    ) -> RegistryEntry:
        if not isinstance(governance, CandidateDiagnostics):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "authoritative governance and trust outcome is mandatory",
            )
        roles = {authority.authority_role for authority in boundary.authorities}
        required = {"source_authority", "source_boundary_admission_authority"}
        if not required <= roles:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "source and availability admission authorities are mandatory",
            )
        epochs = {authority.governance_epoch for authority in boundary.authorities}
        if (
            policy.authority.governance_epoch not in epochs
            or governance.governance_epoch not in epochs
        ):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "availability policy governance epoch does not match the frozen boundary",
            )
        matches = tuple(
            entry
            for entry in governance.candidates
            if entry.producer_identity == publication.source_identity
            and entry.producer_version == publication.implementation_version
        )
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "publication lacks one authoritative admitted governance and trust outcome",
            )
        return matches[0]

    @staticmethod
    def _validate_timeframe(
        boundary: TemporalBoundary,
        timeframe: CanonicalTimeframe | None,
    ) -> None:
        if boundary.timeframe_identity is None:
            if timeframe is not None:
                _reject(
                    TemporalDiagnosticCode.INCOMPATIBLE_TIMEFRAME,
                    "unscoped temporal boundary must not receive a timeframe outcome",
                )
            return
        if timeframe is None:
            _reject(
                TemporalDiagnosticCode.MISSING_TIMEFRAME,
                "timeframe-scoped temporal boundary requires an E01 outcome",
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
                "E01 timeframe outcome does not match the temporal boundary",
            )

    @staticmethod
    def _validate_bases(boundary: TemporalBoundary, policy: AvailabilityPolicy) -> None:
        instants = [
            boundary.publication,
            boundary.availability,
            boundary.knowledge,
            policy.use_time,
            _observation_end(boundary),
        ]
        for optional in (
            boundary.expiration,
            policy.freshness_boundary,
            policy.expected_availability,
            policy.obsolescence_boundary,
        ):
            if optional is not None:
                instants.append(optional)
        if boundary.validity is not None:
            instants.extend((boundary.validity.start, boundary.validity.end))
        if any(not _same_basis(instants[0], item) for item in instants[1:]):
            _reject(
                TemporalDiagnosticCode.INVALID_PRECISION,
                "availability evaluation requires one canonical basis",
            )

    @classmethod
    def evaluate(
        cls,
        publication: EvidenceClaim,
        boundary: TemporalBoundary,
        policy: AvailabilityPolicy,
        governance: CandidateDiagnostics,
        timeframe: CanonicalTimeframe | None = None,
    ) -> AvailabilityDiagnostics:
        """Classify one artifact relative to its frozen knowledge and use boundary."""

        if not isinstance(publication, EvidenceClaim):
            _reject(
                TemporalDiagnosticCode.MISSING_PUBLICATION_TIME,
                "authoritative immutable publication identity is mandatory",
            )
        if not isinstance(boundary, TemporalBoundary):
            raise DataIntegrityError("availability boundary must be a TemporalBoundary")
        if not isinstance(policy, AvailabilityPolicy):
            raise DataIntegrityError("availability policy must be immutable")
        if timeframe is not None and not isinstance(timeframe, CanonicalTimeframe):
            raise DataIntegrityError("availability timeframe must be a CanonicalTimeframe")
        entry = cls._validate_authority(boundary, policy, governance, publication)
        cls._validate_timeframe(boundary, timeframe)
        cls._validate_bases(boundary, policy)
        if boundary.availability.value < boundary.publication.value:
            _reject(
                TemporalDiagnosticCode.FUTURE_LEAKAGE,
                "availability cannot precede publication",
            )

        visible = (
            boundary.publication.value <= boundary.knowledge.value
            and boundary.availability.value <= boundary.knowledge.value
        )
        late = (
            policy.expected_availability is not None
            and boundary.availability.value > policy.expected_availability.value
        )
        stale = (
            policy.freshness_boundary is not None
            and _observation_end(boundary).value < policy.freshness_boundary.value
        )
        expired = (
            boundary.expiration is not None
            and boundary.knowledge.value >= boundary.expiration.value
        )
        obsolete = (
            policy.obsolescence_boundary is not None
            and boundary.knowledge.value >= policy.obsolescence_boundary.value
        )
        if boundary.validity is None:
            validity_satisfied = False
        else:
            validity_satisfied = (
                boundary.validity.start.value <= policy.use_time.value < boundary.validity.end.value
            )
        provisionally_eligible = (
            visible and validity_satisfied and not stale and not expired and not obsolete
        )
        status = _status_for(visible, stale, expired, obsolete)

        diagnostic_pairs: list[tuple[TemporalDiagnosticCode, str]] = []
        if late:
            diagnostic_pairs.append(
                (
                    TemporalDiagnosticCode.LATE_ARRIVAL,
                    "availability exceeds the explicit expected boundary",
                )
            )
        if stale:
            diagnostic_pairs.append(
                (
                    TemporalDiagnosticCode.STALE_EVIDENCE,
                    "observation precedes the explicit freshness boundary",
                )
            )
        if expired:
            diagnostic_pairs.append(
                (
                    TemporalDiagnosticCode.EXPIRED_EVIDENCE,
                    "knowledge boundary reached the explicit expiration time",
                )
            )
        if not validity_satisfied:
            diagnostic_pairs.append(
                (
                    TemporalDiagnosticCode.MISSING_VALIDITY_TIME,
                    "validity does not cover the explicit use time",
                )
            )

        authority_identities = tuple(
            sorted(
                {
                    *(authority.authority_identity for authority in boundary.authorities),
                    policy.authority.authority_identity,
                }
            )
        )
        decision = AvailabilityDecision(
            publication.evidence_id,
            publication.evidence_id,
            publication.content_identity,
            publication.source_identity,
            publication.implementation_version,
            entry.implementation_identity,
            governance.snapshot_identity,
            governance.manifest_reference,
            governance.governance_epoch,
            boundary.boundary_identity,
            policy.use_identity,
            boundary.publication,
            boundary.availability,
            boundary.knowledge,
            boundary.observation,
            policy.use_time,
            status,
            visible,
            provisionally_eligible,
            late,
            stale,
            expired,
            obsolete,
            boundary.timeframe_identity,
            boundary.timeframe_version,
            boundary.calendar_identity,
            boundary.calendar_version,
            authority_identities,
            policy.policy_identity,
            policy.policy_version,
            policy.replacement_identity if obsolete else None,
            boundary.validity,
            boundary.validity_rule_reference,
            boundary.expiration,
            boundary.non_expiring_policy,
            policy.freshness_boundary,
            policy.expected_availability,
            policy.obsolescence_boundary,
            boundary.revision_lineage,
            boundary.visibility_constraints,
            tuple(
                sorted(
                    (
                        authority.authority_role,
                        authority.authority_identity,
                        authority.authority_version,
                        authority.governance_epoch,
                    )
                    for authority in (*boundary.authorities, policy.authority)
                )
            ),
        )
        reasons = tuple(
            TemporalDiagnosticReason(
                code,
                publication.evidence_id,
                boundary.boundary_identity,
                policy.use_identity,
                boundary.timeframe_identity,
                boundary.calendar_identity,
                boundary.knowledge,
                boundary.revision_lineage,
                policy.policy_version,
                reason,
            )
            for code, reason in diagnostic_pairs
        )
        return AvailabilityDiagnostics((decision,), reasons)
