# mypy: disable-error-code="arg-type,no-untyped-def"
from __future__ import annotations

from dataclasses import replace

import pytest

from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.strategy_mapping import *
from epip.strategy_runtime._base import CONTRACT_VERSION
from epip.strategy_runtime.mtf import TimeframeRole
from epip.strategy_runtime.profile import StrategyProfile


@pytest.fixture
def rule() -> RuleIdentity:
    return RuleIdentity("rule", "1", FOUNDATION_SCHEMA_VERSION, "a" * 64)


@pytest.fixture
def selector(rule: RuleIdentity) -> SourceSelector:
    return SourceSelector(
        AnalyticalSourceKind.SWING,
        "epip.swing.models.SwingSequence",
        SourceSelectorKind.DIRECT_ENUM,
        rule,
        True,
    )


@pytest.fixture
def policies(rule: RuleIdentity, selector: SourceSelector) -> dict[str, object]:
    actions = (NonAcceptanceAction.REJECT, NonAcceptanceAction.REQUIRE_SINGLE)
    directions = tuple(
        DirectionFactPolicy(
            name,
            selector,
            ("VALID",),
            (EnumDirectionMapping("UP", StrategyDirection.BUY),),
            None,
            *actions,
        )
        for name in (
            DirectionFactName.ELLIOTT,
            DirectionFactName.TREND,
            DirectionFactName.STRUCTURE,
            DirectionFactName.PRIMARY,
            DirectionFactName.ALTERNATE,
        )
    )
    common = (rule, (selector,), rule)
    entry = EntrySourcePolicy(*common, rule, rule, rule, *actions, True)
    stop = StopSourcePolicy(*common, rule, rule, None, rule, *actions, True)
    target = TargetSourcePolicy(*common, rule, None, None, rule, *actions, True)
    confidence = ConfidencePolicy(
        rule,
        ConfidenceModelKind.DIRECT,
        rule,
        (ConfidenceInput("score", selector, True),),
        (),
        None,
        0.0,
        1.0,
        *actions,
    )
    freshness = FreshnessPolicy(rule, FreshnessBasis.AVAILABILITY, 60, actions[0])
    temporal = TemporalEligibilityPolicy(rule, (TimeframeRole.PRIMARY,), rule, rule, actions[0])
    evidence = EvidenceTaxonomy(
        rule,
        (
            EvidenceKeyPolicy(
                "key", EvidenceRequirement.REQUIRED, selector, rule, freshness, temporal, True
            ),
        ),
        *actions,
        rule,
    )
    mtf = MtfDirectionPolicyRef((TimeframeRole.PRIMARY,), ("H1",), rule, *actions)
    return {
        "directions": directions,
        "entry": entry,
        "stop": stop,
        "target": target,
        "confidence": confidence,
        "evidence": evidence,
        "mtf": mtf,
    }


@pytest.fixture
def semantic_profile(policies: dict[str, object]) -> StrategySemanticMappingProfile:
    confidence = policies["confidence"]
    evidence = policies["evidence"]
    mtf = policies["mtf"]
    assert isinstance(confidence, ConfidencePolicy)
    assert isinstance(evidence, EvidenceTaxonomy)
    assert isinstance(mtf, MtfDirectionPolicyRef)
    parent = StrategyProfile.create(
        profile_id="parent",
        profile_version="1",
        strategy_identity=StrategyIdentity("strategy", "1"),
        compatible_runtime_contract_versions=(CONTRACT_VERSION,),
        compatible_adapter_contract_versions=(FOUNDATION_SCHEMA_VERSION,),
        required_source_domains=("SWING",),
        optional_source_domains=(),
        required_evidence_keys=("key",),
        optional_evidence_keys=(),
        enabled_direction_facts=("PRIMARY",),
        enabled_geometry_sources=("SWING",),
        confidence_model_reference=confidence.policy_identity.reference,
        evidence_taxonomy_reference=evidence.taxonomy_identity.reference,
        mtf_requirement=mtf.rule_identity.reference,
        mapping_rules_reference="semantic@1",
    )
    return StrategySemanticMappingProfile.create(
        semantic_profile_id="semantic",
        semantic_profile_version="1",
        parent_profile=parent,
        direction_policies=policies["directions"],
        mtf_direction_policy=mtf,
        entry_policy=policies["entry"],
        stop_policy=policies["stop"],
        target_policy=policies["target"],
        confidence_policy=confidence,
        evidence_taxonomy=evidence,
        global_conflict_action=NonAcceptanceAction.REJECT,
    )


@pytest.fixture
def changed():
    return replace
