"""Deterministic A05-E06 revision and historical-continuity validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar, NoReturn, cast

from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.governance import GovernanceEpoch
from epip.temporal.availability import AvailabilityDecision, AvailabilityStatus
from epip.temporal.completeness import CompletenessOutcome
from epip.temporal.dependency import TemporalDependencyValidation
from epip.temporal.model import (
    CanonicalInstant,
    TemporalAuthorityReference,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.observation import ObservationValidation


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable revision model")

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


def _instant_key(value: CanonicalInstant) -> tuple[int, str, str, str, str]:
    return (
        value.value,
        value.precision,
        value.time_scale,
        value.timezone_basis,
        value.authority_identity,
    )


def _same_basis(left: CanonicalInstant, right: CanonicalInstant) -> bool:
    return _instant_key(left)[1:] == _instant_key(right)[1:]


class RevisionValidation(_ImmutableRecord):
    """Immutable self-contained E06 revision and usability outcome."""

    __slots__ = (  # noqa: RUF023 - normative context order
        "validation_identity",
        "artifact_identity",
        "publication_identity",
        "boundary_identity",
        "consumer_boundary",
        "publication_time",
        "availability_time",
        "observation_time",
        "knowledge_boundary",
        "historical_boundary",
        "revision_lineage",
        "correction_facts",
        "replacement_facts",
        "withdrawal_facts",
        "scope_facts",
        "selected_revision_identity",
        "prior_plan_interpretation",
        "authority_facts",
        "governance_epoch",
        "completeness_identity",
        "dependency_identities",
        "timeframe_identity",
        "calendar_identity",
        "visible",
        "provisionally_temporally_eligible",
        "complete",
        "dependency_valid",
        "revision_valid",
        "consumer_policy_satisfied",
        "withdrawn",
        "status",
        "policy_identity",
        "policy_version",
    )
    _field_names = __slots__

    validation_identity: str
    artifact_identity: str
    publication_identity: str
    boundary_identity: str
    consumer_boundary: str
    publication_time: CanonicalInstant
    availability_time: CanonicalInstant
    observation_time: CanonicalInstant
    knowledge_boundary: CanonicalInstant
    historical_boundary: CanonicalInstant
    revision_lineage: tuple[str, ...]
    correction_facts: tuple[tuple[str, str, CanonicalInstant, str], ...]
    replacement_facts: tuple[tuple[str, str, str, int, CanonicalInstant, str], ...]
    withdrawal_facts: tuple[tuple[str, str, CanonicalInstant, str], ...]
    scope_facts: tuple[tuple[str, tuple[str, ...], str], ...]
    selected_revision_identity: str
    prior_plan_interpretation: tuple[tuple[str, str], ...]
    authority_facts: tuple[tuple[str, str, str, GovernanceEpoch], ...]
    governance_epoch: GovernanceEpoch
    completeness_identity: str
    dependency_identities: tuple[str, ...]
    timeframe_identity: str
    calendar_identity: str
    visible: bool
    provisionally_temporally_eligible: bool
    complete: bool
    dependency_valid: bool
    revision_valid: bool
    consumer_policy_satisfied: bool
    withdrawn: bool
    status: AvailabilityStatus
    policy_identity: str
    policy_version: str

    def __init__(
        self,
        validation_identity: str,
        artifact_identity: str,
        publication_identity: str,
        boundary_identity: str,
        consumer_boundary: str,
        publication_time: CanonicalInstant,
        availability_time: CanonicalInstant,
        observation_time: CanonicalInstant,
        knowledge_boundary: CanonicalInstant,
        historical_boundary: CanonicalInstant,
        revision_lineage: tuple[str, ...],
        correction_facts: tuple[tuple[str, str, CanonicalInstant, str], ...],
        replacement_facts: tuple[tuple[str, str, str, int, CanonicalInstant, str], ...],
        withdrawal_facts: tuple[tuple[str, str, CanonicalInstant, str], ...],
        scope_facts: tuple[tuple[str, tuple[str, ...], str], ...],
        selected_revision_identity: str,
        prior_plan_interpretation: tuple[tuple[str, str], ...],
        authority_facts: tuple[tuple[str, str, str, GovernanceEpoch], ...],
        governance_epoch: GovernanceEpoch,
        completeness_identity: str,
        dependency_identities: tuple[str, ...],
        timeframe_identity: str,
        calendar_identity: str,
        visible: bool,
        provisionally_temporally_eligible: bool,
        complete: bool,
        dependency_valid: bool,
        revision_valid: bool,
        consumer_policy_satisfied: bool,
        withdrawn: bool,
        status: AvailabilityStatus,
        policy_identity: str,
        policy_version: str,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "validation_identity",
            "artifact_identity",
            "publication_identity",
            "boundary_identity",
            "consumer_boundary",
            "selected_revision_identity",
            "completeness_identity",
            "timeframe_identity",
            "calendar_identity",
            "policy_identity",
            "policy_version",
        ):
            require_text(getattr(self, name), f"revision_validation.{name}")
        for name in (
            "publication_time",
            "availability_time",
            "observation_time",
            "knowledge_boundary",
            "historical_boundary",
        ):
            if not isinstance(getattr(self, name), CanonicalInstant):
                raise DataIntegrityError(f"revision_validation.{name} is invalid")
        if not isinstance(self.revision_lineage, tuple) or not self.revision_lineage:
            raise MissingFieldError("revision validation requires immutable revision lineage")
        for identity in self.revision_lineage:
            require_text(identity, "revision_validation.revision_lineage")
        for name in (
            "correction_facts",
            "replacement_facts",
            "withdrawal_facts",
            "scope_facts",
            "prior_plan_interpretation",
            "authority_facts",
            "dependency_identities",
        ):
            if not isinstance(getattr(self, name), tuple):
                raise DataIntegrityError(f"revision_validation.{name} must be immutable")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("revision validation governance epoch is invalid")
        temporal_facts = (
            self.publication_time,
            self.availability_time,
            self.observation_time,
            self.historical_boundary,
        )
        if any(not _same_basis(self.knowledge_boundary, item) for item in temporal_facts):
            raise DataIntegrityError("revision validation temporal basis is inconsistent")
        if (
            self.publication_time.value > self.availability_time.value
            or self.availability_time.value > self.knowledge_boundary.value
            or self.observation_time.value > self.knowledge_boundary.value
            or self.historical_boundary.value > self.knowledge_boundary.value
        ):
            raise DataIntegrityError("revision validation historical ordering is inconsistent")
        authority_map: dict[str, tuple[str, str, str, GovernanceEpoch]] = {}
        for authority_input in self.authority_facts:
            if (
                not isinstance(authority_input, tuple)
                or len(authority_input) != 4
                or not isinstance(authority_input[3], GovernanceEpoch)
            ):
                raise DataIntegrityError("revision validation authority fact is invalid")
            for value in authority_input[:3]:
                require_text(value, "revision_validation.authority_fact")
            if authority_input[1] in authority_map:
                raise DataIntegrityError("revision validation authority facts must be unique")
            if authority_input[3] != self.governance_epoch:
                raise DataIntegrityError("revision validation authority epoch is inconsistent")
            authority_map[authority_input[1]] = authority_input
        scope_map: dict[str, tuple[str, ...]] = {}
        for scope_fact in self.scope_facts:
            if (
                not isinstance(scope_fact, tuple)
                or len(scope_fact) != 3
                or not isinstance(scope_fact[1], tuple)
                or not scope_fact[1]
            ):
                raise DataIntegrityError("revision validation scope fact is invalid")
            scope = require_text(scope_fact[0], "revision_validation.scope")
            scope_authority = require_text(scope_fact[2], "revision_validation.scope_authority")
            for identity in scope_fact[1]:
                require_text(identity, "revision_validation.scope_artifact")
            if scope in scope_map or len(set(scope_fact[1])) != len(scope_fact[1]):
                raise DataIntegrityError("revision validation scope facts must be unique")
            authority_fact = authority_map.get(scope_authority)
            if authority_fact is None or authority_fact[0] != "revision_scope_authority":
                raise DataIntegrityError("revision validation scope authority is invalid")
            scope_map[scope] = tuple(sorted(scope_fact[1]))
        for correction_fact in self.correction_facts:
            if (
                not isinstance(correction_fact, tuple)
                or len(correction_fact) != 4
                or not isinstance(correction_fact[2], CanonicalInstant)
            ):
                raise DataIntegrityError("revision validation correction fact is invalid")
            for value in correction_fact[:2]:
                require_text(value, "revision_validation.correction_identity")
            require_text(correction_fact[3], "revision_validation.correction_authority")
            if not _same_basis(self.knowledge_boundary, correction_fact[2]):
                raise DataIntegrityError("revision validation correction basis is inconsistent")
            if (
                correction_fact[0] == correction_fact[1]
                or correction_fact[0] not in self.revision_lineage
                or correction_fact[1] not in self.revision_lineage
            ):
                raise DataIntegrityError("revision validation correction lineage is inconsistent")
            correction_authority = authority_map.get(correction_fact[3])
            if correction_authority is None or correction_authority[0] != "correction_authority":
                raise DataIntegrityError("revision validation correction authority is invalid")
        if len(set(self.correction_facts)) != len(self.correction_facts):
            raise DataIntegrityError("revision validation correction facts must be unique")
        for replacement_fact in self.replacement_facts:
            if (
                not isinstance(replacement_fact, tuple)
                or len(replacement_fact) != 6
                or isinstance(replacement_fact[3], bool)
                or not isinstance(replacement_fact[3], int)
                or not isinstance(replacement_fact[4], CanonicalInstant)
            ):
                raise DataIntegrityError("revision validation replacement fact is invalid")
            for value in replacement_fact[:3]:
                require_text(value, "revision_validation.replacement_fact")
            require_text(replacement_fact[5], "revision_validation.replacement_authority")
            if not _same_basis(self.knowledge_boundary, replacement_fact[4]):
                raise DataIntegrityError("revision validation replacement basis is inconsistent")
            if (
                replacement_fact[0] == replacement_fact[1]
                or replacement_fact[0] not in self.revision_lineage
                or replacement_fact[1] not in self.revision_lineage
            ):
                raise DataIntegrityError("revision validation replacement lineage is inconsistent")
            if (
                replacement_fact[2] not in scope_map
                or replacement_fact[0] not in scope_map[replacement_fact[2]]
            ):
                raise DataIntegrityError("revision validation replacement scope is inapplicable")
            replacement_authority = authority_map.get(replacement_fact[5])
            if replacement_authority is None or replacement_authority[0] != "replacement_authority":
                raise DataIntegrityError("revision validation replacement authority is invalid")
        if len(set(self.replacement_facts)) != len(self.replacement_facts):
            raise DataIntegrityError("revision validation replacement facts must be unique")
        for withdrawal_fact in self.withdrawal_facts:
            if (
                not isinstance(withdrawal_fact, tuple)
                or len(withdrawal_fact) != 4
                or not isinstance(withdrawal_fact[2], CanonicalInstant)
            ):
                raise DataIntegrityError("revision validation withdrawal fact is invalid")
            require_text(withdrawal_fact[0], "revision_validation.withdrawal_identity")
            require_text(withdrawal_fact[1], "revision_validation.withdrawal_scope")
            require_text(withdrawal_fact[3], "revision_validation.withdrawal_authority")
            if not _same_basis(self.knowledge_boundary, withdrawal_fact[2]):
                raise DataIntegrityError("revision validation withdrawal basis is inconsistent")
            if withdrawal_fact[0] not in self.revision_lineage:
                raise DataIntegrityError("revision validation withdrawal lineage is inconsistent")
            if (
                withdrawal_fact[1] not in scope_map
                or withdrawal_fact[0] not in scope_map[withdrawal_fact[1]]
            ):
                raise DataIntegrityError("revision validation withdrawal scope is inapplicable")
            withdrawal_authority = authority_map.get(withdrawal_fact[3])
            if withdrawal_authority is None or withdrawal_authority[0] != "withdrawal_authority":
                raise DataIntegrityError("revision validation withdrawal authority is invalid")
        if len(set(self.withdrawal_facts)) != len(self.withdrawal_facts):
            raise DataIntegrityError("revision validation withdrawal facts must be unique")
        RevisionValidator._pairs(self.prior_plan_interpretation, "prior plan interpretation")
        if not self.prior_plan_interpretation:
            raise MissingFieldError("revision validation prior plan interpretation is required")
        if not self.dependency_identities:
            raise MissingFieldError("revision validation dependency identities are required")
        for identity in self.dependency_identities:
            require_text(identity, "revision_validation.dependency_identity")
        if len(set(self.dependency_identities)) != len(self.dependency_identities):
            raise DataIntegrityError("revision validation dependency identities must be unique")
        possible_revisions = set(self.revision_lineage)
        possible_revisions.update(item[1] for item in self.correction_facts)
        possible_revisions.update(item[1] for item in self.replacement_facts)
        if self.selected_revision_identity not in possible_revisions:
            raise DataIntegrityError("revision validation selected revision is inconsistent")
        for name in (
            "visible",
            "provisionally_temporally_eligible",
            "complete",
            "dependency_valid",
            "revision_valid",
            "consumer_policy_satisfied",
            "withdrawn",
        ):
            if not isinstance(getattr(self, name), bool):
                raise DataIntegrityError(f"revision_validation.{name} must be boolean")
        if not isinstance(self.status, AvailabilityStatus):
            raise DataIntegrityError("revision validation status is invalid")
        usable = (
            self.visible
            and self.provisionally_temporally_eligible
            and self.complete
            and self.dependency_valid
            and self.revision_valid
            and self.consumer_policy_satisfied
            and not self.withdrawn
        )
        if (self.status is AvailabilityStatus.USABLE) != usable:
            raise DataIntegrityError("revision validation final usability state is inconsistent")
        object.__setattr__(self, "revision_lineage", tuple(self.revision_lineage))
        object.__setattr__(
            self,
            "correction_facts",
            tuple(
                sorted(
                    self.correction_facts,
                    key=lambda item: (item[0], item[1], _instant_key(item[2]), item[3]),
                )
            ),
        )
        object.__setattr__(
            self,
            "replacement_facts",
            tuple(
                sorted(
                    self.replacement_facts,
                    key=lambda item: (
                        item[0],
                        item[1],
                        item[2],
                        item[3],
                        _instant_key(item[4]),
                        item[5],
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "withdrawal_facts",
            tuple(
                sorted(
                    self.withdrawal_facts,
                    key=lambda item: (item[0], item[1], _instant_key(item[2]), item[3]),
                )
            ),
        )
        object.__setattr__(
            self,
            "scope_facts",
            tuple(sorted(self.scope_facts, key=lambda item: (item[0], item[1], item[2]))),
        )
        object.__setattr__(
            self, "prior_plan_interpretation", tuple(sorted(self.prior_plan_interpretation))
        )
        object.__setattr__(self, "authority_facts", tuple(sorted(self.authority_facts)))
        object.__setattr__(self, "dependency_identities", tuple(sorted(self.dependency_identities)))


def _validation_key(value: RevisionValidation) -> tuple[object, ...]:
    return value._values()


class RevisionDiagnostics(_ImmutableRecord):
    """Immutable deterministic E06 validations and attributed diagnostics."""

    __slots__ = ("validations", "reasons")  # noqa: RUF023 - semantic field order
    _field_names = __slots__

    validations: tuple[RevisionValidation, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        validations: tuple[RevisionValidation, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.validations, tuple) or any(
            not isinstance(item, RevisionValidation) for item in self.validations
        ):
            raise DataIntegrityError("revision diagnostics require immutable validations")
        if not isinstance(self.reasons, tuple) or any(
            not isinstance(item, TemporalDiagnosticReason) for item in self.reasons
        ):
            raise DataIntegrityError("revision diagnostics require immutable reasons")
        validations = tuple(sorted(self.validations, key=_validation_key))
        if len(set(validations)) != len(validations):
            raise DataIntegrityError("revision diagnostics contain duplicate validations")
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
        for reason in reasons:
            matches = tuple(
                item
                for item in validations
                if reason.affected_evidence == item.artifact_identity
                and reason.source_boundary == item.boundary_identity
                and reason.consumer_boundary == item.consumer_boundary
                and reason.knowledge_boundary == item.knowledge_boundary
                and reason.revision_lineage == item.revision_lineage
                and reason.policy_version == item.policy_version
                and (reason.timeframe_identity or "") == item.timeframe_identity
                and (reason.calendar_identity or "") == item.calendar_identity
            )
            if len(matches) != 1:
                raise DataIntegrityError(
                    "revision diagnostic reason is orphaned, mismatched, or ambiguous"
                )
        if len(set(reasons)) != len(reasons):
            raise DataIntegrityError("revision diagnostics contain duplicate reasons")
        bindings: dict[tuple[object, ...], tuple[TemporalDiagnosticCode, str]] = {}
        for reason in reasons:
            binding = (
                reason.affected_evidence,
                reason.source_boundary,
                reason.consumer_boundary,
                reason.timeframe_identity,
                reason.calendar_identity,
                reason.knowledge_boundary,
                reason.revision_lineage,
                reason.policy_version,
            )
            outcome = (reason.code, reason.reason)
            if binding in bindings and bindings[binding] != outcome:
                raise DataIntegrityError("revision diagnostics contain inconsistent bindings")
            bindings[binding] = outcome
        object.__setattr__(self, "validations", validations)
        object.__setattr__(self, "reasons", reasons)


class RevisionValidator:
    """Validate revision continuity and determine final temporal usability."""

    __slots__ = ()

    @classmethod
    def validate(
        cls,
        validation_identity: str,
        artifact_identity: str,
        availability: tuple[AvailabilityDecision, ...],
        observations: tuple[ObservationValidation, ...],
        completeness: tuple[CompletenessOutcome, ...],
        dependencies: tuple[TemporalDependencyValidation, ...],
        correction_facts: tuple[tuple[str, str, CanonicalInstant, str], ...],
        replacement_facts: tuple[tuple[str, str, str, int, CanonicalInstant, str], ...],
        withdrawal_facts: tuple[tuple[str, str, CanonicalInstant, str], ...],
        scope_facts: tuple[tuple[str, tuple[str, ...], str], ...],
        revision_lineage: tuple[str, ...],
        authorities: tuple[TemporalAuthorityReference, ...],
        historical_boundary: CanonicalInstant,
        prior_plan_interpretation: tuple[tuple[str, str], ...],
        consumer_requirements: tuple[tuple[str, bool], ...],
        policy_identity: str,
        policy_version: str,
    ) -> RevisionDiagnostics:
        validation_id = require_text(validation_identity, "revision.validation_identity")
        artifact_id = require_text(artifact_identity, "revision.artifact_identity")
        policy_id = require_text(policy_identity, "revision.policy_identity")
        policy = require_text(policy_version, "revision.policy_version")
        for value, name in (
            (availability, "availability"),
            (observations, "observations"),
            (completeness, "completeness"),
            (dependencies, "dependencies"),
            (correction_facts, "correction facts"),
            (replacement_facts, "replacement facts"),
            (withdrawal_facts, "withdrawal facts"),
            (scope_facts, "scope facts"),
            (revision_lineage, "revision lineage"),
            (authorities, "authorities"),
            (prior_plan_interpretation, "prior plan interpretation"),
            (consumer_requirements, "consumer requirements"),
        ):
            if not isinstance(value, tuple):
                raise DataIntegrityError(f"{name} must be immutable")
        if not isinstance(historical_boundary, CanonicalInstant):
            raise DataIntegrityError("historical boundary is invalid")
        decision = cast(
            AvailabilityDecision,
            cls._one(artifact_id, availability, AvailabilityDecision, "availability"),
        )
        observation = cast(
            ObservationValidation,
            cls._one(artifact_id, observations, ObservationValidation, "observation"),
        )
        complete = cls._one_containing(artifact_id, completeness)
        relevant_dependencies = tuple(
            item
            for item in dependencies
            if artifact_id in {item.source_artifact_identity, item.target_artifact_identity}
        )
        if not relevant_dependencies or any(not item.valid for item in relevant_dependencies):
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "mandatory dependency validation is missing or rejected",
            )
        cls._bind(decision, observation, complete, relevant_dependencies)
        lineage = cls._lineage(revision_lineage, decision)
        authority_map = cls._authorities(authorities, decision.governance_epoch)
        scopes = cls._scopes(scope_facts, authority_map)
        corrections = cls._corrections(
            correction_facts, lineage, authority_map, decision.knowledge_boundary
        )
        replacements = cls._replacements(
            replacement_facts, lineage, authority_map, scopes, decision.knowledge_boundary
        )
        withdrawals = cls._withdrawals(
            withdrawal_facts, lineage, authority_map, scopes, decision.knowledge_boundary
        )
        requirements = cls._requirements(consumer_requirements)
        if not prior_plan_interpretation:
            raise MissingFieldError("prior plan interpretation is required")
        cls._pairs(prior_plan_interpretation, "prior plan interpretation")
        if not _same_basis(historical_boundary, decision.knowledge_boundary):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "historical boundary temporal basis is incompatible",
            )
        if historical_boundary.value > decision.knowledge_boundary.value:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "historical boundary exceeds frozen knowledge",
            )
        selected = cls._select_revision(
            lineage, corrections, replacements, decision.knowledge_boundary
        )
        withdrawn = any(
            item[0] == selected and item[2].value <= decision.knowledge_boundary.value
            for item in withdrawals
        )
        mandatory_policy = all(requirements.values())
        usable = (
            decision.visible
            and decision.provisionally_temporally_eligible
            and complete.complete
            and all(item.valid for item in relevant_dependencies)
            and not withdrawn
            and mandatory_policy
        )
        status = (
            AvailabilityStatus.USABLE
            if usable
            else (AvailabilityStatus.OBSOLETE if withdrawn else AvailabilityStatus.VISIBLE)
        )
        validation = RevisionValidation(
            validation_id,
            artifact_id,
            decision.publication_identity,
            decision.boundary_identity,
            decision.use_identity,
            decision.publication_time,
            decision.availability_time,
            (
                observation.observation
                if isinstance(observation.observation, CanonicalInstant)
                else observation.observation.end
            ),
            decision.knowledge_boundary,
            historical_boundary,
            lineage,
            corrections,
            replacements,
            withdrawals,
            tuple(sorted(scope_facts, key=lambda item: (item[0], item[1], item[2]))),
            selected,
            prior_plan_interpretation,
            tuple(
                (
                    item.authority_role,
                    item.authority_identity,
                    item.authority_version,
                    item.governance_epoch,
                )
                for item in authorities
            ),
            decision.governance_epoch,
            complete.outcome_identity,
            tuple(item.dependency_identity for item in relevant_dependencies),
            decision.timeframe_identity or "",
            decision.calendar_identity or "",
            decision.visible,
            decision.provisionally_temporally_eligible,
            complete.complete,
            all(item.valid for item in relevant_dependencies),
            True,
            mandatory_policy,
            withdrawn,
            status,
            policy_id,
            policy,
        )
        reasons: tuple[TemporalDiagnosticReason, ...] = ()
        if status is not AvailabilityStatus.USABLE:
            reasons = (
                TemporalDiagnosticReason(
                    (
                        TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION
                        if withdrawn
                        else TemporalDiagnosticCode.HISTORICAL_AMBIGUITY
                    ),
                    artifact_id,
                    decision.boundary_identity,
                    decision.use_identity,
                    decision.timeframe_identity,
                    decision.calendar_identity,
                    decision.knowledge_boundary,
                    lineage,
                    policy,
                    "artifact is not finally usable",
                ),
            )
        return RevisionDiagnostics((validation,), reasons)

    @staticmethod
    def _one(
        identity: str, values: tuple[object, ...], expected: type[object], name: str
    ) -> object:
        matches = tuple(
            item
            for item in values
            if isinstance(item, expected) and getattr(item, "artifact_identity", None) == identity
        )
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                f"{name} outcome is missing or ambiguous",
            )
        return matches[0]

    @staticmethod
    def _one_containing(
        identity: str, values: tuple[CompletenessOutcome, ...]
    ) -> CompletenessOutcome:
        matches = tuple(
            item
            for item in values
            if isinstance(item, CompletenessOutcome) and identity in item.artifact_identities
        )
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "completeness outcome is missing or ambiguous",
            )
        return matches[0]

    @staticmethod
    def _bind(
        decision: AvailabilityDecision,
        observation: ObservationValidation,
        complete: CompletenessOutcome,
        dependencies: tuple[TemporalDependencyValidation, ...],
    ) -> None:
        if (
            decision.boundary_identity != observation.boundary_identity
            or decision.use_identity != observation.consumer_temporal_boundary
            or decision.knowledge_boundary != observation.knowledge_boundary
            or decision.revision_lineage != observation.revision_lineage
            or decision.artifact_identity not in complete.artifact_identities
            or decision.knowledge_boundary not in complete.knowledge_boundaries
            or any(item.governance_epoch != decision.governance_epoch for item in dependencies)
        ):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY, "predecessor context is inconsistent"
            )

    @staticmethod
    def _lineage(value: tuple[str, ...], decision: AvailabilityDecision) -> tuple[str, ...]:
        if not value:
            raise MissingFieldError("revision lineage is required")
        for identity in value:
            require_text(identity, "revision.lineage")
        result = tuple(sorted(value))
        if result != decision.revision_lineage:
            _reject(
                TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION,
                "revision lineage does not match predecessor",
            )
        return result

    @staticmethod
    def _authorities(
        values: tuple[TemporalAuthorityReference, ...], epoch: GovernanceEpoch
    ) -> dict[str, TemporalAuthorityReference]:
        if not values or any(not isinstance(item, TemporalAuthorityReference) for item in values):
            raise MissingFieldError("immutable revision authorities are required")
        result = {item.authority_identity: item for item in values}
        if len(result) != len(values) or any(item.governance_epoch != epoch for item in values):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "revision authority context is inconsistent",
            )
        return result

    @staticmethod
    def _pairs(value: tuple[tuple[str, str], ...], name: str) -> None:
        for item in value:
            if not isinstance(item, tuple) or len(item) != 2:
                raise DataIntegrityError(f"{name} contains an unsupported fact")
            require_text(item[0], name)
            require_text(item[1], name)

    @classmethod
    def _scopes(
        cls,
        values: tuple[tuple[str, tuple[str, ...], str], ...],
        authorities: dict[str, TemporalAuthorityReference],
    ) -> dict[str, tuple[str, ...]]:
        if not values:
            raise MissingFieldError("immutable revision scope facts are required")
        result: dict[str, tuple[str, ...]] = {}
        for item in values:
            if (
                not isinstance(item, tuple)
                or len(item) != 3
                or not isinstance(item[1], tuple)
                or not item[1]
            ):
                raise DataIntegrityError("scope facts contain an unsupported fact")
            scope = require_text(item[0], "revision_scope.scope")
            authority = require_text(item[2], "revision_scope.authority")
            artifacts = tuple(
                sorted(require_text(value, "revision_scope.artifact") for value in item[1])
            )
            if scope in result or len(set(artifacts)) != len(artifacts):
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY, "revision scopes must be unique"
                )
            cls._authority(authority, "revision_scope_authority", authorities)
            result[scope] = artifacts
        return result

    @classmethod
    def _corrections(
        cls,
        values: tuple[tuple[str, str, CanonicalInstant, str], ...],
        lineage: tuple[str, ...],
        authorities: dict[str, TemporalAuthorityReference],
        knowledge: CanonicalInstant,
    ) -> tuple[tuple[str, str, CanonicalInstant, str], ...]:
        result = []
        for item in values:
            if (
                not isinstance(item, tuple)
                or len(item) != 4
                or not isinstance(item[2], CanonicalInstant)
            ):
                raise DataIntegrityError("correction facts contain an unsupported fact")
            original, corrected, effective, authority = item
            if original == corrected:
                _reject(
                    TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION,
                    "in-place correction is forbidden",
                )
            if original not in lineage or corrected not in lineage:
                _reject(
                    TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION,
                    "correction lineage is inconsistent",
                )
            cls._authority(authority, "correction_authority", authorities)
            if not _same_basis(effective, knowledge):
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "correction temporal basis is incompatible",
                )
            if effective.value > knowledge.value:
                _reject(
                    TemporalDiagnosticCode.FUTURE_LEAKAGE,
                    "correction is not visible at the knowledge boundary",
                )
            result.append(item)
        return tuple(
            sorted(result, key=lambda item: (item[0], item[1], _instant_key(item[2]), item[3]))
        )

    @classmethod
    def _replacements(
        cls,
        values: tuple[tuple[str, str, str, int, CanonicalInstant, str], ...],
        lineage: tuple[str, ...],
        authorities: dict[str, TemporalAuthorityReference],
        scopes: dict[str, tuple[str, ...]],
        knowledge: CanonicalInstant,
    ) -> tuple[tuple[str, str, str, int, CanonicalInstant, str], ...]:
        result = []
        for item in values:
            if (
                not isinstance(item, tuple)
                or len(item) != 6
                or isinstance(item[3], bool)
                or not isinstance(item[3], int)
                or not isinstance(item[4], CanonicalInstant)
            ):
                raise DataIntegrityError("replacement facts contain an unsupported fact")
            original, replacement, scope, _, effective, authority = item
            require_text(scope, "replacement.scope")
            if scope not in scopes or original not in scopes[scope]:
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "replacement scope is unsupported or inapplicable",
                )
            if original == replacement or original not in lineage or replacement not in lineage:
                _reject(
                    TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION,
                    "replacement lineage is inconsistent",
                )
            cls._authority(authority, "replacement_authority", authorities)
            if not _same_basis(effective, knowledge):
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "replacement temporal basis is incompatible",
                )
            if effective.value > knowledge.value:
                _reject(
                    TemporalDiagnosticCode.FUTURE_LEAKAGE,
                    "replacement is not visible at the knowledge boundary",
                )
            result.append(item)
        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    _instant_key(item[4]),
                    item[5],
                ),
            )
        )

    @classmethod
    def _withdrawals(
        cls,
        values: tuple[tuple[str, str, CanonicalInstant, str], ...],
        lineage: tuple[str, ...],
        authorities: dict[str, TemporalAuthorityReference],
        scopes: dict[str, tuple[str, ...]],
        knowledge: CanonicalInstant,
    ) -> tuple[tuple[str, str, CanonicalInstant, str], ...]:
        result = []
        for item in values:
            if (
                not isinstance(item, tuple)
                or len(item) != 4
                or not isinstance(item[2], CanonicalInstant)
            ):
                raise DataIntegrityError("withdrawal facts contain an unsupported fact")
            identity, scope, effective, authority = item
            require_text(scope, "withdrawal.scope")
            if scope not in scopes or identity not in scopes[scope]:
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "withdrawal scope is unsupported or inapplicable",
                )
            if identity not in lineage:
                _reject(
                    TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION,
                    "withdrawal scope is inconsistent",
                )
            cls._authority(authority, "withdrawal_authority", authorities)
            if not _same_basis(effective, knowledge):
                _reject(
                    TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                    "withdrawal temporal basis is incompatible",
                )
            if effective.value > knowledge.value:
                _reject(
                    TemporalDiagnosticCode.FUTURE_LEAKAGE,
                    "withdrawal is not visible at the knowledge boundary",
                )
            result.append(item)
        return tuple(
            sorted(result, key=lambda item: (item[0], item[1], _instant_key(item[2]), item[3]))
        )

    @staticmethod
    def _authority(
        identity: str, role: str, authorities: dict[str, TemporalAuthorityReference]
    ) -> None:
        authority = authorities.get(identity)
        if authority is None or authority.authority_role != role:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY, f"{role} is missing or unauthorized"
            )

    @staticmethod
    def _requirements(values: tuple[tuple[str, bool], ...]) -> dict[str, bool]:
        result: dict[str, bool] = {}
        for item in values:
            if not isinstance(item, tuple) or len(item) != 2 or not isinstance(item[1], bool):
                raise DataIntegrityError("consumer requirements contain an unsupported fact")
            identity = require_text(item[0], "consumer_requirement.identity")
            if identity in result:
                _reject(
                    TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
                    "consumer requirements must be unique",
                )
            result[identity] = item[1]
        if not result:
            raise MissingFieldError("consumer requirements are required")
        return result

    @staticmethod
    def _select_revision(
        lineage: tuple[str, ...],
        corrections: tuple[tuple[str, str, CanonicalInstant, str], ...],
        replacements: tuple[tuple[str, str, str, int, CanonicalInstant, str], ...],
        knowledge: CanonicalInstant,
    ) -> str:
        candidates: list[tuple[int, int, str]] = [(0, -1, lineage[0])]
        candidates.extend(
            (item[2].value, 0, item[1]) for item in corrections if item[2].value <= knowledge.value
        )
        candidates.extend(
            (item[4].value, item[3], item[1])
            for item in replacements
            if item[4].value <= knowledge.value
        )
        candidates.sort(reverse=True)
        best = candidates[0]
        conflicts = {item[2] for item in candidates if item[:2] == best[:2]}
        if len(conflicts) != 1:
            _reject(
                TemporalDiagnosticCode.CONFLICTING_REVISION,
                "competing revisions lack deterministic precedence",
            )
        return best[2]
