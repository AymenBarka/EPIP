# mypy: disable-error-code="no-untyped-def,no-untyped-call,arg-type,type-arg,assignment,var-annotated"
from __future__ import annotations

from dataclasses import dataclass

from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
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


def _fixture(outcomes=None):
    calls = []
    outcomes = {} if outcomes is None else outcomes
    identities = {}
    families = {}

    def rid(name, family):
        identities[name] = _id(name)
        families[name] = family
        return identities[name]

    primary = (TimeframeRole.PRIMARY,)
    both = (TimeframeRole.PRIMARY, TimeframeRole.HIGHER)

    def selector(name, roles=primary):
        return SourceSelector(
            AnalyticalSourceKind.SWING,
            "epip.swing.models.SwingSequence",
            (
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
            ),
            ("VALID",),
            (EnumDirectionMapping("UP", StrategyDirection.BUY),),
            None,
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
    entry = EntrySourcePolicy(
        _id("entry-policy"),
        (selector("entry-source"),),
        choose,
        rid("entry-rank", SemanticRuleFamily.CANDIDATE_RANKING),
        rid("boundary", SemanticRuleFamily.BOUNDARY_SELECTION),
        app,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        True,
    )
    stop = StopSourcePolicy(
        _id("stop-policy"),
        (selector("stop-source"),),
        choose,
        rid("precedence", SemanticRuleFamily.PRECEDENCE),
        rid("buffer", SemanticRuleFamily.PRICE_TRANSFORMATION),
        None,
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
        rid("extension", SemanticRuleFamily.CANDIDATE_SELECTION),
        app,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
        True,
    )
    confidence_primary = selector("confidence-source", primary)
    confidence_higher = selector("confidence-source", (TimeframeRole.HIGHER,))
    confidence = ConfidencePolicy(
        _id("confidence-policy"),
        ConfidenceModelKind.WEIGHTED,
        rid("confidence-model", SemanticRuleFamily.CONFIDENCE),
        (
            ConfidenceInput("alpha", confidence_primary, True),
            ConfidenceInput("beta", confidence_higher, True),
        ),
        (),
        None,
        0.0,
        1.0,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
    )
    fresh = FreshnessPolicy(
        _id("fresh"), FreshnessBasis.OBSERVATION, 7200, NonAcceptanceAction.REJECT
    )
    temporal = TemporalEligibilityPolicy(
        _id("temporal"),
        both,
        rid("validity", SemanticRuleFamily.TEMPORAL_ELIGIBILITY),
        rid("revision", SemanticRuleFamily.TEMPORAL_ELIGIBILITY),
        NonAcceptanceAction.REJECT,
    )
    evidence = EvidenceTaxonomy(
        _id("taxonomy"),
        tuple(
            EvidenceKeyPolicy(
                key,
                EvidenceRequirement.REQUIRED,
                selector("evidence-" + key, both if key == "alpha" else primary),
                rid("map-" + key, SemanticRuleFamily.EVIDENCE_MAPPING),
                fresh,
                temporal,
                True,
            )
            for key in ("alpha", "zeta")
        ),
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
        required_evidence_keys=("alpha", "zeta"),
        optional_evidence_keys=(),
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
        ("alpha", "zeta"),
        (),
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
            observation_timestamp="2026-01-01T09:30:00Z",
            availability_timestamp="2026-01-01T09:30:01Z",
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
    inputs = AnalyticalInputBundle(
        sources[0].payload, None, None, None, None, None, None, None, coherence, manifest
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
    assert "validity" not in tuple(name for name, _ in calls)
    adapter, context, inputs, profile, policy, calls = _fixture(
        {"validity": TemporalEligibilityResult(SemanticRuleState.SUCCESS, (), False)}
    )
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.REJECTED
    assert "revision" not in tuple(name for name, _ in calls)


def test_evidence_ordering_requires_exact_permutation():
    adapter, context, inputs, profile, policy, _ = _fixture(
        {"evidence-order": EvidenceOrderingResult(SemanticRuleState.SUCCESS, (), ("alpha",))}
    )
    assert adapter.adapt(context, inputs, profile, policy).state is FactAdapterState.INVALID_INPUT
