"""Persistent declarations and explicitly injected resolved semantic rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import digest, exact, text
from epip.strategy_mapping.profile import StrategySemanticMappingProfile
from epip.strategy_mapping.rule_execution import (
    EXECUTION_SCHEMA_VERSION,
    ExecutableSemanticRule,
    SemanticInvocationKind,
    SemanticResultKind,
    SemanticRuleFamily,
)
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_mapping.rule_requests import (
    ApplicabilityRequest,
    BoundarySelectionRequest,
    CandidateRankingRequest,
    CandidateSelectionRequest,
    ConfidenceRuleRequest,
    DirectionRuleRequest,
    EvidenceMappingRequest,
    EvidenceOrderingRequest,
    MtfAggregationRequest,
    PriceTransformationRequest,
    RankedCandidateSelectionRequest,
    SourceExtractionRequest,
    StructuralApplicabilityRequest,
    TemporalEligibilityRequest,
)
from epip.strategy_mapping.rule_results import (
    ApplicabilityResult,
    BoundaryRuleResult,
    CandidateRuleResult,
    ConfidenceRuleResult,
    DirectionRuleResult,
    EvidenceMappingResult,
    EvidenceOrderingResult,
    MtfAggregationResult,
    PriceTransformationResult,
    RankingRuleResult,
    SelectionRuleResult,
    SemanticRuleResult,
    TemporalEligibilityResult,
)

_COMPATIBILITY = {
    SemanticRuleFamily.SOURCE_EXTRACTION: (
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
    ),
    SemanticRuleFamily.DIRECTION_MAPPING: (
        SemanticInvocationKind.DIRECTION,
        SemanticResultKind.DIRECTION,
    ),
    SemanticRuleFamily.CANDIDATE_SELECTION: (
        SemanticInvocationKind.SELECTION,
        SemanticResultKind.SELECTION,
    ),
    SemanticRuleFamily.CANDIDATE_RANKING: (
        SemanticInvocationKind.RANKING,
        SemanticResultKind.RANKING,
    ),
    SemanticRuleFamily.BOUNDARY_SELECTION: (
        SemanticInvocationKind.BOUNDARY,
        SemanticResultKind.BOUNDARY,
    ),
    SemanticRuleFamily.APPLICABILITY: (
        SemanticInvocationKind.APPLICABILITY,
        SemanticResultKind.APPLICABILITY,
    ),
    SemanticRuleFamily.PRECEDENCE: (SemanticInvocationKind.SELECTION, SemanticResultKind.SELECTION),
    SemanticRuleFamily.PRICE_TRANSFORMATION: (
        SemanticInvocationKind.PRICE_TRANSFORMATION,
        SemanticResultKind.PRICE_TRANSFORMATION,
    ),
    SemanticRuleFamily.CONFIDENCE: (
        SemanticInvocationKind.CONFIDENCE,
        SemanticResultKind.CONFIDENCE,
    ),
    SemanticRuleFamily.TEMPORAL_ELIGIBILITY: (
        SemanticInvocationKind.TEMPORAL_ELIGIBILITY,
        SemanticResultKind.TEMPORAL_ELIGIBILITY,
    ),
    SemanticRuleFamily.EVIDENCE_MAPPING: (
        SemanticInvocationKind.EVIDENCE_MAPPING,
        SemanticResultKind.EVIDENCE_MAPPING,
    ),
    SemanticRuleFamily.EVIDENCE_ORDERING: (
        SemanticInvocationKind.EVIDENCE_ORDERING,
        SemanticResultKind.EVIDENCE_ORDERING,
    ),
    SemanticRuleFamily.MTF_AGGREGATION: (
        SemanticInvocationKind.MTF_AGGREGATION,
        SemanticResultKind.MTF_AGGREGATION,
    ),
}

_STRUCTURAL_APPLICABILITY = (
    SemanticInvocationKind.STRUCTURAL_APPLICABILITY,
    SemanticResultKind.APPLICABILITY,
)

_REQUEST_TYPES: dict[SemanticInvocationKind, tuple[type[object], ...]] = {
    SemanticInvocationKind.SOURCE_EXTRACTION: (SourceExtractionRequest,),
    SemanticInvocationKind.DIRECTION: (DirectionRuleRequest,),
    SemanticInvocationKind.SELECTION: (CandidateSelectionRequest, RankedCandidateSelectionRequest),
    SemanticInvocationKind.RANKING: (CandidateRankingRequest,),
    SemanticInvocationKind.BOUNDARY: (BoundarySelectionRequest,),
    SemanticInvocationKind.APPLICABILITY: (ApplicabilityRequest,),
    SemanticInvocationKind.STRUCTURAL_APPLICABILITY: (StructuralApplicabilityRequest,),
    SemanticInvocationKind.PRICE_TRANSFORMATION: (PriceTransformationRequest,),
    SemanticInvocationKind.CONFIDENCE: (ConfidenceRuleRequest,),
    SemanticInvocationKind.TEMPORAL_ELIGIBILITY: (TemporalEligibilityRequest,),
    SemanticInvocationKind.EVIDENCE_MAPPING: (EvidenceMappingRequest,),
    SemanticInvocationKind.EVIDENCE_ORDERING: (EvidenceOrderingRequest,),
    SemanticInvocationKind.MTF_AGGREGATION: (MtfAggregationRequest,),
}

_RESULT_TYPES: dict[SemanticResultKind, type[object]] = {
    SemanticResultKind.CANDIDATES: CandidateRuleResult,
    SemanticResultKind.DIRECTION: DirectionRuleResult,
    SemanticResultKind.SELECTION: SelectionRuleResult,
    SemanticResultKind.RANKING: RankingRuleResult,
    SemanticResultKind.BOUNDARY: BoundaryRuleResult,
    SemanticResultKind.APPLICABILITY: ApplicabilityResult,
    SemanticResultKind.PRICE_TRANSFORMATION: PriceTransformationResult,
    SemanticResultKind.CONFIDENCE: ConfidenceRuleResult,
    SemanticResultKind.TEMPORAL_ELIGIBILITY: TemporalEligibilityResult,
    SemanticResultKind.EVIDENCE_MAPPING: EvidenceMappingResult,
    SemanticResultKind.EVIDENCE_ORDERING: EvidenceOrderingResult,
    SemanticResultKind.MTF_AGGREGATION: MtfAggregationResult,
}


class SemanticRuleCatalogState(Enum):
    EXECUTABLE = "EXECUTABLE"
    DECLARATION_ONLY = "DECLARATION_ONLY"


@dataclass(frozen=True, slots=True, order=True)
class SemanticRuleDeclaration:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str

    def __post_init__(self) -> None:
        exact(self.identity, RuleIdentity, "identity")
        exact(self.family, SemanticRuleFamily, "family")
        exact(self.invocation_kind, SemanticInvocationKind, "invocation_kind")
        exact(self.result_kind, SemanticResultKind, "result_kind")
        object.__setattr__(
            self, "implementation_id", text(self.implementation_id, "implementation_id")
        )
        compatibility = (self.invocation_kind, self.result_kind)
        if _COMPATIBILITY[self.family] != compatibility and not (
            self.family is SemanticRuleFamily.APPLICABILITY
            and compatibility == _STRUCTURAL_APPLICABILITY
        ):
            raise DataIntegrityError("rule family and invocation/result kinds are incompatible")


@dataclass(frozen=True, slots=True, order=True)
class SemanticRuleCatalogEntry:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    state: SemanticRuleCatalogState
    implementation_id: str | None = None

    def __post_init__(self) -> None:
        exact(self.identity, RuleIdentity, "identity")
        exact(self.family, SemanticRuleFamily, "family")
        exact(self.invocation_kind, SemanticInvocationKind, "invocation_kind")
        exact(self.result_kind, SemanticResultKind, "result_kind")
        exact(self.state, SemanticRuleCatalogState, "state")
        compatibility = (self.invocation_kind, self.result_kind)
        if _COMPATIBILITY[self.family] != compatibility and not (
            self.family is SemanticRuleFamily.APPLICABILITY
            and compatibility == _STRUCTURAL_APPLICABILITY
        ):
            raise DataIntegrityError("rule family and invocation/result kinds are incompatible")
        if self.state is SemanticRuleCatalogState.EXECUTABLE:
            object.__setattr__(
                self,
                "implementation_id",
                text(self.implementation_id, "implementation_id"),
            )
        elif self.implementation_id is not None:
            raise DataIntegrityError("declaration-only rule must not name an implementation")


@dataclass(frozen=True, slots=True)
class SemanticRuleCatalog:
    schema_version: str
    catalog_id: str
    entries: tuple[SemanticRuleCatalogEntry, ...]

    def __post_init__(self) -> None:
        if self.schema_version != EXECUTION_SCHEMA_VERSION:
            raise DataIntegrityError("unsupported execution schema version")
        if (
            type(self.entries) is not tuple
            or not self.entries
            or any(type(item) is not SemanticRuleCatalogEntry for item in self.entries)
        ):
            raise DataIntegrityError("entries must be a non-empty SemanticRuleCatalogEntry tuple")
        ordered = tuple(sorted(self.entries, key=lambda item: item.identity.reference))
        if len({item.identity for item in ordered}) != len(ordered):
            raise DataIntegrityError("catalog identities must be unique")
        object.__setattr__(self, "entries", ordered)
        if self.catalog_id != digest(self, exclude=frozenset({"catalog_id"})):
            raise DataIntegrityError("catalog_id does not match catalog")

    @classmethod
    def create(cls, entries: tuple[SemanticRuleCatalogEntry, ...]) -> SemanticRuleCatalog:
        if (
            type(entries) is not tuple
            or not entries
            or any(type(item) is not SemanticRuleCatalogEntry for item in entries)
        ):
            raise DataIntegrityError("entries must be a non-empty SemanticRuleCatalogEntry tuple")
        ordered = tuple(sorted(entries, key=lambda item: item.identity.reference))
        candidate = object.__new__(cls)
        object.__setattr__(candidate, "schema_version", EXECUTION_SCHEMA_VERSION)
        object.__setattr__(candidate, "catalog_id", "")
        object.__setattr__(candidate, "entries", ordered)
        return cls(
            EXECUTION_SCHEMA_VERSION,
            digest(candidate, exclude=frozenset({"catalog_id"})),
            ordered,
        )

    def executable_manifest(self) -> ResolvedRuleManifest:
        declarations = tuple(
            SemanticRuleDeclaration(
                item.identity,
                item.family,
                item.invocation_kind,
                item.result_kind,
                _executable_implementation_id(item),
            )
            for item in self.entries
            if item.state is SemanticRuleCatalogState.EXECUTABLE
        )
        if not declarations:
            raise DataIntegrityError("catalog has no executable declarations")
        return ResolvedRuleManifest.create(declarations)


def _executable_implementation_id(entry: SemanticRuleCatalogEntry) -> str:
    assert entry.state is SemanticRuleCatalogState.EXECUTABLE
    assert entry.implementation_id is not None
    return entry.implementation_id


@dataclass(frozen=True, slots=True)
class ResolvedRuleManifest:
    schema_version: str
    rule_set_id: str
    declarations: tuple[SemanticRuleDeclaration, ...]

    def __post_init__(self) -> None:
        if self.schema_version != EXECUTION_SCHEMA_VERSION:
            raise DataIntegrityError("unsupported execution schema version")
        if (
            type(self.declarations) is not tuple
            or not self.declarations
            or any(type(x) is not SemanticRuleDeclaration for x in self.declarations)
        ):
            raise DataIntegrityError(
                "declarations must be a non-empty SemanticRuleDeclaration tuple"
            )
        ordered = tuple(sorted(self.declarations, key=lambda x: x.identity.reference))
        if len({x.identity for x in ordered}) != len(ordered):
            raise DataIntegrityError("declaration identities must be unique")
        object.__setattr__(self, "declarations", ordered)
        if self.rule_set_id != digest(self, exclude=frozenset({"rule_set_id"})):
            raise DataIntegrityError("rule_set_id does not match manifest")

    @classmethod
    def create(cls, declarations: tuple[SemanticRuleDeclaration, ...]) -> ResolvedRuleManifest:
        ordered = tuple(sorted(declarations, key=lambda x: x.identity.reference))
        candidate = object.__new__(cls)
        object.__setattr__(candidate, "schema_version", EXECUTION_SCHEMA_VERSION)
        object.__setattr__(candidate, "rule_set_id", "")
        object.__setattr__(candidate, "declarations", ordered)
        return cls(
            EXECUTION_SCHEMA_VERSION, digest(candidate, exclude=frozenset({"rule_set_id"})), ordered
        )


@dataclass(frozen=True, slots=True)
class ResolvedSemanticRuleSet:
    manifest: ResolvedRuleManifest
    implementations: tuple[ExecutableSemanticRule, ...]

    def __post_init__(self) -> None:
        exact(self.manifest, ResolvedRuleManifest, "manifest")
        if type(self.implementations) is not tuple or not self.implementations:
            raise DataIntegrityError("implementations must be a non-empty tuple")
        ordered = tuple(sorted(self.implementations, key=lambda x: x.identity.reference))
        if len(ordered) != len(self.manifest.declarations):
            raise DataIntegrityError("implementations must exactly match manifest declarations")
        if len({x.identity for x in ordered}) != len(ordered):
            raise DataIntegrityError("implementation identities must be unique")
        for declaration, implementation in zip(self.manifest.declarations, ordered, strict=True):
            if (
                type(implementation.identity) is not RuleIdentity
                or declaration.identity != implementation.identity
                or declaration.family is not implementation.family
                or declaration.invocation_kind is not implementation.invocation_kind
                or declaration.result_kind is not implementation.result_kind
                or declaration.implementation_id != implementation.implementation_id
            ):
                raise DataIntegrityError("runtime implementation does not match declaration")
            if not callable(getattr(implementation, "invoke", None)):
                raise DataIntegrityError("runtime implementation has no invoke method")
        object.__setattr__(self, "implementations", ordered)

    def __eq__(self, other: object) -> bool:
        return type(other) is ResolvedSemanticRuleSet and self.manifest == other.manifest

    def __hash__(self) -> int:
        return hash(self.manifest)

    def resolve(self, identity: RuleIdentity) -> ExecutableSemanticRule:
        exact(identity, RuleIdentity, "identity")
        for implementation in self.implementations:
            if implementation.identity == identity:
                return implementation
        raise DataIntegrityError("rule identity is not resolved")

    def invoke(self, identity: RuleIdentity, request: object) -> SemanticRuleResult:
        implementation = self.resolve(identity)
        declaration = next(item for item in self.manifest.declarations if item.identity == identity)
        if type(request) not in _REQUEST_TYPES[declaration.invocation_kind]:
            raise DataIntegrityError("request does not match declared invocation kind")
        result = implementation.invoke(request)  # type: ignore[arg-type]
        if type(result) is not _RESULT_TYPES[declaration.result_kind]:
            raise DataIntegrityError("result does not match declared result kind")
        return result

    def validate_profile_closure(self, profile: StrategySemanticMappingProfile) -> None:
        exact(profile, StrategySemanticMappingProfile, "profile")
        required: list[tuple[RuleIdentity, SemanticRuleFamily]] = []

        def add(identity: RuleIdentity, family: SemanticRuleFamily) -> None:
            required.append((identity, family))

        for policy in profile.direction_policies:
            add(policy.selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
            if policy.strategy_rule is not None:
                add(policy.strategy_rule, SemanticRuleFamily.DIRECTION_MAPPING)
        add(profile.mtf_direction_policy.rule_identity, SemanticRuleFamily.MTF_AGGREGATION)
        for geometry_policy in (profile.entry_policy, profile.stop_policy, profile.target_policy):
            for selector in geometry_policy.allowed_selectors:
                add(selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
            add(geometry_policy.candidate_selector, SemanticRuleFamily.CANDIDATE_SELECTION)
            add(geometry_policy.direction_applicability_rule, SemanticRuleFamily.APPLICABILITY)
        add(profile.entry_policy.ranking_rule, SemanticRuleFamily.CANDIDATE_RANKING)
        add(profile.entry_policy.required_boundary_rule, SemanticRuleFamily.BOUNDARY_SELECTION)
        add(profile.stop_policy.precedence_rule, SemanticRuleFamily.PRECEDENCE)
        add(profile.stop_policy.buffer_rule, SemanticRuleFamily.PRICE_TRANSFORMATION)
        if profile.stop_policy.volatility_adjustment_rule is not None:
            add(
                profile.stop_policy.volatility_adjustment_rule,
                SemanticRuleFamily.PRICE_TRANSFORMATION,
            )
        add(profile.target_policy.ranking_rule, SemanticRuleFamily.CANDIDATE_RANKING)
        if profile.target_policy.threshold_rule is not None:
            add(profile.target_policy.threshold_rule, SemanticRuleFamily.APPLICABILITY)
        if profile.target_policy.extension_rule is not None:
            add(profile.target_policy.extension_rule, SemanticRuleFamily.CANDIDATE_SELECTION)
        for confidence_input in profile.confidence_policy.inputs:
            add(
                confidence_input.source_selector.selector_rule,
                SemanticRuleFamily.SOURCE_EXTRACTION,
            )
        add(profile.confidence_policy.model_identity, SemanticRuleFamily.CONFIDENCE)
        if profile.confidence_policy.calibration_identity is not None:
            add(profile.confidence_policy.calibration_identity, SemanticRuleFamily.CONFIDENCE)
        for evidence_item in profile.evidence_taxonomy.keys:
            add(evidence_item.source_selector.selector_rule, SemanticRuleFamily.SOURCE_EXTRACTION)
            add(evidence_item.mapping_rule, SemanticRuleFamily.EVIDENCE_MAPPING)
            add(
                evidence_item.temporal_eligibility_policy.validity_rule,
                SemanticRuleFamily.TEMPORAL_ELIGIBILITY,
            )
            add(
                evidence_item.temporal_eligibility_policy.revision_rule,
                SemanticRuleFamily.TEMPORAL_ELIGIBILITY,
            )
        add(profile.evidence_taxonomy.ordering_rule, SemanticRuleFamily.EVIDENCE_ORDERING)
        expected: dict[RuleIdentity, SemanticRuleFamily] = {}
        for identity, family in required:
            if identity in expected and expected[identity] is not family:
                raise DataIntegrityError("profile requires one identity with conflicting families")
            expected[identity] = family
        actual = {x.identity: x.family for x in self.manifest.declarations}
        if actual != expected:
            raise DataIntegrityError("resolved manifest does not have exact profile closure")


__all__ = [
    "ResolvedRuleManifest",
    "ResolvedSemanticRuleSet",
    "SemanticRuleCatalog",
    "SemanticRuleCatalogEntry",
    "SemanticRuleCatalogState",
    "SemanticRuleDeclaration",
]
