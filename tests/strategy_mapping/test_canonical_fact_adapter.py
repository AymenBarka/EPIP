# mypy: disable-error-code="no-untyped-def,no-untyped-call,arg-type,type-arg,assignment,var-annotated"
from __future__ import annotations

from dataclasses import dataclass

import pytest

from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime._base import CONTRACT_VERSION, digest
from epip.strategy_runtime.context import EvaluationContext, RuntimeMode
from epip.strategy_runtime.facts import AnalyticalInputBundle
from epip.strategy_runtime.mtf import MultiTimeframeInputSet, TimeframeInput, TimeframeRole
from epip.strategy_runtime.profile import StrategyProfile
from epip.strategy_runtime.protocols import FactAdapterState
from epip.strategy_runtime.provenance import (
    FactAdapterIdentity,
    FactProvenance,
    ProvenanceManifest,
    SourceProvenance,
)
from epip.strategy_runtime.result import RuntimeDiagnosticCode
from epip.swing import SwingSequence


def _id(name):
    return RuleIdentity(name, "1", FOUNDATION_SCHEMA_VERSION, digest(name))


@dataclass(frozen=True)
class _Rule:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str
    calls: list
    outcomes: dict

    def invoke(self, request):
        self.calls.append((self.identity.rule_id, request))
        name = self.identity.rule_id
        if name in self.outcomes:
            outcome = self.outcomes[name]
            if isinstance(outcome, BaseException):
                raise outcome
            if callable(outcome):
                return outcome(request)
            return outcome
        if self.family is SemanticRuleFamily.SOURCE_EXTRACTION:
            source = request.source
            if name.startswith("direction"):
                value = SemanticValue(SemanticValueKind.TEXT, text_value="UP")
                values = (value,)
            elif name == "confidence-source":
                values = (SemanticValue(SemanticValueKind.FINITE_FLOAT, float_value=0.8),)
            else:
                prices = (
                    (100.0, 101.0)
                    if name == "entry-source"
                    else (95.0, 94.0) if name == "stop-source" else (120.0, 121.0)
                )
                if name.startswith("evidence"):
                    values = (SemanticValue(SemanticValueKind.TEXT, text_value=name),)
                else:
                    values = tuple(
                        SemanticValue(SemanticValueKind.PRICE, float_value=x) for x in prices
                    )
            candidates = tuple(
                SemanticCandidate.create(
                    source_binding_id=source.source_binding_id,
                    provenance_ref=source.provenance_ref,
                    instrument_binding_id=source.instrument.binding_id,
                    timeframe=source.timeframe,
                    source_rule_identity=self.identity,
                    value=value,
                )
                for value in values
            )
            return CandidateRuleResult(SemanticRuleState.SUCCESS, (), candidates)
        if self.family is SemanticRuleFamily.MTF_AGGREGATION:
            return MtfAggregationResult(SemanticRuleState.SUCCESS, (), StrategyDirection.BUY)
        if self.family is SemanticRuleFamily.APPLICABILITY:
            return ApplicabilityResult(SemanticRuleState.SUCCESS, (), True)
        if self.family is SemanticRuleFamily.CANDIDATE_SELECTION:
            selected = (
                (request.candidates[0].candidate_id,)
                if name == "extension"
                else tuple(x.candidate_id for x in request.candidates)
            )
            return SelectionRuleResult(SemanticRuleState.SUCCESS, (), selected)
        if self.family is SemanticRuleFamily.CANDIDATE_RANKING:
            ordered = tuple(x.candidate_id for x in reversed(request.candidates))
            return RankingRuleResult(SemanticRuleState.SUCCESS, (), ordered)
        if self.family is SemanticRuleFamily.BOUNDARY_SELECTION:
            return BoundaryRuleResult(SemanticRuleState.SUCCESS, (), request.candidate.value)
        if self.family is SemanticRuleFamily.PRECEDENCE:
            return SelectionRuleResult(
                SemanticRuleState.SUCCESS, (), (request.candidates[0].candidate_id,)
            )
        if self.family is SemanticRuleFamily.PRICE_TRANSFORMATION:
            return PriceTransformationResult(SemanticRuleState.SUCCESS, (), request.candidate)
        if self.family is SemanticRuleFamily.CONFIDENCE:
            return ConfidenceRuleResult(SemanticRuleState.SUCCESS, (), 0.8)
        if self.family is SemanticRuleFamily.EVIDENCE_MAPPING:
            return EvidenceMappingResult(
                SemanticRuleState.SUCCESS, (), tuple(x.candidate_id for x in request.candidates)
            )
        if self.family is SemanticRuleFamily.TEMPORAL_ELIGIBILITY:
            return TemporalEligibilityResult(SemanticRuleState.SUCCESS, (), True)
        if self.family is SemanticRuleFamily.EVIDENCE_ORDERING:
            return EvidenceOrderingResult(
                SemanticRuleState.SUCCESS, (), tuple(reversed(request.evidence_keys))
            )
        raise AssertionError(name)


def _family_shape(family):
    return {
        SemanticRuleFamily.SOURCE_EXTRACTION: (
            SemanticInvocationKind.SOURCE_EXTRACTION,
            SemanticResultKind.CANDIDATES,
        ),
        SemanticRuleFamily.DIRECTION_MAPPING: (
            SemanticInvocationKind.DIRECTION,
            SemanticResultKind.DIRECTION,
        ),
        SemanticRuleFamily.MTF_AGGREGATION: (
            SemanticInvocationKind.MTF_AGGREGATION,
            SemanticResultKind.MTF_AGGREGATION,
        ),
        SemanticRuleFamily.APPLICABILITY: (
            SemanticInvocationKind.APPLICABILITY,
            SemanticResultKind.APPLICABILITY,
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
        SemanticRuleFamily.PRECEDENCE: (
            SemanticInvocationKind.SELECTION,
            SemanticResultKind.SELECTION,
        ),
        SemanticRuleFamily.PRICE_TRANSFORMATION: (
            SemanticInvocationKind.PRICE_TRANSFORMATION,
            SemanticResultKind.PRICE_TRANSFORMATION,
        ),
        SemanticRuleFamily.CONFIDENCE: (
            SemanticInvocationKind.CONFIDENCE,
            SemanticResultKind.CONFIDENCE,
        ),
        SemanticRuleFamily.EVIDENCE_MAPPING: (
            SemanticInvocationKind.EVIDENCE_MAPPING,
            SemanticResultKind.EVIDENCE_MAPPING,
        ),
        SemanticRuleFamily.TEMPORAL_ELIGIBILITY: (
            SemanticInvocationKind.TEMPORAL_ELIGIBILITY,
            SemanticResultKind.TEMPORAL_ELIGIBILITY,
        ),
        SemanticRuleFamily.EVIDENCE_ORDERING: (
            SemanticInvocationKind.EVIDENCE_ORDERING,
            SemanticResultKind.EVIDENCE_ORDERING,
        ),
    }[family]


def _fixture(outcomes=None, options=None):
    calls = []
    outcomes = {} if outcomes is None else outcomes
    options = {} if options is None else options
    identities = {}
    families = {}

    def rid(name, family):
        identities[name] = _id(name)
        families[name] = family
        return identities[name]

    primary = (TimeframeRole.PRIMARY,)
    both = (TimeframeRole.PRIMARY, TimeframeRole.HIGHER)

    def selector(
        name,
        roles=primary,
        kind=None,
        source_kind=AnalyticalSourceKind.SWING,
        source_contract="epip.swing.models.SwingSequence",
    ):
        return SourceSelector(
            source_kind,
            source_contract,
            kind
            or (
                SourceSelectorKind.DIRECT_ENUM
                if name.startswith("direction")
                else SourceSelectorKind.PRICE_CANDIDATES
            ),
            rid(name, SemanticRuleFamily.SOURCE_EXTRACTION),
            True,
            roles,
        )

    direction_policies = tuple(
        DirectionFactPolicy(
            name,
            selector(
                "direction-" + name.value.lower(),
                both if name is DirectionFactName.PRIMARY else primary,
                (
                    SourceSelectorKind.HYPOTHESIS_RULE
                    if options.get("rule_direction") and name is DirectionFactName.ALTERNATE
                    else None
                ),
            ),
            ("VALID",),
            (
                ()
                if options.get("rule_direction") and name is DirectionFactName.ALTERNATE
                else (EnumDirectionMapping("UP", StrategyDirection.BUY),)
            ),
            (
                rid("direction-rule", SemanticRuleFamily.DIRECTION_MAPPING)
                if options.get("rule_direction") and name is DirectionFactName.ALTERNATE
                else None
            ),
            NonAcceptanceAction.REJECT,
            NonAcceptanceAction.REQUIRE_SINGLE,
        )
        for name in (
            DirectionFactName.ELLIOTT,
            DirectionFactName.TREND,
            DirectionFactName.STRUCTURE,
            DirectionFactName.PRIMARY,
            DirectionFactName.ALTERNATE,
        )
    )
    app = rid("applicability", SemanticRuleFamily.APPLICABILITY)
    choose = rid("selection", SemanticRuleFamily.CANDIDATE_SELECTION)
    entry_selector = selector("entry-source")
    entry_selectors = (entry_selector,)
    if options.get("duplicate_geometry_selectors"):
        entry_selectors = (
            entry_selector,
            SourceSelector(
                entry_selector.source_kind,
                entry_selector.source_contract,
                SourceSelectorKind.DIRECT_VALUE,
                entry_selector.selector_rule,
                True,
                entry_selector.frame_roles,
            ),
        )
    entry = EntrySourcePolicy(
        _id("entry-policy"),
        entry_selectors,
        choose,
        rid("entry-rank", SemanticRuleFamily.CANDIDATE_RANKING),
        rid("boundary", SemanticRuleFamily.BOUNDARY_SELECTION),
        app,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        True,
    )
    volatility = (
        rid("volatility", SemanticRuleFamily.PRICE_TRANSFORMATION)
        if options.get("volatility")
        else None
    )
    stop = StopSourcePolicy(
        _id("stop-policy"),
        (selector("stop-source"),),
        choose,
        rid("precedence", SemanticRuleFamily.PRECEDENCE),
        rid("buffer", SemanticRuleFamily.PRICE_TRANSFORMATION),
        volatility,
        app,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        True,
    )
    target = TargetSourcePolicy(
        _id("target-policy"),
        (selector("target-source"),),
        choose,
        rid("target-rank", SemanticRuleFamily.CANDIDATE_RANKING),
        rid("threshold", SemanticRuleFamily.APPLICABILITY),
        (
            None
            if options.get("no_target_extension")
            else rid("extension", SemanticRuleFamily.CANDIDATE_SELECTION)
        ),
        app,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        True,
    )
    confidence_primary = selector("confidence-source", primary)
    confidence_higher = selector("confidence-source", (TimeframeRole.HIGHER,))
    calibration = (
        rid("calibration", SemanticRuleFamily.CONFIDENCE) if options.get("calibration") else None
    )
    confidence_optional = bool(options.get("confidence_optional"))
    confidence = ConfidencePolicy(
        _id("confidence-policy"),
        ConfidenceModelKind.CALIBRATED if calibration is not None else ConfidenceModelKind.WEIGHTED,
        rid("confidence-model", SemanticRuleFamily.CONFIDENCE),
        (
            ConfidenceInput("alpha", confidence_primary, True),
            ConfidenceInput("beta", confidence_higher, not confidence_optional),
        ),
        (),
        calibration,
        0.0,
        1.0,
        NonAcceptanceAction.NO_FACT if confidence_optional else NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
    )
    fresh = FreshnessPolicy(
        _id("fresh"),
        FreshnessBasis.OBSERVATION,
        options.get("freshness_seconds", 7200),
        NonAcceptanceAction.REJECT,
    )
    requirements = options.get("evidence_requirements", {})

    def evidence_policy(key):
        temporal = TemporalEligibilityPolicy(
            _id("temporal-" + key),
            both,
            rid("validity-" + key, SemanticRuleFamily.TEMPORAL_ELIGIBILITY),
            rid("revision-" + key, SemanticRuleFamily.TEMPORAL_ELIGIBILITY),
            NonAcceptanceAction.REJECT,
        )
        evidence_selector = selector("evidence-" + key, both if key == "alpha" else primary)
        if options.get("absent_optional_evidence") and key == "alpha":
            evidence_selector = selector(
                "evidence-" + key,
                both,
                source_kind=AnalyticalSourceKind.MARKET_STRUCTURE,
                source_contract="epip.market_structure.models.MarketStructureSnapshot",
            )
        return EvidenceKeyPolicy(
            key,
            requirements.get(key, EvidenceRequirement.REQUIRED),
            evidence_selector,
            rid("map-" + key, SemanticRuleFamily.EVIDENCE_MAPPING),
            fresh,
            temporal,
            True,
        )

    evidence = EvidenceTaxonomy(
        _id("taxonomy"),
        tuple(evidence_policy(key) for key in ("alpha", "zeta")),
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        rid("evidence-order", SemanticRuleFamily.EVIDENCE_ORDERING),
    )
    mtf = MtfDirectionPolicyRef(
        both,
        ("H1", "H4"),
        DirectionFactName.PRIMARY,
        rid("mtf", SemanticRuleFamily.MTF_AGGREGATION),
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
    )
    strategy = StrategyIdentity("strategy", "1")
    parent = StrategyProfile.create(
        profile_id="profile",
        profile_version="1",
        strategy_identity=strategy,
        compatible_runtime_contract_versions=(CONTRACT_VERSION,),
        compatible_adapter_contract_versions=(CONTRACT_VERSION,),
        required_source_domains=("SWING",),
        optional_source_domains=(),
        required_evidence_keys=tuple(
            key
            for key in ("alpha", "zeta")
            if requirements.get(key, EvidenceRequirement.REQUIRED) is EvidenceRequirement.REQUIRED
        ),
        optional_evidence_keys=tuple(
            key
            for key in ("alpha", "zeta")
            if requirements.get(key, EvidenceRequirement.REQUIRED) is EvidenceRequirement.OPTIONAL
        ),
        enabled_direction_facts=tuple(sorted(x.value for x in DirectionFactName)),
        enabled_geometry_sources=("SWING",),
        confidence_model_reference=confidence.policy_identity.reference,
        evidence_taxonomy_reference=evidence.taxonomy_identity.reference,
        mtf_requirement=mtf.rule_identity.reference,
        mapping_rules_reference="semantic@1",
    )
    semantic = StrategySemanticMappingProfile.create(
        semantic_profile_id="semantic",
        semantic_profile_version="1",
        parent_profile=parent,
        direction_policies=direction_policies,
        mtf_direction_policy=mtf,
        entry_policy=entry,
        stop_policy=stop,
        target_policy=target,
        confidence_policy=confidence,
        evidence_taxonomy=evidence,
        global_conflict_action=NonAcceptanceAction.REJECT,
    )
    policy = StrategyPolicy(
        "policy",
        "1",
        strategy,
        (StrategyDirection.BUY,),
        1.0,
        0.5,
        parent.required_evidence_keys,
        parent.optional_evidence_keys,
        60,
        2,
        (),
    )
    adapter_identity = FactAdapterIdentity("canonical", "1", CONTRACT_VERSION, "a" * 64)
    context = EvaluationContext.create(
        instrument_id="instrument",
        symbol="EURUSD",
        primary_timeframe="H1",
        evaluation_timestamp="2026-01-01T10:00:00Z",
        event_timestamp="2026-01-01T10:00:00Z",
        receipt_timestamp=None,
        runtime_mode=RuntimeMode.BACKTEST,
        profile_identity=parent.identity,
        source_set_id="sources",
        run_id="run",
    )
    instrument = InstrumentBinding.create("instrument", "EURUSD", (), "1")

    def source(role, timeframe, object_id):
        payload = SwingSequence("EURUSD", timeframe, ())
        return AnalyticalSourceBinding.create(
            source_kind=AnalyticalSourceKind.SWING,
            source_contract_version="1",
            source_object_id=object_id,
            instrument=instrument,
            timeframe=timeframe,
            observation_timestamp=(
                options.get("higher_observation", "2026-01-01T09:30:00Z")
                if role is TimeframeRole.HIGHER
                else "2026-01-01T09:30:00Z"
            ),
            availability_timestamp=(
                options.get("higher_availability", "2026-01-01T09:30:01Z")
                if role is TimeframeRole.HIGHER
                else "2026-01-01T09:30:01Z"
            ),
            as_of_timestamp="2026-01-01T09:31:00Z",
            revision=RevisionIdentity(object_id, "revision-" + object_id, 0, None),
            superseded_at=None,
            closed=True,
            provenance_ref=object_id,
            payload=payload,
        )

    sources = (
        source(TimeframeRole.PRIMARY, "H1", "primary"),
        source(TimeframeRole.HIGHER, "H4", "higher"),
    )
    frames = tuple(
        TimeframeAnalyticalFrame.create(
            TimeframeInput(
                timeframe,
                role,
                "2026-01-01T09:00:00Z",
                "2026-01-01T10:00:00Z",
                "2026-01-01T10:00:00Z",
                True,
                (item.source_object_id,),
                (item.provenance_ref,),
            ),
            (item,),
            (item.provenance_ref,),
        )
        for item, role, timeframe in zip(sources, both, ("H1", "H4"), strict=True)
    )
    coherence = MultiTimeframeInputSet.create(
        "H1",
        "2026-01-01T10:00:00.000000Z",
        tuple(sorted((frame.frame for frame in frames), key=lambda item: item.timeframe)),
    )
    source_provenance = tuple(
        SourceProvenance(
            item.source_contract,
            item.source_contract,
            "1",
            item.source_object_id,
            item.observation_timestamp,
            "1",
            None,
            "b" * 64,
        )
        for item in sources
    )
    fact_keys = (
        "direction.elliott",
        "direction.trend",
        "direction.structure",
        "direction.mtf",
        "direction.primary",
        "direction.alternate",
        "entry",
        "stop",
        "target",
        "confidence",
        "evidence",
    )
    facts = tuple(
        FactProvenance(
            key,
            ("primary",),
            adapter_identity.adapter_id,
            adapter_identity.adapter_version,
            parent.identity.profile_id,
            parent.identity.profile_version,
            "semantic",
            "1",
            "c" * 64,
        )
        for key in fact_keys
    )
    manifest = ProvenanceManifest.create(
        tuple(sorted(source_provenance, key=lambda item: item.source_object_id)),
        tuple(sorted(facts, key=lambda item: item.fact_key)),
        parent.identity,
        adapter_identity,
        context.evaluation_id,
    )
    typed = MultiTimeframeAnalyticalBundle.create(
        instrument, coherence, frames, manifest.manifest_id
    )
    primary_payload = sources[0].payload
    if options.get("p01_primary_mode") == "mismatch":
        primary_payload = SwingSequence("EURUSD", "H4", ())
    elif options.get("p01_primary_mode") == "omitted":
        primary_payload = None
    inputs = AnalyticalInputBundle(
        primary_payload, None, None, None, None, None, None, None, coherence, manifest
    )
    declarations = []
    implementations = []
    for name, family in families.items():
        invocation, result = _family_shape(family)
        declaration = SemanticRuleDeclaration(
            identities[name], family, invocation, result, "impl-" + name
        )
        declarations.append(declaration)
        implementations.append(
            _Rule(
                identities[name],
                family,
                invocation,
                result,
                "impl-" + name,
                calls,
                outcomes,
            )
        )
    rule_set = ResolvedSemanticRuleSet(
        ResolvedRuleManifest.create(tuple(declarations)), tuple(implementations)
    )
    binding = AdapterInvocationBinding.create(
        adapter_identity=adapter_identity,
        semantic_profile_identity=semantic.identity,
        resolved_rule_set_id=rule_set.manifest.rule_set_id,
        typed_bundle_id=typed.bundle_id,
        analytical_input_digest=digest(inputs),
        provenance_manifest_id=manifest.manifest_id,
        instrument_binding_id=instrument.binding_id,
    )
    return (
        CanonicalFactAdapter(adapter_identity, semantic, rule_set, typed, binding),
        context,
        inputs,
        parent,
        policy,
        calls,
    )


def test_complete_adapter_is_accepted_deterministic_and_preserves_semantic_orders():
    adapter, context, inputs, profile, policy, calls = _fixture()
    first = adapter.adapt(context, inputs, profile, policy)
    first_calls = tuple(calls)
    calls.clear()
    second = adapter.adapt(context, inputs, profile, policy)
    assert first == second
    assert first.state is FactAdapterState.ACCEPTED
    assert first.bundle is not None
    assert first.bundle.directional_facts.mtf_direction is StrategyDirection.BUY
    assert first.bundle.entry_facts.zone_lower == first.bundle.entry_facts.zone_upper == 101.0
    assert first.bundle.stop_facts.invalidation_price in (94.0, 95.0)
    assert first.bundle.target_facts.target_price in (120.0, 121.0)
    assert first.bundle.confidence == 0.8
    assert tuple(item.evidence_key for item in first.bundle.evidence) == ("zeta", "alpha")
    assert all(item.fresh and item.temporally_eligible for item in first.bundle.evidence)
    assert first_calls == tuple(calls)
    extension = next(request for name, request in calls if name == "extension")
    ranking = next(request for name, request in calls if name == "target-rank")
    ranked_ids = tuple(item.candidate_id for item in extension.candidates)
    assert ranked_ids == tuple(reversed(tuple(item.candidate_id for item in ranking.candidates)))


def test_structural_invalidity_prevents_all_semantic_invocation():
    adapter, context, inputs, profile, policy, calls = _fixture()
    bad = StrategyPolicy(
        "other",
        "1",
        StrategyIdentity("other", "1"),
        policy.enabled_directions,
        policy.minimum_rr,
        policy.minimum_confidence,
        policy.required_evidence,
        policy.optional_evidence,
        policy.expiration_seconds,
        policy.numeric_precision,
        policy.elliott_policy,
    )
    result = adapter.adapt(context, inputs, profile, bad)
    assert result.state is FactAdapterState.INVALID_INPUT
    assert result.bundle is None
    assert calls == []


def test_rule_terminal_states_are_translated_and_fail_fast():
    cases = (
        (SemanticRuleState.NO_MATCH, FactAdapterState.REJECTED),
        (SemanticRuleState.REJECTED, FactAdapterState.REJECTED),
        (SemanticRuleState.INVALID_INPUT, FactAdapterState.INVALID_INPUT),
        (SemanticRuleState.FAILED, FactAdapterState.FAILED),
    )
    for state, expected in cases:
        adapter, context, inputs, profile, policy, calls = _fixture(
            {"direction-alternate": CandidateRuleResult(state, (), None)}
        )
        result = adapter.adapt(context, inputs, profile, policy)
        assert result.state is expected
        assert result.bundle is None
        assert len(calls) == 1


def test_unexpected_rule_exception_is_sanitized():
    adapter, context, inputs, profile, policy, _ = _fixture(
        {"direction-alternate": RuntimeError("C:\\secret\\payload.txt")}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.FAILED
    assert result.bundle is None
    assert "secret" not in repr(result.diagnostics)
    assert result.diagnostics[0].message == "FAILED"


def test_entry_empty_applicability_stops_selection():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"applicability": ApplicabilityResult(SemanticRuleState.SUCCESS, (), False)}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED
    assert "selection" not in tuple(name for name, _ in calls)


def test_invalid_geometry_selection_and_ranking_fail_closed():
    invalid_selection = SelectionRuleResult(SemanticRuleState.SUCCESS, (), ("unknown",))
    adapter, context, inputs, profile, policy, _ = _fixture({"selection": invalid_selection})
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT
    invalid_ranking = RankingRuleResult(SemanticRuleState.SUCCESS, (), ("unknown",))
    adapter, context, inputs, profile, policy, _ = _fixture({"entry-rank": invalid_ranking})
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT


def test_target_threshold_false_stops_extension():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"threshold": ApplicabilityResult(SemanticRuleState.SUCCESS, (), False)}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED
    assert "extension" not in tuple(name for name, _ in calls)


def test_confidence_failure_stops_evidence():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"confidence-model": ConfidenceRuleResult(SemanticRuleState.FAILED, (), None)}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.FAILED
    assert not any(name.startswith("evidence-") for name, _ in calls)


def test_evidence_mapping_and_temporal_fail_fast():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"map-alpha": EvidenceMappingResult(SemanticRuleState.SUCCESS, (), ("unknown",))}
    )
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT
    assert "validity-alpha" not in tuple(name for name, _ in calls)
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"validity-alpha": TemporalEligibilityResult(SemanticRuleState.SUCCESS, (), False)}
    )
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.REJECTED
    assert "revision-alpha" not in tuple(name for name, _ in calls)


def test_evidence_ordering_requires_exact_permutation():
    adapter, context, inputs, profile, policy, _ = _fixture(
        {"evidence-order": EvidenceOrderingResult(SemanticRuleState.SUCCESS, (), ("alpha",))}
    )
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT


def _price_candidate(request, value, *, source_binding_id=None):
    candidate = request.candidate
    return SemanticCandidate.create(
        source_binding_id=source_binding_id or candidate.source_binding_id,
        provenance_ref=candidate.provenance_ref,
        instrument_binding_id=candidate.instrument_binding_id,
        timeframe=candidate.timeframe,
        source_rule_identity=candidate.source_rule_identity,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=value),
    )


def test_rule_based_direction_is_propagated_without_frame_fallback():
    direction = DirectionRuleResult(SemanticRuleState.SUCCESS, (), StrategyDirection.SELL)
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"direction-rule": direction}, {"rule_direction": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None
    assert result.bundle.directional_facts.alternate_direction is StrategyDirection.SELL
    name, request = next(item for item in calls if item[0] == "direction-rule")
    assert name == "direction-rule"
    assert request.context.timeframe_role is None
    assert request.context.source_binding_ids
    assert tuple(name for name, _ in calls).count("direction-rule") == 1


def test_malformed_direction_result_fails_closed_before_geometry():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"direction-rule": object()}, {"rule_direction": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT
    assert result.bundle is None
    assert "entry-source" not in tuple(name for name, _ in calls)
    assert "object" not in repr(result.diagnostics)


def test_optional_stop_volatility_transform_receives_buffered_value():
    def buffer(request):
        return PriceTransformationResult(
            SemanticRuleState.SUCCESS, (), _price_candidate(request, 93.0)
        )

    def volatility(request):
        assert request.candidate.value.float_value == 93.0
        return PriceTransformationResult(
            SemanticRuleState.SUCCESS, (), _price_candidate(request, 92.0)
        )

    adapter, context, inputs, profile, policy, calls = _fixture(
        {"buffer": buffer, "volatility": volatility}, {"volatility": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None and result.bundle.stop_facts.invalidation_price == 92.0
    names = tuple(name for name, _ in calls)
    assert names.index("precedence") < names.index("buffer") < names.index("volatility")


def test_terminal_stop_volatility_fails_fast_before_target():
    terminal = PriceTransformationResult(SemanticRuleState.FAILED, (), None)
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"volatility": terminal}, {"volatility": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.FAILED and result.bundle is None
    assert "target-source" not in tuple(name for name, _ in calls)


def test_calibrated_confidence_receives_base_and_precedes_evidence():
    def calibration(request):
        assert request.base_confidence == 0.8
        return ConfidenceRuleResult(SemanticRuleState.SUCCESS, (), 0.7)

    adapter, context, inputs, profile, policy, calls = _fixture(
        {"calibration": calibration}, {"calibration": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None and result.bundle.confidence == 0.7
    names = tuple(name for name, _ in calls)
    assert names.count("confidence-model") == names.count("calibration") == 1
    assert (
        names.index("confidence-model") < names.index("calibration") < names.index("evidence-alpha")
    )


def test_calibration_failure_is_sanitized_and_stops_evidence():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"calibration": RuntimeError("C:\\private\\calibration")}, {"calibration": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.FAILED and result.bundle is None
    assert "private" not in repr(result.diagnostics)
    assert not any(name.startswith("evidence-") for name, _ in calls)


def test_optional_confidence_no_match_is_reduced_before_model():
    no_match = CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)

    def confidence_source(request):
        if request.source.timeframe == "H4":
            return no_match
        return CandidateRuleResult(
            SemanticRuleState.SUCCESS,
            (),
            (
                SemanticCandidate.create(
                    source_binding_id=request.source.source_binding_id,
                    provenance_ref=request.source.provenance_ref,
                    instrument_binding_id=request.source.instrument.binding_id,
                    timeframe=request.source.timeframe,
                    source_rule_identity=request.context.rule_identity,
                    value=SemanticValue(SemanticValueKind.FINITE_FLOAT, float_value=0.8),
                ),
            ),
        )

    adapter, context, inputs, profile, policy, calls = _fixture(
        {"confidence-source": confidence_source}, {"confidence_optional": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    model_request = next(request for name, request in calls if name == "confidence-model")
    assert tuple(item.input_key for item in model_request.inputs) == ("alpha",)


def test_required_confidence_no_match_rejects_before_model():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"confidence-source": CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    assert "confidence-model" not in tuple(name for name, _ in calls)


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        (SemanticRuleState.REJECTED, FactAdapterState.REJECTED),
        (SemanticRuleState.INVALID_INPUT, FactAdapterState.INVALID_INPUT),
        (SemanticRuleState.FAILED, FactAdapterState.FAILED),
    ),
)
def test_confidence_extraction_terminal_states_stop_model(state, expected):
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"confidence-source": CandidateRuleResult(state, (), None)}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is expected and result.bundle is None
    assert "confidence-model" not in tuple(name for name, _ in calls)


def test_optional_evidence_no_match_is_omitted_before_mapping_and_temporal():
    options = {"evidence_requirements": {"alpha": EvidenceRequirement.OPTIONAL}}
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"evidence-alpha": CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)}, options
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None
    assert tuple(item.evidence_key for item in result.bundle.evidence) == ("zeta",)
    names = tuple(name for name, _ in calls)
    assert (
        "map-alpha" not in names and "validity-alpha" not in names and "revision-alpha" not in names
    )
    order = next(request for name, request in calls if name == "evidence-order")
    assert order.evidence_keys == ("zeta",)


def test_required_evidence_no_match_rejects_before_mapping():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"evidence-alpha": CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    assert "map-alpha" not in tuple(name for name, _ in calls)


def test_required_stale_evidence_stops_before_temporal_and_ordering():
    adapter, context, inputs, profile, policy, calls = _fixture(
        options={"freshness_seconds": 2000, "higher_observation": "2026-01-01T07:00:00Z"}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    names = tuple(name for name, _ in calls)
    assert (
        "validity-alpha" not in names
        and "revision-alpha" not in names
        and "evidence-order" not in names
    )


def test_optional_stale_evidence_is_omitted_and_remaining_evidence_continues():
    options = {
        "freshness_seconds": 2000,
        "higher_observation": "2026-01-01T07:00:00Z",
        "evidence_requirements": {"alpha": EvidenceRequirement.OPTIONAL},
    }
    adapter, context, inputs, profile, policy, calls = _fixture(options=options)
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None
    assert tuple(item.evidence_key for item in result.bundle.evidence) == ("zeta",)
    names = tuple(name for name, _ in calls)
    assert "validity-alpha" not in names and "revision-alpha" not in names
    assert "validity-zeta" in names and "evidence-order" in names


def test_optional_temporal_false_omits_item_and_required_false_stops_revision():
    false = TemporalEligibilityResult(SemanticRuleState.SUCCESS, (), False)
    options = {"evidence_requirements": {"alpha": EvidenceRequirement.OPTIONAL}}
    adapter, context, inputs, profile, policy, calls = _fixture({"validity-alpha": false}, options)
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None
    assert tuple(item.evidence_key for item in result.bundle.evidence) == ("zeta",)
    assert "revision-alpha" not in tuple(name for name, _ in calls)

    adapter, context, inputs, profile, policy, calls = _fixture({"validity-alpha": false})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    assert "revision-alpha" not in tuple(name for name, _ in calls)


def test_temporal_terminal_state_is_translated_without_boolean_conflation():
    terminal = TemporalEligibilityResult(SemanticRuleState.INVALID_INPUT, (), None)
    adapter, context, inputs, profile, policy, calls = _fixture({"validity-alpha": terminal})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "revision-alpha" not in tuple(name for name, _ in calls)


def test_all_optional_evidence_omitted_rejects_before_ordering():
    options = {
        "evidence_requirements": {
            "alpha": EvidenceRequirement.OPTIONAL,
            "zeta": EvidenceRequirement.OPTIONAL,
        }
    }
    no_match = CandidateRuleResult(SemanticRuleState.NO_MATCH, (), None)
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"evidence-alpha": no_match, "evidence-zeta": no_match}, options
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    assert result.diagnostics[-1].message == "SELECTOR_NO_MATCH"
    assert "evidence-order" not in tuple(name for name, _ in calls)


def test_wrong_rule_result_and_source_lineage_fail_closed():
    adapter, context, inputs, profile, policy, calls = _fixture({"direction-alternate": object()})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "entry-source" not in tuple(name for name, _ in calls)

    def wrong_lineage(request):
        candidate = SemanticCandidate.create(
            source_binding_id="wrong-source",
            provenance_ref=request.source.provenance_ref,
            instrument_binding_id=request.source.instrument.binding_id,
            timeframe=request.source.timeframe,
            source_rule_identity=request.context.rule_identity,
            value=SemanticValue(SemanticValueKind.TEXT, text_value="UP"),
        )
        return CandidateRuleResult(SemanticRuleState.SUCCESS, (), (candidate,))

    adapter, context, inputs, profile, policy, calls = _fixture(
        {"direction-alternate": wrong_lineage}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "entry-source" not in tuple(name for name, _ in calls)


def test_target_ranking_value_kind_and_transform_lineage_fail_closed():
    invalid_ranking = RankingRuleResult(SemanticRuleState.SUCCESS, (), ("unknown",))
    adapter, context, inputs, profile, policy, _ = _fixture({"target-rank": invalid_ranking})
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT

    def text_targets(request):
        candidate = SemanticCandidate.create(
            source_binding_id=request.source.source_binding_id,
            provenance_ref=request.source.provenance_ref,
            instrument_binding_id=request.source.instrument.binding_id,
            timeframe=request.source.timeframe,
            source_rule_identity=request.context.rule_identity,
            value=SemanticValue(SemanticValueKind.TEXT, text_value="target"),
        )
        return CandidateRuleResult(SemanticRuleState.SUCCESS, (), (candidate,))

    adapter, context, inputs, profile, policy, _ = _fixture({"target-source": text_targets})
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT

    def wrong_transform_lineage(request):
        return PriceTransformationResult(
            SemanticRuleState.SUCCESS,
            (),
            _price_candidate(request, 93.0, source_binding_id="wrong-source"),
        )

    adapter, context, inputs, profile, policy, calls = _fixture({"buffer": wrong_transform_lineage})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "target-source" not in tuple(name for name, _ in calls)


def test_structurally_absent_optional_evidence_source_uses_no_match_path():
    options = {
        "absent_optional_evidence": True,
        "evidence_requirements": {"alpha": EvidenceRequirement.OPTIONAL},
    }
    adapter, context, inputs, profile, policy, calls = _fixture(options=options)
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.ACCEPTED
    assert result.bundle is not None
    assert tuple(item.evidence_key for item in result.bundle.evidence) == ("zeta",)
    assert "evidence-alpha" not in tuple(name for name, _ in calls)


@pytest.mark.parametrize("values", (("UP", "DOWN"), ("UNKNOWN",)))
def test_direct_direction_ambiguity_and_unknown_value_fail_closed(values):
    def extraction(request):
        candidates = tuple(
            SemanticCandidate.create(
                source_binding_id=request.source.source_binding_id,
                provenance_ref=request.source.provenance_ref,
                instrument_binding_id=request.source.instrument.binding_id,
                timeframe=request.source.timeframe,
                source_rule_identity=request.context.rule_identity,
                value=SemanticValue(SemanticValueKind.TEXT, text_value=value),
            )
            for value in values
        )
        return CandidateRuleResult(SemanticRuleState.SUCCESS, (), candidates)

    adapter, context, inputs, profile, policy, calls = _fixture({"direction-alternate": extraction})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    assert "entry-source" not in tuple(name for name, _ in calls)


def test_duplicate_geometry_candidates_fail_closed_before_applicability():
    adapter, context, inputs, profile, policy, calls = _fixture(
        options={"duplicate_geometry_selectors": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "applicability" not in tuple(name for name, _ in calls)


def test_target_without_extension_rejects_non_price_winner():
    def text_targets(request):
        candidate = SemanticCandidate.create(
            source_binding_id=request.source.source_binding_id,
            provenance_ref=request.source.provenance_ref,
            instrument_binding_id=request.source.instrument.binding_id,
            timeframe=request.source.timeframe,
            source_rule_identity=request.context.rule_identity,
            value=SemanticValue(SemanticValueKind.TEXT, text_value="target"),
        )
        return CandidateRuleResult(SemanticRuleState.SUCCESS, (), (candidate,))

    adapter, context, inputs, profile, policy, calls = _fixture(
        {"target-source": text_targets}, {"no_target_extension": True}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "confidence-source" not in tuple(name for name, _ in calls)


def test_rule_integrity_exception_and_invalid_public_arguments_are_sanitized():
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"direction-alternate": DataIntegrityError("private payload")}
    )
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert "private" not in repr(result.diagnostics)
    assert "entry-source" not in tuple(name for name, _ in calls)

    adapter, context, inputs, profile, policy, calls = _fixture()
    result = adapter.adapt(object(), inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert calls == []


@pytest.mark.parametrize("mode", ("mismatch", "omitted"))
def test_p01_primary_payload_must_match_typed_primary_source(mode):
    adapter, context, inputs, profile, policy, calls = _fixture(options={"p01_primary_mode": mode})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.INVALID_INPUT and result.bundle is None
    assert calls == []


def test_successful_empty_direction_extraction_is_governed_as_no_match():
    empty = CandidateRuleResult(SemanticRuleState.SUCCESS, (), ())
    adapter, context, inputs, profile, policy, calls = _fixture({"direction-alternate": empty})
    result = adapter.adapt(context, inputs, profile, policy)
    assert result.state is FactAdapterState.REJECTED and result.bundle is None
    assert result.diagnostics[-1].code is RuntimeDiagnosticCode.MISSING_FACT
    assert "entry-source" not in tuple(name for name, _ in calls)
