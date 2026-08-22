"""Deterministic A05-E05 temporal dependency validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar, NoReturn

from epip.core.integrity import DataIntegrityError, require_text
from epip.evidence.graph import DependencyGraph
from epip.governance import GovernanceEpoch
from epip.temporal.availability import AvailabilityDecision
from epip.temporal.completeness import CompletenessOutcome
from epip.temporal.model import (
    CanonicalInstant,
    CanonicalInterval,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.observation import ObservationValidation
from epip.temporal.timeframe import TemporalMappingContract


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable dependency model")

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


def _interval_key(value: CanonicalInterval) -> tuple[object, ...]:
    return (_instant_key(value.start), _instant_key(value.end), value.boundary_convention.value)


def _observation_interval(value: CanonicalInstant | CanonicalInterval) -> CanonicalInterval:
    if isinstance(value, CanonicalInterval):
        return value
    return CanonicalInterval(
        value,
        CanonicalInstant(
            value.value + 1,
            value.precision,
            value.time_scale,
            value.timezone_basis,
            value.authority_identity,
        ),
    )


def _same_basis(left: CanonicalInstant, right: CanonicalInstant) -> bool:
    return (
        left.precision,
        left.time_scale,
        left.timezone_basis,
    ) == (right.precision, right.time_scale, right.timezone_basis)


class TemporalDependencyValidation(_ImmutableRecord):
    """One immutable self-contained E05 dependency-validation outcome."""

    __slots__ = (  # noqa: RUF023 - normative context order
        "dependency_identity",
        "source_node",
        "target_node",
        "source_artifact_identity",
        "target_artifact_identity",
        "source_boundary",
        "consumer_boundary",
        "source_calendar_identity",
        "source_revision_lineage",
        "relationship",
        "mapping_identity",
        "mapping_version",
        "mapping_facts",
        "mapping_authority",
        "source_timeframe_identity",
        "source_timeframe_version",
        "target_timeframe_identity",
        "target_timeframe_version",
        "source_interval",
        "target_interval",
        "source_knowledge_boundary",
        "target_knowledge_boundary",
        "source_completeness_identity",
        "target_completeness_identity",
        "source_complete",
        "target_complete",
        "graph_snapshot_identity",
        "graph_manifest_reference",
        "governance_epoch",
        "graph_nodes",
        "graph_edges",
        "consumer_requirement",
        "compatibility_policy_version",
        "policy_identity",
        "policy_version",
        "valid",
    )
    _field_names = __slots__

    dependency_identity: str
    source_node: str
    target_node: str
    source_artifact_identity: str
    target_artifact_identity: str
    source_boundary: str
    consumer_boundary: str
    source_calendar_identity: str
    source_revision_lineage: tuple[str, ...]
    relationship: str
    mapping_identity: str | None
    mapping_version: str | None
    mapping_facts: tuple[tuple[str, str], ...]
    mapping_authority: tuple[str, str, str, GovernanceEpoch] | None
    source_timeframe_identity: str
    source_timeframe_version: str
    target_timeframe_identity: str
    target_timeframe_version: str
    source_interval: CanonicalInterval
    target_interval: CanonicalInterval
    source_knowledge_boundary: CanonicalInstant
    target_knowledge_boundary: CanonicalInstant
    source_completeness_identity: str
    target_completeness_identity: str
    source_complete: bool
    target_complete: bool
    graph_snapshot_identity: str
    graph_manifest_reference: str
    governance_epoch: GovernanceEpoch
    graph_nodes: tuple[str, ...]
    graph_edges: tuple[tuple[str, str], ...]
    consumer_requirement: tuple[bool, bool, str]
    compatibility_policy_version: str
    policy_identity: str
    policy_version: str
    valid: bool

    def __init__(
        self,
        dependency_identity: str,
        source_node: str,
        target_node: str,
        source_artifact_identity: str,
        target_artifact_identity: str,
        source_boundary: str,
        consumer_boundary: str,
        source_calendar_identity: str,
        source_revision_lineage: tuple[str, ...],
        relationship: str,
        mapping_identity: str | None,
        mapping_version: str | None,
        mapping_facts: tuple[tuple[str, str], ...],
        mapping_authority: tuple[str, str, str, GovernanceEpoch] | None,
        source_timeframe_identity: str,
        source_timeframe_version: str,
        target_timeframe_identity: str,
        target_timeframe_version: str,
        source_interval: CanonicalInterval,
        target_interval: CanonicalInterval,
        source_knowledge_boundary: CanonicalInstant,
        target_knowledge_boundary: CanonicalInstant,
        source_completeness_identity: str,
        target_completeness_identity: str,
        source_complete: bool,
        target_complete: bool,
        graph_snapshot_identity: str,
        graph_manifest_reference: str,
        governance_epoch: GovernanceEpoch,
        graph_nodes: tuple[str, ...],
        graph_edges: tuple[tuple[str, str], ...],
        consumer_requirement: tuple[bool, bool, str],
        compatibility_policy_version: str,
        policy_identity: str,
        policy_version: str,
        valid: bool,
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        for name in (
            "dependency_identity",
            "source_node",
            "target_node",
            "source_artifact_identity",
            "target_artifact_identity",
            "source_boundary",
            "consumer_boundary",
            "source_calendar_identity",
            "relationship",
            "source_timeframe_identity",
            "source_timeframe_version",
            "target_timeframe_identity",
            "target_timeframe_version",
            "source_completeness_identity",
            "target_completeness_identity",
            "graph_snapshot_identity",
            "graph_manifest_reference",
            "compatibility_policy_version",
            "policy_identity",
            "policy_version",
        ):
            require_text(getattr(self, name), f"temporal_dependency.{name}")
        if self.relationship not in {
            "SAME_TIME",
            "HISTORICAL",
            "CROSS_TIME",
            "CROSS_TIMEFRAME",
        }:
            raise DataIntegrityError("temporal dependency relationship is unsupported")
        if not isinstance(self.source_revision_lineage, tuple):
            raise DataIntegrityError("temporal dependency revision lineage must be immutable")
        for identity in self.source_revision_lineage:
            require_text(identity, "temporal_dependency.source_revision_lineage")
        if (self.mapping_identity is None) != (self.mapping_version is None):
            raise DataIntegrityError("temporal dependency mapping identity and version must pair")
        if self.mapping_identity is not None:
            require_text(self.mapping_identity, "temporal_dependency.mapping_identity")
            require_text(self.mapping_version, "temporal_dependency.mapping_version")
        if not isinstance(self.mapping_facts, tuple) or any(
            not isinstance(item, tuple) or len(item) != 2 for item in self.mapping_facts
        ):
            raise DataIntegrityError("temporal dependency mapping facts are invalid")
        for name, value in self.mapping_facts:
            require_text(name, "temporal_dependency.mapping_fact.name")
            require_text(value, "temporal_dependency.mapping_fact.value")
        if (self.mapping_identity is None) != (not self.mapping_facts):
            raise DataIntegrityError("temporal dependency mapping context is incomplete")
        if self.mapping_authority is not None:
            if (
                not isinstance(self.mapping_authority, tuple)
                or len(self.mapping_authority) != 4
                or not isinstance(self.mapping_authority[3], GovernanceEpoch)
            ):
                raise DataIntegrityError("temporal dependency mapping authority is invalid")
            for value in self.mapping_authority[:3]:
                require_text(value, "temporal_dependency.mapping_authority")
        if (self.mapping_identity is None) != (self.mapping_authority is None):
            raise DataIntegrityError("temporal dependency mapping authority context is incomplete")
        for name in ("source_interval", "target_interval"):
            if not isinstance(getattr(self, name), CanonicalInterval):
                raise DataIntegrityError(f"temporal_dependency.{name} is invalid")
        for name in ("source_knowledge_boundary", "target_knowledge_boundary"):
            if not isinstance(getattr(self, name), CanonicalInstant):
                raise DataIntegrityError(f"temporal_dependency.{name} is invalid")
        for name in ("source_complete", "target_complete", "valid"):
            if not isinstance(getattr(self, name), bool):
                raise DataIntegrityError(f"temporal_dependency.{name} must be boolean")
        if not self.valid:
            raise DataIntegrityError("successful dependency validation must be valid")
        if not isinstance(self.governance_epoch, GovernanceEpoch):
            raise DataIntegrityError("temporal dependency governance epoch is invalid")
        if not isinstance(self.graph_nodes, tuple) or any(
            not isinstance(item, str) or not item for item in self.graph_nodes
        ):
            raise DataIntegrityError("temporal dependency graph nodes are invalid")
        if not isinstance(self.graph_edges, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or any(not isinstance(endpoint, str) or not endpoint for endpoint in item)
            for item in self.graph_edges
        ):
            raise DataIntegrityError("temporal dependency graph edges are invalid")
        if (
            not isinstance(self.consumer_requirement, tuple)
            or len(self.consumer_requirement) != 3
            or not isinstance(self.consumer_requirement[0], bool)
            or not isinstance(self.consumer_requirement[1], bool)
        ):
            raise DataIntegrityError("temporal dependency consumer requirement is invalid")
        require_text(self.consumer_requirement[2], "temporal_dependency.knowledge_rule")
        object.__setattr__(self, "graph_nodes", tuple(sorted(self.graph_nodes)))
        object.__setattr__(self, "graph_edges", tuple(sorted(self.graph_edges)))
        object.__setattr__(self, "mapping_facts", tuple(sorted(self.mapping_facts)))
        object.__setattr__(
            self, "source_revision_lineage", tuple(sorted(self.source_revision_lineage))
        )


def _validation_key(value: TemporalDependencyValidation) -> tuple[object, ...]:
    return (
        value.dependency_identity,
        value.source_node,
        value.target_node,
        value.source_artifact_identity,
        value.target_artifact_identity,
        value.source_boundary,
        value.consumer_boundary,
        value.source_calendar_identity,
        value.source_revision_lineage,
        value.relationship,
        value.mapping_identity or "",
        value.mapping_version or "",
        value.mapping_facts,
        (
            (
                value.mapping_authority[0],
                value.mapping_authority[1],
                value.mapping_authority[2],
                value.mapping_authority[3].sequence,
            )
            if value.mapping_authority is not None
            else ()
        ),
        value.source_timeframe_identity,
        value.source_timeframe_version,
        value.target_timeframe_identity,
        value.target_timeframe_version,
        _interval_key(value.source_interval),
        _interval_key(value.target_interval),
        _instant_key(value.source_knowledge_boundary),
        _instant_key(value.target_knowledge_boundary),
        value.source_completeness_identity,
        value.target_completeness_identity,
        value.source_complete,
        value.target_complete,
        value.graph_snapshot_identity,
        value.graph_manifest_reference,
        value.governance_epoch.sequence,
        value.graph_nodes,
        value.graph_edges,
        value.consumer_requirement,
        value.compatibility_policy_version,
        value.policy_identity,
        value.policy_version,
        value.valid,
    )


class TemporalDependencyDiagnostics(_ImmutableRecord):
    """Immutable deterministic E05 outcomes and attributed diagnostics."""

    __slots__ = ("validations", "reasons")  # noqa: RUF023 - semantic field order
    _field_names = __slots__

    validations: tuple[TemporalDependencyValidation, ...]
    reasons: tuple[TemporalDiagnosticReason, ...]

    def __init__(
        self,
        validations: tuple[TemporalDependencyValidation, ...],
        reasons: tuple[TemporalDiagnosticReason, ...] = (),
    ) -> None:
        self._initialize({name: value for name, value in locals().items() if name != "self"})
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.validations, tuple) or any(
            not isinstance(item, TemporalDependencyValidation) for item in self.validations
        ):
            raise DataIntegrityError("dependency diagnostics require immutable validations")
        if not isinstance(self.reasons, tuple) or any(
            not isinstance(item, TemporalDiagnosticReason) for item in self.reasons
        ):
            raise DataIntegrityError("dependency diagnostics require immutable reasons")
        validations = tuple(sorted(self.validations, key=_validation_key))
        if len(set(validations)) != len(validations):
            raise DataIntegrityError("dependency diagnostics contain duplicate validations")
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
                validation
                for validation in validations
                if reason.affected_evidence == validation.dependency_identity
                and reason.source_boundary == validation.source_boundary
                and reason.consumer_boundary == validation.consumer_boundary
                and reason.timeframe_identity == validation.source_timeframe_identity
                and reason.calendar_identity == validation.source_calendar_identity
                and reason.knowledge_boundary == validation.target_knowledge_boundary
                and reason.revision_lineage == validation.source_revision_lineage
                and reason.policy_version == validation.policy_version
            )
            if not matches:
                raise DataIntegrityError("dependency diagnostic reason is orphaned or mismatched")
            if len(matches) != 1:
                raise DataIntegrityError("dependency diagnostic reason binding is ambiguous")
        if len(set(reasons)) != len(reasons):
            raise DataIntegrityError("dependency diagnostics contain duplicate reasons")
        bindings = tuple(
            (
                reason.affected_evidence,
                reason.source_boundary,
                reason.consumer_boundary,
                reason.timeframe_identity,
                reason.calendar_identity,
                reason.knowledge_boundary,
                reason.revision_lineage,
                reason.policy_version,
            )
            for reason in reasons
        )
        if len(set(bindings)) != len(bindings):
            raise DataIntegrityError(
                "dependency diagnostics contain duplicate inconsistent bindings"
            )
        object.__setattr__(self, "validations", validations)
        object.__setattr__(self, "reasons", reasons)


class TemporalDependencyValidator:
    """Validate temporal relationships over one frozen A04 dependency graph."""

    __slots__ = ()

    @staticmethod
    def _require_graph(graph: DependencyGraph) -> None:
        if not isinstance(graph, DependencyGraph):
            raise DataIntegrityError("dependency graph must be a frozen A04 graph")
        if (
            not graph.nodes
            or graph.nodes != graph.diagnostics.graph_nodes
            or graph.edges != graph.diagnostics.graph_edges
            or graph.snapshot_identity != graph.diagnostics.snapshot_identity
            or graph.manifest_reference != graph.diagnostics.manifest_reference
            or graph.governance_epoch != graph.diagnostics.governance_epoch
        ):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "A04 dependency graph context is incomplete or inconsistent",
            )

    @staticmethod
    def _require_tuple(value: object, name: str) -> tuple[object, ...]:
        if not isinstance(value, tuple):
            raise DataIntegrityError(f"{name} must be an immutable tuple")
        return value

    @classmethod
    def validate(
        cls,
        graph: DependencyGraph,
        mappings: tuple[TemporalMappingContract, ...],
        availability: tuple[AvailabilityDecision, ...],
        observations: tuple[ObservationValidation, ...],
        completeness: tuple[CompletenessOutcome, ...],
        dependency_facts: tuple[tuple[str, str, str, str, str, str, str | None], ...],
        consumer_requirements: tuple[tuple[str, bool, bool, str], ...],
        compatibility_facts: tuple[tuple[str, bool, str], ...],
        policy_identity: str,
        policy_version: str,
    ) -> TemporalDependencyDiagnostics:
        """Validate all declared temporal dependency facts without changing topology."""

        cls._require_graph(graph)
        policy_id = require_text(policy_identity, "dependency.policy_identity")
        policy = require_text(policy_version, "dependency.policy_version")
        cls._require_tuple(mappings, "mapping contracts")
        cls._require_tuple(availability, "availability outcomes")
        cls._require_tuple(observations, "observation outcomes")
        cls._require_tuple(completeness, "completeness outcomes")
        cls._require_tuple(dependency_facts, "dependency facts")
        cls._require_tuple(consumer_requirements, "consumer requirements")
        cls._require_tuple(compatibility_facts, "compatibility facts")
        if any(not isinstance(item, TemporalMappingContract) for item in mappings):
            raise DataIntegrityError("mapping contracts contain an unsupported fact")
        if any(not isinstance(item, AvailabilityDecision) for item in availability):
            raise DataIntegrityError("availability outcomes contain an unsupported fact")
        if any(not isinstance(item, ObservationValidation) for item in observations):
            raise DataIntegrityError("observation outcomes contain an unsupported fact")
        if any(not isinstance(item, CompletenessOutcome) for item in completeness):
            raise DataIntegrityError("completeness outcomes contain an unsupported fact")
        facts = cls._dependency_facts(dependency_facts)
        requirements = cls._requirements(consumer_requirements)
        compatibility = cls._compatibility(compatibility_facts)
        fact_edges = tuple(sorted((item[1], item[2]) for item in facts))
        if fact_edges != tuple(sorted(graph.edges)):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "temporal dependency facts must preserve the complete A04 topology",
            )
        ids = tuple(item[0] for item in facts)
        if set(ids) != set(requirements) or set(ids) != set(compatibility):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "every dependency requires consumer and compatibility facts",
            )
        validations = tuple(
            cls._validate_fact(
                graph,
                fact,
                mappings,
                availability,
                observations,
                completeness,
                requirements[fact[0]],
                compatibility[fact[0]],
                policy_id,
                policy,
            )
            for fact in facts
        )
        return TemporalDependencyDiagnostics(validations)

    @staticmethod
    def _dependency_facts(
        value: tuple[tuple[str, str, str, str, str, str, str | None], ...],
    ) -> tuple[tuple[str, str, str, str, str, str, str | None], ...]:
        result: list[tuple[str, str, str, str, str, str, str | None]] = []
        for item in value:
            if not isinstance(item, tuple) or len(item) != 7:
                raise DataIntegrityError("dependency facts contain an unsupported fact")
            for field in item[:6]:
                require_text(field, "dependency_fact")
            if item[6] is not None:
                require_text(item[6], "dependency_fact.mapping_identity")
            result.append(item)
        result.sort()
        if len({item[0] for item in result}) != len(result):
            _reject(
                TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
                "dependency identities must be unique",
            )
        return tuple(result)

    @staticmethod
    def _requirements(
        value: tuple[tuple[str, bool, bool, str], ...],
    ) -> dict[str, tuple[bool, bool, str]]:
        result: dict[str, tuple[bool, bool, str]] = {}
        for item in value:
            if (
                not isinstance(item, tuple)
                or len(item) != 4
                or not isinstance(item[1], bool)
                or not isinstance(item[2], bool)
            ):
                raise DataIntegrityError("consumer requirements contain an unsupported fact")
            identity = require_text(item[0], "consumer_requirement.dependency_identity")
            rule = require_text(item[3], "consumer_requirement.knowledge_rule")
            if rule not in {"SOURCE_NOT_AFTER_TARGET", "SAME_KNOWLEDGE_BOUNDARY"}:
                _reject(
                    TemporalDiagnosticCode.FUTURE_LEAKAGE,
                    "consumer knowledge-boundary rule is unsupported",
                )
            if identity in result:
                _reject(
                    TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
                    "consumer requirement identities must be unique",
                )
            result[identity] = (item[1], item[2], rule)
        return result

    @staticmethod
    def _compatibility(
        value: tuple[tuple[str, bool, str], ...],
    ) -> dict[str, tuple[bool, str]]:
        result: dict[str, tuple[bool, str]] = {}
        for item in value:
            if not isinstance(item, tuple) or len(item) != 3 or not isinstance(item[1], bool):
                raise DataIntegrityError("compatibility facts contain an unsupported fact")
            identity = require_text(item[0], "compatibility.dependency_identity")
            version = require_text(item[2], "compatibility.policy_version")
            if identity in result:
                _reject(
                    TemporalDiagnosticCode.DUPLICATE_TEMPORAL_ARTIFACT,
                    "compatibility fact identities must be unique",
                )
            result[identity] = (item[1], version)
        return result

    @classmethod
    def _validate_fact(
        cls,
        graph: DependencyGraph,
        fact: tuple[str, str, str, str, str, str, str | None],
        mappings: tuple[TemporalMappingContract, ...],
        availability: tuple[AvailabilityDecision, ...],
        observations: tuple[ObservationValidation, ...],
        completeness: tuple[CompletenessOutcome, ...],
        requirement: tuple[bool, bool, str],
        compatibility: tuple[bool, str],
        policy_identity: str,
        policy_version: str,
    ) -> TemporalDependencyValidation:
        identity, source_node, target_node, source_id, target_id, relationship, mapping_id = fact
        if source_node not in graph.nodes or target_node not in graph.nodes:
            _reject(TemporalDiagnosticCode.HISTORICAL_AMBIGUITY, "dependency endpoint is absent")
        source = cls._one_observation(source_id, observations)
        target = cls._one_observation(target_id, observations)
        source_availability = cls._one_availability(source_id, availability)
        target_availability = cls._one_availability(target_id, availability)
        source_complete = cls._one_completeness(source_id, completeness)
        target_complete = cls._one_completeness(target_id, completeness)
        cls._bind_predecessors(source, source_availability, source_complete)
        cls._bind_predecessors(target, target_availability, target_complete)
        source_interval = _observation_interval(source.observation)
        target_interval = _observation_interval(target.observation)
        if not _same_basis(source_interval.start, target_interval.start):
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "dependency observations do not share a canonical temporal basis",
            )
        cls._validate_relationship(relationship, source, target, source_interval, target_interval)
        mapping = cls._validate_mapping(
            relationship,
            mapping_id,
            source,
            target,
            source_interval,
            target_interval,
            mappings,
        )
        cls._validate_mapping_requirements(mapping, source, target, target_complete)
        cls._validate_requirements(requirement, source, target, source_complete, target_complete)
        if not compatibility[0]:
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "authoritative compatibility fact rejects the dependency",
            )
        return TemporalDependencyValidation(
            identity,
            source_node,
            target_node,
            source_id,
            target_id,
            source.boundary_identity,
            target.boundary_identity,
            source.calendar_identity or "",
            source.revision_lineage,
            relationship,
            mapping.mapping_identity if mapping is not None else None,
            mapping.mapping_version if mapping is not None else None,
            cls._mapping_facts(mapping),
            (
                (
                    mapping.authority.authority_role,
                    mapping.authority.authority_identity,
                    mapping.authority.authority_version,
                    mapping.authority.governance_epoch,
                )
                if mapping is not None
                else None
            ),
            source.timeframe_identity or "",
            source.timeframe_version or "",
            target.timeframe_identity or "",
            target.timeframe_version or "",
            source_interval,
            target_interval,
            source.knowledge_boundary,
            target.knowledge_boundary,
            source_complete.outcome_identity,
            target_complete.outcome_identity,
            source_complete.complete,
            target_complete.complete,
            graph.snapshot_identity,
            graph.manifest_reference,
            graph.governance_epoch,
            graph.nodes,
            graph.edges,
            requirement,
            compatibility[1],
            policy_identity,
            policy_version,
            True,
        )

    @staticmethod
    def _mapping_facts(
        mapping: TemporalMappingContract | None,
    ) -> tuple[tuple[str, str], ...]:
        if mapping is None:
            return ()
        return tuple(
            sorted(
                (
                    ("mapping_identity", mapping.mapping_identity),
                    ("mapping_version", mapping.mapping_version),
                    ("source_timeframe_identity", mapping.source_timeframe_identity),
                    ("source_timeframe_version", mapping.source_timeframe_version),
                    ("target_timeframe_identity", mapping.target_timeframe_identity),
                    ("target_timeframe_version", mapping.target_timeframe_version),
                    ("alignment_rule", mapping.alignment_rule),
                    ("membership_rule", mapping.membership_rule),
                    ("closure_requirement", mapping.closure_requirement),
                    ("completeness_requirement", mapping.completeness_requirement),
                    ("visibility_rule", mapping.visibility_rule),
                    ("revision_propagation_rule", mapping.revision_propagation_rule),
                    ("conflict_rule", mapping.conflict_rule),
                    ("policy_version", mapping.policy_version),
                )
            )
        )

    @staticmethod
    def _one_observation(
        identity: str, values: tuple[ObservationValidation, ...]
    ) -> ObservationValidation:
        matches = tuple(item for item in values if item.artifact_identity == identity)
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.MISSING_OBSERVATION_TIME,
                "dependency observation is missing or ambiguous",
            )
        return matches[0]

    @staticmethod
    def _one_availability(
        identity: str, values: tuple[AvailabilityDecision, ...]
    ) -> AvailabilityDecision:
        matches = tuple(item for item in values if item.artifact_identity == identity)
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "dependency availability is missing or ambiguous",
            )
        return matches[0]

    @staticmethod
    def _one_completeness(
        identity: str, values: tuple[CompletenessOutcome, ...]
    ) -> CompletenessOutcome:
        matches = tuple(item for item in values if identity in item.artifact_identities)
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "dependency completeness is missing or ambiguous",
            )
        return matches[0]

    @staticmethod
    def _bind_predecessors(
        observation: ObservationValidation,
        availability: AvailabilityDecision,
        completeness: CompletenessOutcome,
    ) -> None:
        if (
            observation.boundary_identity != availability.boundary_identity
            or observation.consumer_temporal_boundary != availability.use_identity
            or observation.knowledge_boundary != availability.knowledge_boundary
            or observation.revision_lineage != availability.revision_lineage
            or observation.artifact_identity not in completeness.artifact_identities
            or observation.knowledge_boundary not in completeness.knowledge_boundaries
            or observation.revision_lineage not in completeness.revision_lineages
        ):
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY, "predecessor context is inconsistent"
            )
        if not availability.visible or not availability.provisionally_temporally_eligible:
            _reject(
                TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
                "dependency artifact is not temporally eligible",
            )

    @staticmethod
    def _validate_relationship(
        relationship: str,
        source: ObservationValidation,
        target: ObservationValidation,
        source_interval: CanonicalInterval,
        target_interval: CanonicalInterval,
    ) -> None:
        same_timeframe = (
            source.timeframe_identity,
            source.timeframe_version,
        ) == (target.timeframe_identity, target.timeframe_version)
        if relationship == "SAME_TIME":
            if not same_timeframe or source_interval != target_interval:
                _reject(
                    TemporalDiagnosticCode.CROSS_TIMEFRAME_CONFLICT,
                    "same-time dependency is inconsistent",
                )
            return
        if relationship in {"HISTORICAL", "CROSS_TIME"}:
            if not same_timeframe:
                _reject(
                    TemporalDiagnosticCode.HIDDEN_TIMEFRAME_CONVERSION,
                    "same-timeframe dependency hides conversion",
                )
            if relationship == "CROSS_TIME" and source_interval == target_interval:
                _reject(
                    TemporalDiagnosticCode.CROSS_TIMEFRAME_CONFLICT,
                    "cross-time dependency is not cross-time",
                )
            if source_interval.end.value > target_interval.start.value:
                _reject(
                    TemporalDiagnosticCode.FUTURE_DEPENDENCY, "dependency points into the future"
                )
            return
        if relationship != "CROSS_TIMEFRAME":
            raise DataIntegrityError("dependency relationship is unsupported")
        if same_timeframe:
            _reject(
                TemporalDiagnosticCode.HIDDEN_AGGREGATION,
                "cross-timeframe dependency hides aggregation or inheritance",
            )

    @staticmethod
    def _validate_mapping(
        relationship: str,
        mapping_identity: str | None,
        source: ObservationValidation,
        target: ObservationValidation,
        source_interval: CanonicalInterval,
        target_interval: CanonicalInterval,
        mappings: tuple[TemporalMappingContract, ...],
    ) -> TemporalMappingContract | None:
        if relationship != "CROSS_TIMEFRAME":
            if mapping_identity is not None:
                _reject(
                    TemporalDiagnosticCode.HIDDEN_TIMEFRAME_CONVERSION, "unexpected mapping fact"
                )
            return None
        matches = tuple(
            item
            for item in mappings
            if item.mapping_identity == mapping_identity
            and item.source_timeframe_identity == source.timeframe_identity
            and item.source_timeframe_version == source.timeframe_version
            and item.target_timeframe_identity == target.timeframe_identity
            and item.target_timeframe_version == target.timeframe_version
        )
        if len(matches) != 1:
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "required mapping fact is missing or unsupported",
            )
        mapping = matches[0]
        if "INHERIT" in mapping.revision_propagation_rule.upper():
            _reject(
                TemporalDiagnosticCode.HIDDEN_INHERITANCE,
                "mapping contract attempts hidden temporal inheritance",
            )
        supported = (
            mapping.alignment_rule == "SOURCE_START_ALIGNED_TO_TARGET"
            and mapping.membership_rule == "SOURCE_INTERVAL_INCLUDED_BY_TARGET"
            and mapping.closure_requirement == "TARGET_CLOSED"
            and mapping.completeness_requirement == "ALL_DECLARED_MEMBERS_PRESENT"
            and mapping.visibility_rule == "KNOWLEDGE_BOUNDARY_ADMITTED"
            and mapping.revision_propagation_rule == "NEW_PLAN_REQUIRED"
            and mapping.conflict_rule == "FAIL_CLOSED"
        )
        if not supported:
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "mapping rules are unsupported",
            )
        if (
            source_interval.start.value != target_interval.start.value
            or source_interval.start.value < target_interval.start.value
            or source_interval.end.value > target_interval.end.value
        ):
            _reject(
                TemporalDiagnosticCode.CROSS_TIMEFRAME_INCOMPATIBILITY,
                "mapping alignment or interval membership is invalid",
            )
        return mapping

    @staticmethod
    def _validate_mapping_requirements(
        mapping: TemporalMappingContract | None,
        source: ObservationValidation,
        target: ObservationValidation,
        target_completeness: CompletenessOutcome,
    ) -> None:
        if mapping is None:
            return
        if mapping.closure_requirement == "TARGET_CLOSED" and (
            target.provisional or target.closure_state not in {"POINT", "CLOSED", "FINAL"}
        ):
            _reject(
                TemporalDiagnosticCode.PROVISIONAL_AS_FINAL,
                "mapping contract requires final target closure",
            )
        if (
            mapping.completeness_requirement == "ALL_DECLARED_MEMBERS_PRESENT"
            and not target_completeness.complete
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW,
                "mapping contract requires complete target membership",
            )

    @staticmethod
    def _validate_requirements(
        requirement: tuple[bool, bool, str],
        source: ObservationValidation,
        target: ObservationValidation,
        source_completeness: CompletenessOutcome,
        target_completeness: CompletenessOutcome,
    ) -> None:
        require_closure, require_complete, knowledge_rule = requirement
        if require_closure and (source.provisional or target.provisional):
            _reject(
                TemporalDiagnosticCode.PROVISIONAL_AS_FINAL, "dependency requires final closure"
            )
        if require_complete and (
            not source_completeness.complete or not target_completeness.complete
        ):
            _reject(
                TemporalDiagnosticCode.INCOMPLETE_WINDOW, "dependency requires complete windows"
            )
        if source.knowledge_boundary.value > target.knowledge_boundary.value:
            _reject(
                TemporalDiagnosticCode.FUTURE_LEAKAGE, "source exceeds consumer knowledge boundary"
            )
        if (
            knowledge_rule == "SAME_KNOWLEDGE_BOUNDARY"
            and source.knowledge_boundary != target.knowledge_boundary
        ):
            _reject(TemporalDiagnosticCode.FUTURE_LEAKAGE, "knowledge boundaries must be equal")
