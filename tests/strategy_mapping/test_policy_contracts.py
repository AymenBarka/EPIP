# mypy: disable-error-code="arg-type,var-annotated,type-var,attr-defined"
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole
from epip.strategy_runtime.profile import StrategyProfile


def test_closed_vocabularies_are_exact() -> None:
    assert [item.value for item in AnalyticalSourceKind] == [
        "SWING",
        "MARKET_STRUCTURE",
        "LIQUIDITY",
        "FIBONACCI",
        "MARKET_CONTEXT",
        "ELLIOTT",
        "DECISION",
        "KERNEL",
    ]
    assert len(SourceSelectorKind) == 9
    assert len(NonAcceptanceAction) == 4
    assert len(DirectionFactName) == 6
    assert len(ConfidenceModelKind) == 4
    assert len(EvidenceRequirement) == len(FreshnessBasis) == 2


def test_rule_identity_is_immutable_hashable_and_valid(rule: RuleIdentity) -> None:
    assert hash(rule) and rule.reference.endswith("#" + "a" * 64)
    with pytest.raises(FrozenInstanceError):
        rule.rule_id = "changed"  # type: ignore[misc]
    for kwargs in ({"rule_id": ""}, {"rule_schema_version": "bad"}, {"fingerprint": "bad"}):
        with pytest.raises(DataIntegrityError):
            replace(rule, **kwargs)


def test_source_selector_validation(rule: RuleIdentity, selector: SourceSelector) -> None:
    assert selector.canonical_key()[0] == "SWING"
    for kwargs in (
        {"source_kind": "SWING"},
        {"source_contract": ""},
        {"selector_kind": "DIRECT_ENUM"},
        {"selector_rule": object()},
        {"required_provenance": 1},
        {"required_provenance": False},
    ):
        with pytest.raises(DataIntegrityError):
            replace(selector, **kwargs)


def test_direction_policy_shapes(rule: RuleIdentity, selector: SourceSelector) -> None:
    mapping = EnumDirectionMapping("UP", StrategyDirection.BUY)
    policy = DirectionFactPolicy(
        DirectionFactName.PRIMARY,
        selector,
        ("B", "A"),
        (mapping,),
        None,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
    )
    assert policy.allowed_source_states == ("A", "B")
    with pytest.raises(DataIntegrityError):
        EnumDirectionMapping("UP", "BUY")
    failures = (
        {"fact_name": "PRIMARY"},
        {"selector": object()},
        {"allowed_source_states": ()},
        {"enum_mappings": []},
        {"enum_mappings": (mapping, mapping)},
        {"missing_action": "REJECT"},
    )
    for kwargs in failures:
        with pytest.raises(DataIntegrityError):
            replace(policy, **kwargs)
    indirect = replace(selector, selector_kind=SourceSelectorKind.HYPOTHESIS_RULE)
    with pytest.raises(DataIntegrityError):
        replace(policy, selector=indirect, enum_mappings=(), strategy_rule=None)
    assert replace(policy, selector=indirect, enum_mappings=(), strategy_rule=rule)


def test_mtf_direction_policy_validation(rule: RuleIdentity) -> None:
    obj = MtfDirectionPolicyRef(
        (TimeframeRole.PRIMARY, TimeframeRole.HIGHER),
        ("H4", "H1"),
        DirectionFactName.PRIMARY,
        rule,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
    )
    assert obj.required_timeframes == ("H1", "H4")
    for kwargs in (
        {"required_roles": [TimeframeRole.PRIMARY]},
        {"required_roles": ()},
        {"required_roles": (TimeframeRole.HIGHER,)},
        {"required_roles": (TimeframeRole.PRIMARY,) * 2},
        {"required_timeframes": ()},
        {"frame_direction_fact": DirectionFactName.MTF},
        {"frame_direction_fact": "PRIMARY"},
        {"rule_identity": object()},
        {"conflict_action": "x"},
    ):
        with pytest.raises(DataIntegrityError):
            replace(obj, **kwargs)


def test_geometry_policies_and_ordering(
    policies: dict[str, object], selector: SourceSelector
) -> None:
    for name in ("entry", "stop", "target"):
        obj = policies[name]
        assert hash(obj)
        for kwargs in (
            {"allowed_selectors": ()},
            {"allowed_selectors": (selector, selector)},
            {"candidate_selector": object()},
            {"require_provenance": False},
            {"missing_action": "REJECT"},
        ):
            with pytest.raises(DataIntegrityError):
                replace(obj, **kwargs)
    with pytest.raises(DataIntegrityError):
        replace(policies["entry"], ranking_rule=object())
    with pytest.raises(DataIntegrityError):
        replace(policies["stop"], buffer_rule=object())
    with pytest.raises(DataIntegrityError):
        replace(policies["stop"], volatility_adjustment_rule=object())
    with pytest.raises(DataIntegrityError):
        replace(policies["target"], extension_rule=object())


def test_confidence_contract_variants(rule: RuleIdentity, selector: SourceSelector) -> None:
    item = ConfidenceInput("b", selector, True)
    other = ConfidenceInput("a", selector, False)
    parameter = ModelParameter("weight", 0.5)
    base = ConfidencePolicy(
        rule,
        ConfidenceModelKind.DIRECT,
        rule,
        (item,),
        (parameter,),
        None,
        0.0,
        1.0,
        NonAcceptanceAction.REJECT,
        NonAcceptanceAction.REQUIRE_SINGLE,
    )
    for kind in (ConfidenceModelKind.WEIGHTED, ConfidenceModelKind.RULE):
        assert replace(base, model_kind=kind, inputs=(item, other)).inputs[0].input_key == "a"
    assert replace(base, model_kind=ConfidenceModelKind.CALIBRATED, calibration_identity=rule)
    for kwargs in (
        {"model_kind": "DIRECT"},
        {"inputs": ()},
        {"inputs": (item, item)},
        {"parameters": []},
        {"parameters": (parameter, parameter)},
        {"output_min": 0.1},
        {"output_max": float("inf")},
        {"calibration_identity": rule},
    ):
        with pytest.raises(DataIntegrityError):
            replace(base, **kwargs)
    with pytest.raises(DataIntegrityError):
        replace(base, inputs=(item, other))
    with pytest.raises(DataIntegrityError):
        ModelParameter("x", float("nan"))


def test_evidence_contracts(policies: dict[str, object], rule: RuleIdentity) -> None:
    taxonomy = policies["evidence"]
    key = taxonomy.keys[0]
    assert key.freshness_policy.max_age_seconds == 60
    for obj, kwargs in (
        (key.freshness_policy, {"max_age_seconds": -1}),
        (key.temporal_eligibility_policy, {"required_timeframe_roles": ()}),
        (key.temporal_eligibility_policy, {"validity_rule": object()}),
        (
            key.temporal_eligibility_policy,
            {"required_timeframe_roles": (TimeframeRole.PRIMARY,) * 2},
        ),
        (key.temporal_eligibility_policy, {"required_timeframe_roles": [TimeframeRole.PRIMARY]}),
        (key, {"require_provenance": False}),
        (key, {"requirement": "REQUIRED"}),
        (taxonomy, {"keys": ()}),
        (taxonomy, {"keys": (key, key)}),
        (taxonomy, {"ordering_rule": object()}),
    ):
        with pytest.raises(DataIntegrityError):
            replace(obj, **kwargs)


def test_semantic_profile_identity_and_fingerprint(
    semantic_profile: StrategySemanticMappingProfile,
) -> None:
    same = StrategySemanticMappingProfile.create(
        semantic_profile_id="semantic",
        semantic_profile_version="1",
        parent_profile=semantic_profile.parent_profile,
        direction_policies=tuple(reversed(semantic_profile.direction_policies)),
        mtf_direction_policy=semantic_profile.mtf_direction_policy,
        entry_policy=semantic_profile.entry_policy,
        stop_policy=semantic_profile.stop_policy,
        target_policy=semantic_profile.target_policy,
        confidence_policy=semantic_profile.confidence_policy,
        evidence_taxonomy=semantic_profile.evidence_taxonomy,
        global_conflict_action=semantic_profile.global_conflict_action,
    )
    assert same == semantic_profile and hash(same.identity)
    assert semantic_profile.identity.reference == "semantic@1"
    with pytest.raises(DataIntegrityError):
        replace(
            semantic_profile,
            identity=replace(semantic_profile.identity, fingerprint="0" * 64),
        )
    with pytest.raises(DataIntegrityError):
        replace(semantic_profile, direction_policies=semantic_profile.direction_policies[:-1])
    with pytest.raises(DataIntegrityError):
        replace(semantic_profile, direction_policies=[])
    with pytest.raises(DataIntegrityError):
        replace(
            semantic_profile,
            identity=replace(
                semantic_profile.identity,
                parent_profile_identity=replace(
                    semantic_profile.parent_profile.identity, profile_id="other"
                ),
            ),
        )
    with pytest.raises(DataIntegrityError):
        replace(semantic_profile, global_conflict_action=NonAcceptanceAction.NO_FACT)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mapping_rules_reference", "wrong"),
        ("confidence_model_reference", "wrong"),
        ("evidence_taxonomy_reference", "wrong"),
        ("mtf_requirement", "wrong"),
        ("required_evidence_keys", ("wrong",)),
    ],
)
def test_semantic_profile_rejects_parent_reference_mismatch(
    semantic_profile: StrategySemanticMappingProfile, field: str, value: object
) -> None:
    old = semantic_profile.parent_profile
    values = {
        name: getattr(old, name)
        for name in old.__dataclass_fields__
        if name not in {"identity", "strategy_identity"}
    }
    values[field] = value
    parent = StrategyProfile.create(
        profile_id=old.identity.profile_id,
        profile_version=old.identity.profile_version,
        strategy_identity=old.strategy_identity,
        **values,
    )
    with pytest.raises(DataIntegrityError):
        StrategySemanticMappingProfile.create(
            semantic_profile_id="semantic",
            semantic_profile_version="1",
            parent_profile=parent,
            direction_policies=semantic_profile.direction_policies,
            mtf_direction_policy=semantic_profile.mtf_direction_policy,
            entry_policy=semantic_profile.entry_policy,
            stop_policy=semantic_profile.stop_policy,
            target_policy=semantic_profile.target_policy,
            confidence_policy=semantic_profile.confidence_policy,
            evidence_taxonomy=semantic_profile.evidence_taxonomy,
            global_conflict_action=semantic_profile.global_conflict_action,
        )
