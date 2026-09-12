from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from epip.a07.foundation import StrategyDirection
from epip.strategy_mapping import (
    FOUNDATION_SCHEMA_VERSION,
    FreshnessBasis,
    NonAcceptanceAction,
    SemanticInvocationKind,
    SemanticRuleCatalog,
    SemanticRuleCatalogState,
    SemanticRuleFamily,
    StrategySemanticMappingProfile,
    from_json,
    to_json,
)
from epip.strategy_profiles.elliott_fibonacci import (
    EVIDENCE_KEYS,
    POLICY,
    PROFILE,
    RULE_CATALOG,
    RULE_IDENTITIES,
    RULE_MANIFEST,
    RULE_SET,
    SEMANTIC_PROFILE,
)
from epip.strategy_profiles.elliott_fibonacci.configuration import (
    ELLIOTT_WEIGHT,
    ENTRY_RATIOS,
    EXPIRATION_SECONDS,
    FIBONACCI_WEIGHT,
    MINIMUM_CONFIDENCE,
    MINIMUM_RR,
    PROFILE_ID,
    PROFILE_VERSION,
    REQUIRED_SOURCE_DOMAINS,
    TARGET_RATIO,
)
from epip.strategy_runtime._base import CONTRACT_VERSION
from epip.strategy_runtime.mtf import TimeframeRole


def _mutate(instance: object, field: str, value: object) -> None:
    setattr(instance, field, value)


def test_exact_configuration_and_parent_policy() -> None:
    assert (PROFILE_ID, PROFILE_VERSION) == ("elliott-fibonacci-wave3", "1.0.0")
    assert ENTRY_RATIOS == (0.618, 0.705)
    assert TARGET_RATIO == 1.618
    assert (MINIMUM_RR, MINIMUM_CONFIDENCE) == (3.0, 0.70)
    assert (ELLIOTT_WEIGHT, FIBONACCI_WEIGHT) == (0.60, 0.40)
    assert EXPIRATION_SECONDS == 300
    assert REQUIRED_SOURCE_DOMAINS == ("ELLIOTT", "FIBONACCI", "MARKET_STRUCTURE")
    assert POLICY.strategy_identity == PROFILE.strategy_identity
    assert POLICY.enabled_directions == (StrategyDirection.BUY, StrategyDirection.SELL)
    assert POLICY.required_evidence == tuple(sorted(EVIDENCE_KEYS))
    assert POLICY.optional_evidence == ()
    assert POLICY.numeric_precision == 2


def test_profile_and_semantic_references_are_exact_and_closed() -> None:
    assert PROFILE.identity.profile_id == PROFILE_ID
    assert PROFILE.identity.profile_version == PROFILE_VERSION
    assert PROFILE.identity.contract_version == CONTRACT_VERSION
    assert PROFILE.compatible_adapter_contract_versions == (FOUNDATION_SCHEMA_VERSION,)
    assert SEMANTIC_PROFILE.parent_profile is PROFILE
    assert SEMANTIC_PROFILE.identity.semantic_profile_id == PROFILE_ID
    assert SEMANTIC_PROFILE.identity.semantic_profile_version == PROFILE_VERSION
    assert PROFILE.mapping_rules_reference == SEMANTIC_PROFILE.identity.reference
    assert PROFILE.confidence_model_reference == (
        SEMANTIC_PROFILE.confidence_policy.policy_identity.reference
    )
    assert PROFILE.evidence_taxonomy_reference == (
        SEMANTIC_PROFILE.evidence_taxonomy.taxonomy_identity.reference
    )
    assert PROFILE.mtf_requirement == SEMANTIC_PROFILE.mtf_direction_policy.rule_identity.reference
    assert {item.identity for item in RULE_CATALOG.entries} == set(RULE_IDENTITIES.values())
    assert len(RULE_MANIFEST.declarations) == 5


def test_caller_bound_primary_and_required_sources_are_exact() -> None:
    mtf = SEMANTIC_PROFILE.mtf_direction_policy
    assert mtf.bind_primary_timeframe is True
    assert mtf.required_roles == (TimeframeRole.PRIMARY,)
    assert mtf.required_timeframes == ()
    assert PROFILE.required_source_domains == tuple(sorted(REQUIRED_SOURCE_DOMAINS))
    assert PROFILE.optional_source_domains == ()
    selectors = [item.selector for item in SEMANTIC_PROFILE.direction_policies]
    selectors.extend(SEMANTIC_PROFILE.entry_policy.allowed_selectors)
    selectors.extend(SEMANTIC_PROFILE.stop_policy.allowed_selectors)
    selectors.extend(SEMANTIC_PROFILE.target_policy.allowed_selectors)
    assert all(item.frame_roles == (TimeframeRole.PRIMARY,) for item in selectors)
    assert all(item.required_provenance for item in selectors)


def test_evidence_order_freshness_and_confidence_are_governed() -> None:
    taxonomy = SEMANTIC_PROFILE.evidence_taxonomy
    assert {item.evidence_key for item in taxonomy.keys} == set(EVIDENCE_KEYS)
    assert all(item.require_provenance for item in taxonomy.keys)
    assert all(item.freshness_policy.basis is FreshnessBasis.AVAILABILITY for item in taxonomy.keys)
    assert all(item.freshness_policy.max_age_seconds == 0 for item in taxonomy.keys)
    assert all(
        item.freshness_policy.failure_action is NonAcceptanceAction.REJECT for item in taxonomy.keys
    )
    confidence = SEMANTIC_PROFILE.confidence_policy
    assert tuple(item.input_key for item in confidence.inputs) == (
        "elliott_primary_probability",
        "fibonacci_confluence_score",
    )
    assert {item.parameter_key: item.value for item in confidence.parameters} == {
        "elliott_weight": 0.60,
        "fibonacci_weight": 0.40,
    }


def test_rule_identity_inventory_and_fingerprints_are_canonical() -> None:
    assert len(RULE_IDENTITIES) == 37
    for suffix, identity in RULE_IDENTITIES.items():
        assert identity.rule_id == f"p04.elliott-fibonacci-wave3.{suffix}"
        assert identity.rule_version == "1.0.0"
        assert identity.rule_schema_version == FOUNDATION_SCHEMA_VERSION
        assert len(identity.fingerprint) == 64
        rebuilt = type(identity)(
            identity.rule_id,
            identity.rule_version,
            identity.rule_schema_version,
            identity.fingerprint,
        )
        assert identity == rebuilt
        assert hash(identity) == hash(rebuilt)
    payload = "\n".join(
        f"{suffix}={identity.reference}" for suffix, identity in RULE_IDENTITIES.items()
    )
    assert sha256(payload.encode()).hexdigest() == (
        "4312aab4d2bf321807a643a3259e25d888faa935c21cdf0f6943bf6b0031faf4"
    )
    assert {item.family for item in RULE_CATALOG.entries}.issubset(set(SemanticRuleFamily))


def test_rule_catalog_has_exact_f01_executable_closure() -> None:
    assert type(RULE_CATALOG) is SemanticRuleCatalog
    assert len(RULE_CATALOG.entries) == 37
    executable = tuple(
        item for item in RULE_CATALOG.entries if item.state is SemanticRuleCatalogState.EXECUTABLE
    )
    declared = tuple(
        item
        for item in RULE_CATALOG.entries
        if item.state is SemanticRuleCatalogState.DECLARATION_ONLY
    )
    assert len(executable) == 5 and len(declared) == 32
    assert all(item.implementation_id is not None for item in executable)
    assert all(item.implementation_id is None for item in declared)
    identities = {
        RULE_IDENTITIES[suffix]
        for suffix in (
            "extract.elliott",
            "extract.fibonacci",
            "applicability.elliott-wave3",
            "applicability.fibonacci-wave3",
            "select.wave1-anchor",
        )
    }
    assert {item.identity for item in executable} == identities
    assert {item.identity for item in RULE_MANIFEST.declarations} == identities
    assert {item.identity for item in RULE_SET.implementations} == identities


def test_f01_applicability_declarations_are_structural() -> None:
    entries = {item.identity: item for item in RULE_CATALOG.entries}
    for suffix in ("applicability.elliott-wave3", "applicability.fibonacci-wave3"):
        assert (
            entries[RULE_IDENTITIES[suffix]].invocation_kind
            is SemanticInvocationKind.STRUCTURAL_APPLICABILITY
        )
    assert all(
        item.invocation_kind is not SemanticInvocationKind.STRUCTURAL_APPLICABILITY
        for item in RULE_CATALOG.entries
        if item.identity
        not in {
            RULE_IDENTITIES["applicability.elliott-wave3"],
            RULE_IDENTITIES["applicability.fibonacci-wave3"],
        }
    )


def test_rule_catalog_serialization_is_deterministic() -> None:
    payload = to_json(RULE_CATALOG)
    assert payload == to_json(RULE_CATALOG)
    assert from_json(SemanticRuleCatalog, payload) == RULE_CATALOG


def test_objects_are_immutable_deterministic_and_serializable() -> None:
    first = to_json(SEMANTIC_PROFILE)
    assert first == to_json(SEMANTIC_PROFILE)
    assert json.loads(first)["$type"].endswith(":StrategySemanticMappingProfile")
    assert from_json(StrategySemanticMappingProfile, first) == SEMANTIC_PROFILE
    assert hash(from_json(StrategySemanticMappingProfile, first)) == hash(SEMANTIC_PROFILE)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        _mutate(PROFILE, "required_source_domains", ())
    with pytest.raises((FrozenInstanceError, AttributeError)):
        _mutate(SEMANTIC_PROFILE, "global_conflict_action", NonAcceptanceAction.NO_FACT)


def test_package_has_no_execution_or_dynamic_discovery_surface() -> None:
    package = importlib.import_module("epip.strategy_profiles.elliott_fibonacci")
    exported = set(package.__all__)
    assert exported == {
        "EVIDENCE_KEYS",
        "POLICY",
        "PROFILE",
        "RULE_CATALOG",
        "RULE_IDENTITIES",
        "RULE_MANIFEST",
        "RULE_SET",
        "SEMANTIC_PROFILE",
    }
    source = inspect.getsource(
        importlib.import_module("epip.strategy_profiles.elliott_fibonacci.profile")
    )
    forbidden = (
        "datetime.now",
        "time.time",
        "random.",
        "os.environ",
        "subprocess",
        "eval(",
        "exec(",
    )
    assert not any(value in source for value in forbidden)
    assert not any(name.endswith("Rule") for name in exported)
    assert all(dataclasses.is_dataclass(item) for item in RULE_CATALOG.entries)
