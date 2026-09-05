"""Generic deterministic P02 analysis-to-A07 fact adapter."""

from __future__ import annotations

from typing import NamedTuple

from epip.a07.direction import DirectionalFacts
from epip.a07.entry import EntryFacts
from epip.a07.evidence import StrategyEvidenceSnapshot
from epip.a07.foundation import StrategyDirection, StrategyEvidenceIdentity
from epip.a07.policy import StrategyPolicy
from epip.a07.stop import StopFacts
from epip.a07.target import TargetFacts
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._confidence_cardinality import _reduce_confidence_policy
from epip.strategy_mapping._evidence_freshness import _resolve_evidence_freshness
from epip.strategy_mapping.confidence_policy import ModelParameter
from epip.strategy_mapping.direction_policy import (
    DirectionFactName,
    DirectionFactPolicy,
    SourceSelector,
    SourceSelectorKind,
)
from epip.strategy_mapping.evidence_identity import (
    derive_evidence_item_identity,
    derive_evidence_set_identity,
)
from epip.strategy_mapping.evidence_policy import EvidenceRequirement
from epip.strategy_mapping.geometry_policy import (
    EntrySourcePolicy,
    StopSourcePolicy,
    TargetSourcePolicy,
)
from epip.strategy_mapping.invocation_binding import AdapterInvocationBinding
from epip.strategy_mapping.mtf_bundle import MultiTimeframeAnalyticalBundle
from epip.strategy_mapping.profile import StrategySemanticMappingProfile
from epip.strategy_mapping.resolved_rules import ResolvedSemanticRuleSet
from epip.strategy_mapping.rule_execution import (
    SemanticRuleDiagnosticCode,
    SemanticRuleState,
    SemanticValueKind,
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
    SemanticRuleInvocationContext,
    SourceExtractionRequest,
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
    TemporalEligibilityResult,
)
from epip.strategy_mapping.rule_values import (
    ConfidenceInputValue,
    SemanticCandidate,
    TimeframeDirectionValue,
)
from epip.strategy_mapping.source_binding import AnalyticalSourceBinding
from epip.strategy_mapping.source_resolution import resolve_source_bindings
from epip.strategy_mapping.transitions import (
    boundary_entry_range,
    materialize_evidence_order,
    selection_winner,
)
from epip.strategy_runtime._base import CONTRACT_VERSION, digest
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.facts import AnalyticalInputBundle, StrategyFactBundle
from epip.strategy_runtime.mtf import TimeframeRole
from epip.strategy_runtime.profile import StrategyProfile
from epip.strategy_runtime.protocols import FactAdapterResult, FactAdapterState
from epip.strategy_runtime.provenance import FactAdapterIdentity
from epip.strategy_runtime.result import (
    DiagnosticSeverity,
    RuntimeDiagnostic,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
)


class _Terminal(Exception):
    def __init__(self, state: FactAdapterState, diagnostics: tuple[RuntimeDiagnostic, ...]) -> None:
        super().__init__(state.value)
        self.state = state
        self.diagnostics = diagnostics


class _EvidenceRecord(NamedTuple):
    key: str
    candidates: tuple[SemanticCandidate, ...]
    identity: StrategyEvidenceIdentity
    source_ids: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    fresh: bool
    eligible: bool


def _diagnostic(
    code: RuntimeDiagnosticCode,
    subject: str,
    message: str,
    *,
    stage: RuntimeDiagnosticStage = RuntimeDiagnosticStage.ADAPTER,
    source_refs: tuple[str, ...] = (),
) -> RuntimeDiagnostic:
    return RuntimeDiagnostic(code, stage, DiagnosticSeverity.ERROR, subject, source_refs, message)


def _terminal_for_rule(
    identity: RuleIdentity, state: SemanticRuleState, codes: tuple[SemanticRuleDiagnosticCode, ...]
) -> _Terminal:
    mapping = {
        SemanticRuleState.NO_MATCH: (
            FactAdapterState.REJECTED,
            RuntimeDiagnosticCode.MISSING_FACT,
        ),
        SemanticRuleState.REJECTED: (
            FactAdapterState.REJECTED,
            RuntimeDiagnosticCode.ADAPTER_REJECTED,
        ),
        SemanticRuleState.INVALID_INPUT: (
            FactAdapterState.INVALID_INPUT,
            RuntimeDiagnosticCode.INVALID_REQUEST,
        ),
        SemanticRuleState.FAILED: (
            FactAdapterState.FAILED,
            RuntimeDiagnosticCode.ADAPTER_FAILED,
        ),
    }
    adapter_state, runtime_code = mapping[state]
    messages = tuple(item.value for item in codes) or (state.value,)
    return _Terminal(
        adapter_state,
        tuple(_diagnostic(runtime_code, identity.reference, item) for item in messages),
    )


class CanonicalFactAdapter:
    """Immutable evaluation-scoped implementation of the frozen P01 adapter protocol."""

    __slots__ = ("_binding", "_identity", "_profile", "_rules", "_typed_bundle")

    def __init__(
        self,
        identity: FactAdapterIdentity,
        semantic_profile: StrategySemanticMappingProfile,
        resolved_rules: ResolvedSemanticRuleSet,
        typed_bundle: MultiTimeframeAnalyticalBundle,
        invocation_binding: AdapterInvocationBinding,
    ) -> None:
        if (
            type(identity) is not FactAdapterIdentity
            or type(semantic_profile) is not StrategySemanticMappingProfile
            or type(resolved_rules) is not ResolvedSemanticRuleSet
            or type(typed_bundle) is not MultiTimeframeAnalyticalBundle
            or type(invocation_binding) is not AdapterInvocationBinding
        ):
            raise DataIntegrityError("canonical adapter dependencies have invalid types")
        self._identity = identity
        self._profile = semantic_profile
        self._rules = resolved_rules
        self._typed_bundle = typed_bundle
        self._binding = invocation_binding

    @property
    def identity(self) -> FactAdapterIdentity:
        return self._identity

    def adapt(
        self,
        context: EvaluationContext,
        inputs: AnalyticalInputBundle,
        profile: StrategyProfile,
        policy: StrategyPolicy,
    ) -> FactAdapterResult:
        diagnostics: list[RuntimeDiagnostic] = []
        try:
            self._validate_structure(context, inputs, profile, policy)
            directions, final_direction = self._direction(context)
            entry = self._entry(context, final_direction)
            stop = self._stop(context, final_direction)
            target = self._target(context, final_direction)
            confidence, confidence_diagnostics = self._confidence(context)
            diagnostics.extend(confidence_diagnostics)
            evidence, evidence_identity, evidence_diagnostics = self._evidence(context, policy)
            diagnostics.extend(evidence_diagnostics)
            bundle = StrategyFactBundle.create(
                evaluation_id=context.evaluation_id,
                strategy_identity=profile.strategy_identity,
                policy_reference=policy.identity.reference,
                profile_identity=profile.identity,
                evidence_identity=evidence_identity,
                evidence=evidence,
                directional_facts=directions,
                entry_facts=entry,
                stop_facts=stop,
                target_facts=target,
                confidence=confidence,
                mtf_context_id=inputs.mtf_context.context_id,
                provenance=inputs.provenance,
            )
            return FactAdapterResult(FactAdapterState.ACCEPTED, bundle, tuple(diagnostics))
        except _Terminal as terminal:
            diagnostics.extend(terminal.diagnostics)
            return FactAdapterResult(terminal.state, None, tuple(diagnostics))
        except DataIntegrityError:
            diagnostics.append(
                _diagnostic(
                    RuntimeDiagnosticCode.INVALID_REQUEST,
                    self._binding.binding_id,
                    SemanticRuleDiagnosticCode.RULE_OUTPUT_INVALID.value,
                )
            )
            return FactAdapterResult(FactAdapterState.INVALID_INPUT, None, tuple(diagnostics))
        except Exception:  # noqa: BLE001 - frozen boundary sanitizes implementation failures
            diagnostics.append(
                _diagnostic(
                    RuntimeDiagnosticCode.ADAPTER_FAILED,
                    self._identity.adapter_id,
                    "FAILED",
                )
            )
            return FactAdapterResult(FactAdapterState.FAILED, None, tuple(diagnostics))

    def _validate_structure(
        self,
        context: object,
        inputs: object,
        profile: object,
        policy: object,
    ) -> None:
        if (
            type(context) is not EvaluationContext
            or type(inputs) is not AnalyticalInputBundle
            or type(profile) is not StrategyProfile
            or type(policy) is not StrategyPolicy
        ):
            raise DataIntegrityError("P01 invocation types are invalid")
        assert isinstance(context, EvaluationContext)
        assert isinstance(inputs, AnalyticalInputBundle)
        assert isinstance(profile, StrategyProfile)
        assert isinstance(policy, StrategyPolicy)
        binding = self._binding
        if (
            binding.adapter_identity != self._identity
            or binding.semantic_profile_identity != self._profile.identity
            or binding.resolved_rule_set_id != self._rules.manifest.rule_set_id
            or binding.typed_bundle_id != self._typed_bundle.bundle_id
            or binding.analytical_input_digest != digest(inputs)
            or binding.provenance_manifest_id != inputs.provenance.manifest_id
            or binding.instrument_binding_id != self._typed_bundle.instrument.binding_id
            or context.profile_identity != profile.identity
            or profile != self._profile.parent_profile
            or policy.strategy_identity != profile.strategy_identity
            or inputs.provenance.adapter_identity != self._identity
            or inputs.provenance.profile_identity != profile.identity
            or inputs.provenance.evaluation_id != context.evaluation_id
            or inputs.mtf_context != self._typed_bundle.coherence
            or policy.required_evidence != profile.required_evidence_keys
            or policy.optional_evidence != profile.optional_evidence_keys
            or self._identity.contract_version not in profile.compatible_adapter_contract_versions
            or CONTRACT_VERSION not in profile.compatible_runtime_contract_versions
        ):
            raise DataIntegrityError("invocation binding mismatch")
        self._typed_bundle.validate_for(context, inputs.provenance)
        self._rules.validate_profile_closure(self._profile)
        primary = next(
            (
                item
                for item in self._typed_bundle.frames
                if item.frame.role is TimeframeRole.PRIMARY
            ),
            None,
        )
        if primary is None:
            raise DataIntegrityError("primary frame is absent")
        payloads = {
            "SWING": inputs.swing,
            "MARKET_STRUCTURE": inputs.structure,
            "LIQUIDITY": inputs.liquidity,
            "FIBONACCI": inputs.fibonacci,
            "MARKET_CONTEXT": inputs.context,
            "ELLIOTT": inputs.elliott,
            "DECISION": inputs.decision,
            "KERNEL": inputs.kernel_result,
        }
        typed = {item.source_kind.value: item.payload for item in primary.sources}
        if any(value != typed.get(name) for name, value in payloads.items() if value is not None):
            raise DataIntegrityError("P01 primary payload differs from typed source")
        if any(payloads.get(name) is None for name in typed):
            raise DataIntegrityError("typed primary payload is omitted from P01 inputs")
        selectors = [item.selector for item in self._profile.direction_policies]
        for geometry in (
            self._profile.entry_policy,
            self._profile.stop_policy,
            self._profile.target_policy,
        ):
            selectors.extend(geometry.allowed_selectors)
        selectors.extend(item.source_selector for item in self._profile.confidence_policy.inputs)
        selectors.extend(item.source_selector for item in self._profile.evidence_taxonomy.keys)
        for selector in selectors:
            resolve_source_bindings(selector, self._typed_bundle)

    def _context(
        self,
        evaluation: EvaluationContext,
        identity: RuleIdentity,
        sources: tuple[AnalyticalSourceBinding, ...],
        *,
        frame_role: TimeframeRole | None = None,
        timeframe: str | None = None,
        candidates: tuple[SemanticCandidate, ...] = (),
    ) -> SemanticRuleInvocationContext:
        source_ids = tuple(item.source_binding_id for item in sources) or tuple(
            item.source_binding_id for item in candidates
        )
        refs = tuple(item.provenance_ref for item in sources) or tuple(
            item.provenance_ref for item in candidates
        )
        return SemanticRuleInvocationContext(
            evaluation.evaluation_id,
            evaluation.evaluation_timestamp,
            self._profile.identity,
            identity,
            self._typed_bundle.instrument.binding_id,
            timeframe,
            frame_role,
            source_ids,
            refs,
        )

    def _invoke(self, identity: RuleIdentity, request: object, expected: type[object]) -> object:
        try:
            result = self._rules.resolve(identity).invoke(request)  # type: ignore[arg-type]
        except DataIntegrityError:
            raise
        except Exception as exc:
            raise _Terminal(
                FactAdapterState.FAILED,
                (
                    _diagnostic(
                        RuntimeDiagnosticCode.ADAPTER_FAILED,
                        identity.reference,
                        "FAILED",
                    ),
                ),
            ) from exc
        if type(result) is not expected:
            raise DataIntegrityError("rule returned the wrong result contract")
        state = result.state
        if state is not SemanticRuleState.SUCCESS:
            raise _terminal_for_rule(identity, state, result.diagnostic_codes)
        return result

    def _extract(
        self,
        evaluation: EvaluationContext,
        selector: SourceSelector,
        *,
        active_role: TimeframeRole | None = None,
    ) -> tuple[tuple[SemanticCandidate, ...], tuple[AnalyticalSourceBinding, ...]]:
        sources = resolve_source_bindings(selector, self._typed_bundle, active_role=active_role)
        if not sources:
            raise _terminal_for_rule(selector.selector_rule, SemanticRuleState.NO_MATCH, ())
        candidates: list[SemanticCandidate] = []
        no_match = True
        for source in sources:
            request = SourceExtractionRequest(
                self._context(
                    evaluation,
                    selector.selector_rule,
                    (source,),
                    frame_role=active_role,
                    timeframe=source.timeframe if active_role is not None else None,
                ),
                source,
            )
            try:
                result = self._invoke(selector.selector_rule, request, CandidateRuleResult)
            except _Terminal as terminal:
                if terminal.state is FactAdapterState.REJECTED and all(
                    item.code is RuntimeDiagnosticCode.MISSING_FACT for item in terminal.diagnostics
                ):
                    continue
                raise
            assert isinstance(result, CandidateRuleResult) and result.candidates is not None
            no_match = False
            for candidate in result.candidates:
                if (
                    candidate.source_binding_id != source.source_binding_id
                    or candidate.provenance_ref != source.provenance_ref
                    or candidate.instrument_binding_id != source.instrument.binding_id
                    or candidate.timeframe != source.timeframe
                    or candidate.source_rule_identity != selector.selector_rule
                ):
                    raise DataIntegrityError("candidate lineage is invalid")
                candidates.append(candidate)
        if no_match:
            raise _terminal_for_rule(selector.selector_rule, SemanticRuleState.NO_MATCH, ())
        ordered = tuple(sorted(candidates, key=lambda item: item.candidate_id))
        if len({item.candidate_id for item in ordered}) != len(ordered):
            raise DataIntegrityError("duplicate candidate identity")
        return ordered, sources

    def _direction_policy(
        self,
        evaluation: EvaluationContext,
        policy: DirectionFactPolicy,
        role: TimeframeRole | None = None,
    ) -> tuple[
        StrategyDirection, tuple[SemanticCandidate, ...], tuple[AnalyticalSourceBinding, ...]
    ]:
        candidates, sources = self._extract(evaluation, policy.selector, active_role=role)
        if not candidates:
            raise _terminal_for_rule(policy.selector.selector_rule, SemanticRuleState.NO_MATCH, ())
        if policy.selector.selector_kind is SourceSelectorKind.DIRECT_ENUM:
            if len(candidates) != 1 or candidates[0].value.kind is not SemanticValueKind.TEXT:
                raise _Terminal(
                    FactAdapterState.REJECTED,
                    (
                        _diagnostic(
                            RuntimeDiagnosticCode.ADAPTER_REJECTED,
                            policy.fact_name.value,
                            "AMBIGUOUS_CANDIDATE",
                        ),
                    ),
                )
            mapping = {item.source_value: item.strategy_direction for item in policy.enum_mappings}
            source_value = candidates[0].value.text_value
            assert source_value is not None
            direction = mapping.get(source_value)
            if direction is None:
                raise _terminal_for_rule(
                    policy.selector.selector_rule, SemanticRuleState.NO_MATCH, ()
                )
            return direction, candidates, sources
        assert policy.strategy_rule is not None
        request = DirectionRuleRequest(
            self._context(evaluation, policy.strategy_rule, sources, candidates=candidates),
            candidates,
            policy.allowed_source_states,
        )
        result = self._invoke(policy.strategy_rule, request, DirectionRuleResult)
        assert isinstance(result, DirectionRuleResult) and result.direction is not None
        return result.direction, candidates, sources

    def _direction(
        self, evaluation: EvaluationContext
    ) -> tuple[DirectionalFacts, StrategyDirection]:
        values: dict[DirectionFactName, StrategyDirection] = {}
        frame_values: list[TimeframeDirectionValue] = []
        frame_name = self._profile.mtf_direction_policy.frame_direction_fact
        for policy in self._profile.direction_policies:
            if policy.fact_name is frame_name:
                matching = tuple(
                    frame
                    for frame in self._typed_bundle.frames
                    if frame.frame.role in self._profile.mtf_direction_policy.required_roles
                    and frame.frame.timeframe
                    in self._profile.mtf_direction_policy.required_timeframes
                )
                for frame in matching:
                    direction, candidates, _ = self._direction_policy(
                        evaluation, policy, frame.frame.role
                    )
                    frame_values.append(
                        TimeframeDirectionValue(
                            frame.frame.timeframe,
                            frame.frame.role,
                            direction,
                            tuple(item.source_binding_id for item in candidates),
                            tuple(item.provenance_ref for item in candidates),
                        )
                    )
                    if frame.frame.role is TimeframeRole.PRIMARY:
                        values[policy.fact_name] = direction
            else:
                values[policy.fact_name] = self._direction_policy(evaluation, policy)[0]
        mtf_policy = self._profile.mtf_direction_policy
        mtf_candidates = tuple(
            candidate
            for item in frame_values
            for candidate in self._all_candidates_for_ids(item.source_binding_ids)
        )
        mtf_sources = self._sources_for_ids(
            tuple(item for value in frame_values for item in value.source_binding_ids)
        )
        request = MtfAggregationRequest(
            self._context(
                evaluation, mtf_policy.rule_identity, mtf_sources, candidates=mtf_candidates
            ),
            tuple(frame_values),
            mtf_policy.required_roles,
            mtf_policy.required_timeframes,
        )
        result = self._invoke(mtf_policy.rule_identity, request, MtfAggregationResult)
        assert isinstance(result, MtfAggregationResult) and result.direction is not None
        values[DirectionFactName.MTF] = result.direction
        facts = DirectionalFacts(
            values[DirectionFactName.ELLIOTT],
            values[DirectionFactName.TREND],
            values[DirectionFactName.STRUCTURE],
            values[DirectionFactName.MTF],
            values[DirectionFactName.PRIMARY],
            values[DirectionFactName.ALTERNATE],
        )
        return facts, result.direction

    def _all_candidates_for_ids(self, source_ids: tuple[str, ...]) -> tuple[SemanticCandidate, ...]:
        del source_ids
        return ()

    def _sources_for_ids(self, source_ids: tuple[str, ...]) -> tuple[AnalyticalSourceBinding, ...]:
        wanted = set(source_ids)
        return tuple(
            source
            for frame in self._typed_bundle.frames
            for source in frame.sources
            if source.source_binding_id in wanted
        )

    def _geometry_candidates(
        self,
        evaluation: EvaluationContext,
        policy: EntrySourcePolicy | StopSourcePolicy | TargetSourcePolicy,
        direction: StrategyDirection,
    ) -> tuple[tuple[SemanticCandidate, ...], tuple[AnalyticalSourceBinding, ...]]:
        candidates: list[SemanticCandidate] = []
        sources: list[AnalyticalSourceBinding] = []
        for selector in policy.allowed_selectors:
            extracted, resolved = self._extract(evaluation, selector)
            candidates.extend(extracted)
            sources.extend(resolved)
        pool = tuple(sorted(candidates, key=lambda item: item.candidate_id))
        if not pool or len({item.candidate_id for item in pool}) != len(pool):
            raise DataIntegrityError("geometry candidate population is invalid")
        applicable: list[SemanticCandidate] = []
        all_sources = tuple(sorted(set(sources), key=lambda item: item.canonical_key()))
        for candidate in pool:
            request = ApplicabilityRequest(
                self._context(
                    evaluation,
                    policy.direction_applicability_rule,
                    all_sources,
                    candidates=(candidate,),
                ),
                candidate,
                direction,
            )
            result = self._invoke(policy.direction_applicability_rule, request, ApplicabilityResult)
            assert isinstance(result, ApplicabilityResult)
            if result.applicable:
                applicable.append(candidate)
        if not applicable:
            raise _terminal_for_rule(
                policy.direction_applicability_rule, SemanticRuleState.NO_MATCH, ()
            )
        selection_request = CandidateSelectionRequest(
            self._context(
                evaluation, policy.candidate_selector, all_sources, candidates=tuple(applicable)
            ),
            tuple(applicable),
            direction,
        )
        result = self._invoke(policy.candidate_selector, selection_request, SelectionRuleResult)
        assert isinstance(result, SelectionRuleResult) and result.selected_candidate_ids is not None
        by_id = {item.candidate_id: item for item in applicable}
        if not set(result.selected_candidate_ids) <= set(by_id):
            raise DataIntegrityError("selection is not a request subset")
        return tuple(by_id[item] for item in result.selected_candidate_ids), all_sources

    def _entry(self, evaluation: EvaluationContext, direction: StrategyDirection) -> EntryFacts:
        policy = self._profile.entry_policy
        candidates, sources = self._geometry_candidates(evaluation, policy, direction)
        rank_request = CandidateRankingRequest(
            self._context(evaluation, policy.ranking_rule, sources, candidates=candidates),
            candidates,
            direction,
        )
        ranking = self._invoke(policy.ranking_rule, rank_request, RankingRuleResult)
        assert isinstance(ranking, RankingRuleResult) and ranking.ordered_candidate_ids is not None
        if set(ranking.ordered_candidate_ids) != {item.candidate_id for item in candidates} or len(
            ranking.ordered_candidate_ids
        ) != len(candidates):
            raise DataIntegrityError("ranking is not an exact permutation")
        winner = {item.candidate_id: item for item in candidates}[ranking.ordered_candidate_ids[0]]
        boundary_request = BoundarySelectionRequest(
            self._context(evaluation, policy.required_boundary_rule, sources, candidates=(winner,)),
            winner,
            direction,
        )
        boundary = self._invoke(policy.required_boundary_rule, boundary_request, BoundaryRuleResult)
        assert isinstance(boundary, BoundaryRuleResult)
        return EntryFacts(*boundary_entry_range(boundary))

    def _stop(self, evaluation: EvaluationContext, direction: StrategyDirection) -> StopFacts:
        policy = self._profile.stop_policy
        candidates, sources = self._geometry_candidates(evaluation, policy, direction)
        request = CandidateSelectionRequest(
            self._context(evaluation, policy.precedence_rule, sources, candidates=candidates),
            candidates,
            direction,
        )
        result = self._invoke(policy.precedence_rule, request, SelectionRuleResult)
        assert isinstance(result, SelectionRuleResult)
        winner = selection_winner(request, result)
        transformed = self._transform(evaluation, policy.buffer_rule, winner, direction, sources)
        if policy.volatility_adjustment_rule is not None:
            transformed = self._transform(
                evaluation, policy.volatility_adjustment_rule, transformed, direction, sources
            )
        assert transformed.value.float_value is not None
        return StopFacts(transformed.value.float_value)

    def _target(self, evaluation: EvaluationContext, direction: StrategyDirection) -> TargetFacts:
        policy = self._profile.target_policy
        candidates, sources = self._geometry_candidates(evaluation, policy, direction)
        request = CandidateRankingRequest(
            self._context(evaluation, policy.ranking_rule, sources, candidates=candidates),
            candidates,
            direction,
        )
        result = self._invoke(policy.ranking_rule, request, RankingRuleResult)
        assert isinstance(result, RankingRuleResult) and result.ordered_candidate_ids is not None
        if set(result.ordered_candidate_ids) != {item.candidate_id for item in candidates} or len(
            result.ordered_candidate_ids
        ) != len(candidates):
            raise DataIntegrityError("target ranking is not an exact permutation")
        ranked = tuple(
            {item.candidate_id: item for item in candidates}[item]
            for item in result.ordered_candidate_ids
        )
        if policy.threshold_rule is not None:
            threshold_request = ApplicabilityRequest(
                self._context(evaluation, policy.threshold_rule, sources, candidates=(ranked[0],)),
                ranked[0],
                direction,
            )
            threshold = self._invoke(policy.threshold_rule, threshold_request, ApplicabilityResult)
            assert isinstance(threshold, ApplicabilityResult)
            if not threshold.applicable:
                raise _terminal_for_rule(policy.threshold_rule, SemanticRuleState.NO_MATCH, ())
        winner = ranked[0]
        if policy.extension_rule is not None:
            extension_request = RankedCandidateSelectionRequest(
                self._context(evaluation, policy.extension_rule, sources, candidates=ranked),
                ranked,
                direction,
            )
            extension = self._invoke(policy.extension_rule, extension_request, SelectionRuleResult)
            assert isinstance(extension, SelectionRuleResult)
            winner = selection_winner(extension_request, extension, require_price=True)
        if winner.value.kind is not SemanticValueKind.PRICE:
            raise DataIntegrityError("target winner must contain PRICE")
        assert winner.value.float_value is not None
        return TargetFacts(winner.value.float_value)

    def _transform(
        self,
        evaluation: EvaluationContext,
        identity: RuleIdentity,
        candidate: SemanticCandidate,
        direction: StrategyDirection,
        sources: tuple[AnalyticalSourceBinding, ...],
    ) -> SemanticCandidate:
        request = PriceTransformationRequest(
            self._context(evaluation, identity, sources, candidates=(candidate,)),
            candidate,
            direction,
        )
        result = self._invoke(identity, request, PriceTransformationResult)
        assert isinstance(result, PriceTransformationResult) and result.candidate is not None
        transformed = result.candidate
        if (
            transformed.source_binding_id != candidate.source_binding_id
            or transformed.provenance_ref != candidate.provenance_ref
            or transformed.instrument_binding_id != candidate.instrument_binding_id
            or transformed.timeframe != candidate.timeframe
        ):
            raise DataIntegrityError("price transformation changed candidate lineage")
        return transformed

    def _confidence(
        self, evaluation: EvaluationContext
    ) -> tuple[float, tuple[RuntimeDiagnostic, ...]]:
        policy = self._profile.confidence_policy
        extracted = []
        all_sources: list[AnalyticalSourceBinding] = []
        for item in policy.inputs:
            try:
                result_candidates, sources = self._extract(evaluation, item.source_selector)
                result = CandidateRuleResult(SemanticRuleState.SUCCESS, (), result_candidates)
                all_sources.extend(sources)
            except _Terminal as terminal:
                if terminal.state is FactAdapterState.REJECTED and all(
                    x.code is RuntimeDiagnosticCode.MISSING_FACT for x in terminal.diagnostics
                ):
                    result = CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)
                else:
                    raise
            extracted.append((item, result))
        reduced = _reduce_confidence_policy(policy, tuple(extracted))
        if reduced.terminal_state is not None:
            raise _Terminal(reduced.terminal_state, reduced.diagnostics)
        sources = tuple(sorted(set(all_sources), key=lambda item: item.canonical_key()))
        base = self._confidence_rule(
            evaluation, policy.model_identity, reduced.included, policy.parameters, None, sources
        )
        final = base
        if policy.calibration_identity is not None:
            final = self._confidence_rule(
                evaluation,
                policy.calibration_identity,
                reduced.included,
                policy.parameters,
                base,
                sources,
            )
        return final, reduced.diagnostics

    def _confidence_rule(
        self,
        evaluation: EvaluationContext,
        identity: RuleIdentity,
        inputs: tuple[ConfidenceInputValue, ...],
        parameters: tuple[ModelParameter, ...],
        base: float | None,
        sources: tuple[AnalyticalSourceBinding, ...],
    ) -> float:
        request = ConfidenceRuleRequest(
            self._context(evaluation, identity, sources), inputs, parameters, base
        )
        result = self._invoke(identity, request, ConfidenceRuleResult)
        assert isinstance(result, ConfidenceRuleResult) and result.confidence is not None
        return result.confidence

    def _evidence(self, evaluation: EvaluationContext, policy: StrategyPolicy) -> tuple[
        tuple[StrategyEvidenceSnapshot, ...],
        StrategyEvidenceIdentity,
        tuple[RuntimeDiagnostic, ...],
    ]:
        records: list[_EvidenceRecord] = []
        diagnostics: list[RuntimeDiagnostic] = []
        for item in self._profile.evidence_taxonomy.keys:
            try:
                candidates, sources = self._extract(evaluation, item.source_selector)
            except _Terminal as terminal:
                if (
                    item.requirement is EvidenceRequirement.OPTIONAL
                    and terminal.state is FactAdapterState.REJECTED
                ):
                    diagnostics.extend(terminal.diagnostics)
                    continue
                raise
            request = EvidenceMappingRequest(
                self._context(evaluation, item.mapping_rule, sources, candidates=candidates),
                item.evidence_key,
                candidates,
            )
            result = self._invoke(item.mapping_rule, request, EvidenceMappingResult)
            assert (
                isinstance(result, EvidenceMappingResult)
                and result.selected_candidate_ids is not None
            )
            by_id = {candidate.candidate_id: candidate for candidate in candidates}
            if not result.selected_candidate_ids or not set(result.selected_candidate_ids) <= set(
                by_id
            ):
                raise DataIntegrityError("evidence mapping is not a non-empty subset")
            selected = tuple(by_id[key] for key in result.selected_candidate_ids)
            selected_sources = self._sources_for_ids(
                tuple(candidate.source_binding_id for candidate in selected)
            )
            freshness = _resolve_evidence_freshness(
                evidence_key=item.evidence_key,
                selected_candidates=selected,
                source_bindings=selected_sources,
                policy=item.freshness_policy,
                evaluation_timestamp=evaluation.evaluation_timestamp,
                requirement=item.requirement,
            )
            if freshness.terminal_state is not None:
                raise _Terminal(freshness.terminal_state, freshness.diagnostics)
            diagnostics.extend(freshness.diagnostics)
            if freshness.omitted:
                continue
            temporal = item.temporal_eligibility_policy
            eligible = True
            for rule_identity in (temporal.validity_rule, temporal.revision_rule):
                temporal_request = TemporalEligibilityRequest(
                    self._context(evaluation, rule_identity, selected_sources, candidates=selected),
                    selected,
                    temporal.required_timeframe_roles,
                    tuple(source.revision.revision_id for source in selected_sources),
                )
                temporal_result = self._invoke(
                    rule_identity, temporal_request, TemporalEligibilityResult
                )
                assert isinstance(temporal_result, TemporalEligibilityResult)
                if not temporal_result.eligible:
                    if item.requirement is EvidenceRequirement.OPTIONAL:
                        diagnostics.append(
                            _diagnostic(
                                RuntimeDiagnosticCode.TEMPORAL_FAILURE,
                                item.evidence_key,
                                RuntimeDiagnosticCode.TEMPORAL_FAILURE.value,
                                stage=RuntimeDiagnosticStage.TEMPORAL,
                            )
                        )
                        eligible = False
                        break
                    raise _Terminal(
                        FactAdapterState.REJECTED,
                        (
                            _diagnostic(
                                RuntimeDiagnosticCode.TEMPORAL_FAILURE,
                                item.evidence_key,
                                RuntimeDiagnosticCode.TEMPORAL_FAILURE.value,
                                stage=RuntimeDiagnosticStage.TEMPORAL,
                            ),
                        ),
                    )
            if not eligible:
                continue
            source_ids = tuple(candidate.source_binding_id for candidate in selected)
            refs = tuple(candidate.provenance_ref for candidate in selected)
            identity = derive_evidence_item_identity(
                strategy_identity=policy.strategy_identity,
                semantic_profile_identity=self._profile.identity,
                adapter_identity=self._identity,
                typed_bundle_id=self._typed_bundle.bundle_id,
                provenance_manifest_id=self._typed_bundle.provenance_manifest_id,
                evidence_key=item.evidence_key,
                mapping_rule=item.mapping_rule,
                validity_rule=temporal.validity_rule,
                revision_rule=temporal.revision_rule,
                selected_candidate_ids=tuple(candidate.candidate_id for candidate in selected),
                selected_source_binding_ids=source_ids,
                selected_provenance_refs=refs,
                fresh=True,
                temporally_eligible=True,
            )
            records.append(
                _EvidenceRecord(item.evidence_key, selected, identity, source_ids, refs, True, True)
            )
        if not records:
            raise _Terminal(
                FactAdapterState.REJECTED,
                (
                    _diagnostic(
                        RuntimeDiagnosticCode.MISSING_FACT,
                        self._profile.evidence_taxonomy.taxonomy_identity.reference,
                        "SELECTOR_NO_MATCH",
                    ),
                ),
            )
        all_sources = self._sources_for_ids(
            tuple(source for record in records for source in record.source_ids)
        )
        order_request = EvidenceOrderingRequest(
            self._context(evaluation, self._profile.evidence_taxonomy.ordering_rule, all_sources),
            tuple(record.key for record in records),
        )
        order_result = self._invoke(
            self._profile.evidence_taxonomy.ordering_rule, order_request, EvidenceOrderingResult
        )
        assert isinstance(order_result, EvidenceOrderingResult)
        order = materialize_evidence_order(order_request, order_result)
        by_key = {record.key: record for record in records}
        ordered = tuple(by_key[key] for key in order)
        set_identity = derive_evidence_set_identity(
            strategy_identity=policy.strategy_identity,
            semantic_profile_identity=self._profile.identity,
            adapter_identity=self._identity,
            typed_bundle_id=self._typed_bundle.bundle_id,
            provenance_manifest_id=self._typed_bundle.provenance_manifest_id,
            entries=tuple(
                (
                    record.key,
                    record.identity,
                    tuple(candidate.candidate_id for candidate in record.candidates),
                    record.source_ids,
                    record.provenance_refs,
                )
                for record in ordered
            ),
        )
        snapshots = tuple(
            StrategyEvidenceSnapshot(
                policy.strategy_identity,
                record.identity,
                record.key,
                record.fresh,
                record.eligible,
            )
            for record in ordered
        )
        return snapshots, set_identity, tuple(diagnostics)


__all__ = ["CanonicalFactAdapter"]
