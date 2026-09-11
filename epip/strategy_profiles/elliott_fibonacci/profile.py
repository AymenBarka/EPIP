"""Immutable P04-F00 profile and declaration foundation; no rule execution."""

from __future__ import annotations

import json
from hashlib import sha256
from types import MappingProxyType

from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.strategy_mapping import (
    EXECUTION_SCHEMA_VERSION,
    FOUNDATION_SCHEMA_VERSION,
    AnalyticalSourceKind,
    ConfidenceInput,
    ConfidenceModelKind,
    ConfidencePolicy,
    DirectionFactName,
    DirectionFactPolicy,
    EntrySourcePolicy,
    EnumDirectionMapping,
    EvidenceKeyPolicy,
    EvidenceRequirement,
    EvidenceTaxonomy,
    FreshnessBasis,
    FreshnessPolicy,
    ModelParameter,
    MtfDirectionPolicyRef,
    NonAcceptanceAction,
    RuleIdentity,
    SemanticInvocationKind,
    SemanticResultKind,
    SemanticRuleCatalog,
    SemanticRuleCatalogEntry,
    SemanticRuleCatalogState,
    SemanticRuleFamily,
    SourceSelector,
    SourceSelectorKind,
    StopSourcePolicy,
    StrategySemanticMappingProfile,
    TargetSourcePolicy,
    TemporalEligibilityPolicy,
)
from epip.strategy_profiles.elliott_fibonacci.configuration import (
    ELLIOTT_WEIGHT,
    ENTRY_RATIOS,
    EVIDENCE_KEYS,
    EXPIRATION_SECONDS,
    FIBONACCI_WEIGHT,
    MINIMUM_CONFIDENCE,
    MINIMUM_RR,
    NUMERIC_PRECISION,
    PROFILE_ID,
    PROFILE_REFERENCE,
    PROFILE_VERSION,
    REQUIRED_SOURCE_DOMAINS,
    TARGET_RATIO,
)
from epip.strategy_runtime._base import CONTRACT_VERSION
from epip.strategy_runtime.mtf import TimeframeRole
from epip.strategy_runtime.profile import StrategyProfile

_PREFIX = "p04.elliott-fibonacci-wave3."

_FAMILY_SUFFIXES = {
    SemanticRuleFamily.SOURCE_EXTRACTION: (
        "extract.elliott",
        "extract.fibonacci",
        "extract.market-structure",
    ),
    SemanticRuleFamily.APPLICABILITY: (
        "applicability.elliott-wave3",
        "applicability.fibonacci-wave3",
        "applicability.direction",
        "applicability.entry",
        "applicability.stop",
        "applicability.target",
        "invalidation.wave3",
    ),
    SemanticRuleFamily.CANDIDATE_SELECTION: (
        "select.wave1-anchor",
        "select.entry",
        "select.stop",
        "select.target",
    ),
    SemanticRuleFamily.CANDIDATE_RANKING: (
        "rank.entry-golden-zone",
        "rank.target-extension-1618",
    ),
    SemanticRuleFamily.BOUNDARY_SELECTION: ("boundary.entry-0618-0705",),
    SemanticRuleFamily.PRECEDENCE: ("precedence.stop-wave1-origin",),
    SemanticRuleFamily.PRICE_TRANSFORMATION: (
        "transform.stop-identity",
        "transform.target-extension-1618",
    ),
    SemanticRuleFamily.DIRECTION_MAPPING: (
        "direction.elliott",
        "direction.trend",
        "direction.structure",
        "direction.primary",
        "direction.alternate",
    ),
    SemanticRuleFamily.MTF_AGGREGATION: ("direction.caller-primary-identity",),
    SemanticRuleFamily.CONFIDENCE: ("confidence.elliott-fibonacci-60-40",),
    SemanticRuleFamily.TEMPORAL_ELIGIBILITY: (
        "evidence.validity",
        "evidence.revision",
    ),
    SemanticRuleFamily.EVIDENCE_MAPPING: tuple(
        f"evidence.{key.replace('.', '-').replace('_', '-')}" for key in EVIDENCE_KEYS
    ),
    SemanticRuleFamily.EVIDENCE_ORDERING: ("evidence.ordering",),
}

_INVOCATION_RESULT = {
    SemanticRuleFamily.SOURCE_EXTRACTION: (
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
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
    SemanticRuleFamily.DIRECTION_MAPPING: (
        SemanticInvocationKind.DIRECTION,
        SemanticResultKind.DIRECTION,
    ),
    SemanticRuleFamily.MTF_AGGREGATION: (
        SemanticInvocationKind.MTF_AGGREGATION,
        SemanticResultKind.MTF_AGGREGATION,
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
}


def _semantics(suffix: str) -> tuple[str, ...]:
    clauses = [f"operation={suffix}"]
    if "elliott" in suffix or "wave" in suffix:
        clauses.append(
            "valid contiguous same-degree WAVE_1/WAVE_2; zero violations; empty alternates; next WAVE_3"
        )
    if "fibonacci" in suffix or "anchor" in suffix:
        clauses.append("Fibonacci anchors equal ordered WAVE_1 start/end")
    if suffix.startswith("direction."):
        clauses.append("closed UP/DOWN and UPTREND/DOWNTREND direction mapping")
    if "entry" in suffix:
        clauses.append(f"inclusive entry ratios {ENTRY_RATIOS[0]} and {ENTRY_RATIOS[1]}")
    if "stop" in suffix:
        clauses.append("WAVE_1 origin identity stop")
    if "target" in suffix:
        clauses.append(f"direction-aware target extension {TARGET_RATIO}")
    if "confidence" in suffix:
        clauses.append(f"confidence {ELLIOTT_WEIGHT} Elliott plus {FIBONACCI_WEIGHT} Fibonacci")
    if suffix.startswith("evidence."):
        clauses.append("required availability freshness zero seconds on PRIMARY")
    if suffix == "evidence.ordering":
        clauses.extend(EVIDENCE_KEYS)
    return tuple(clauses)


def _identity(family: SemanticRuleFamily, suffix: str) -> RuleIdentity:
    rule_id = f"{_PREFIX}{suffix}"
    payload = {
        "domain": "epip.p04.semantic-rule.v1",
        "family": family.value,
        "profile": PROFILE_REFERENCE,
        "rule_id": rule_id,
        "rule_version": PROFILE_VERSION,
        "semantics": list(_semantics(suffix)),
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return RuleIdentity(
        rule_id, PROFILE_VERSION, FOUNDATION_SCHEMA_VERSION, sha256(encoded.encode()).hexdigest()
    )


_RULES = {
    suffix: _identity(family, suffix)
    for family, suffixes in _FAMILY_SUFFIXES.items()
    for suffix in suffixes
}
RULE_IDENTITIES = MappingProxyType(_RULES)


def _selector(
    source: AnalyticalSourceKind,
    contract: str,
    kind: SourceSelectorKind,
) -> SourceSelector:
    suffix = {
        AnalyticalSourceKind.ELLIOTT: "extract.elliott",
        AnalyticalSourceKind.FIBONACCI: "extract.fibonacci",
        AnalyticalSourceKind.MARKET_STRUCTURE: "extract.market-structure",
    }[source]
    return SourceSelector(source, contract, kind, _RULES[suffix], True, (TimeframeRole.PRIMARY,))


_ELLIOTT = _selector(
    AnalyticalSourceKind.ELLIOTT,
    "epip.elliott.models.WaveSnapshot",
    SourceSelectorKind.ELLIOTT_COUNT_RULE,
)
_FIBONACCI = _selector(
    AnalyticalSourceKind.FIBONACCI,
    "epip.fibonacci.models.FibonacciSnapshot",
    SourceSelectorKind.ZONE_CANDIDATES,
)
_STRUCTURE = _selector(
    AnalyticalSourceKind.MARKET_STRUCTURE,
    "epip.market_structure.models.MarketStructureSnapshot",
    SourceSelectorKind.DIRECT_ENUM,
)
_ACTIONS = (NonAcceptanceAction.REJECT, NonAcceptanceAction.REQUIRE_SINGLE)
_DIRECTION_MAPPINGS = (
    EnumDirectionMapping("ACCUMULATION", StrategyDirection.NO_TRADE),
    EnumDirectionMapping("DISTRIBUTION", StrategyDirection.NO_TRADE),
    EnumDirectionMapping("DOWNTREND", StrategyDirection.SELL),
    EnumDirectionMapping("RANGE", StrategyDirection.NO_TRADE),
    EnumDirectionMapping("UNKNOWN", StrategyDirection.NO_TRADE),
    EnumDirectionMapping("UPTREND", StrategyDirection.BUY),
)

_DIRECTION_POLICIES = (
    DirectionFactPolicy(
        DirectionFactName.ELLIOTT,
        _ELLIOTT,
        ("DOWN", "UP"),
        (),
        _RULES["direction.elliott"],
        *_ACTIONS,
    ),
    DirectionFactPolicy(
        DirectionFactName.TREND,
        _STRUCTURE,
        tuple(item.source_value for item in _DIRECTION_MAPPINGS),
        _DIRECTION_MAPPINGS,
        None,
        *_ACTIONS,
    ),
    DirectionFactPolicy(
        DirectionFactName.STRUCTURE,
        _STRUCTURE,
        tuple(item.source_value for item in _DIRECTION_MAPPINGS),
        _DIRECTION_MAPPINGS,
        None,
        *_ACTIONS,
    ),
    DirectionFactPolicy(
        DirectionFactName.PRIMARY,
        _ELLIOTT,
        ("DOWN", "UP"),
        (),
        _RULES["direction.primary"],
        *_ACTIONS,
    ),
    DirectionFactPolicy(
        DirectionFactName.ALTERNATE,
        _ELLIOTT,
        ("DOWN", "UP"),
        (),
        _RULES["direction.alternate"],
        *_ACTIONS,
    ),
)

_MTF = MtfDirectionPolicyRef(
    (TimeframeRole.PRIMARY,),
    (),
    DirectionFactName.PRIMARY,
    _RULES["direction.caller-primary-identity"],
    *_ACTIONS,
    bind_primary_timeframe=True,
)
_ENTRY = EntrySourcePolicy(
    _RULES["applicability.entry"],
    (_FIBONACCI,),
    _RULES["select.entry"],
    _RULES["rank.entry-golden-zone"],
    _RULES["boundary.entry-0618-0705"],
    _RULES["applicability.entry"],
    *_ACTIONS,
    True,
)
_STOP = StopSourcePolicy(
    _RULES["applicability.stop"],
    (_ELLIOTT,),
    _RULES["select.stop"],
    _RULES["precedence.stop-wave1-origin"],
    _RULES["transform.stop-identity"],
    None,
    _RULES["applicability.stop"],
    *_ACTIONS,
    True,
)
_TARGET = TargetSourcePolicy(
    _RULES["applicability.target"],
    (_FIBONACCI,),
    _RULES["select.target"],
    _RULES["rank.target-extension-1618"],
    _RULES["applicability.target"],
    None,
    _RULES["applicability.target"],
    *_ACTIONS,
    True,
)
_CONFIDENCE = ConfidencePolicy(
    _RULES["confidence.elliott-fibonacci-60-40"],
    ConfidenceModelKind.WEIGHTED,
    _RULES["confidence.elliott-fibonacci-60-40"],
    (
        ConfidenceInput("elliott_primary_probability", _ELLIOTT, True),
        ConfidenceInput("fibonacci_confluence_score", _FIBONACCI, True),
    ),
    (
        ModelParameter("elliott_weight", ELLIOTT_WEIGHT),
        ModelParameter("fibonacci_weight", FIBONACCI_WEIGHT),
    ),
    None,
    0.0,
    1.0,
    *_ACTIONS,
)


def _evidence_selector(key: str) -> SourceSelector:
    if key.startswith(("elliott.", "stop.")):
        return _ELLIOTT
    if key.startswith(("fibonacci.", "entry.", "target.", "confidence.")):
        return _FIBONACCI
    return _STRUCTURE


_FRESHNESS = FreshnessPolicy(
    _RULES["evidence.validity"], FreshnessBasis.AVAILABILITY, 0, NonAcceptanceAction.REJECT
)
_TEMPORAL = TemporalEligibilityPolicy(
    _RULES["evidence.validity"],
    (TimeframeRole.PRIMARY,),
    _RULES["evidence.validity"],
    _RULES["evidence.revision"],
    NonAcceptanceAction.REJECT,
)
_EVIDENCE = EvidenceTaxonomy(
    _RULES["evidence.ordering"],
    tuple(
        EvidenceKeyPolicy(
            key,
            EvidenceRequirement.REQUIRED,
            _evidence_selector(key),
            _RULES[f"evidence.{key.replace('.', '-').replace('_', '-')}"],
            _FRESHNESS,
            _TEMPORAL,
            True,
        )
        for key in EVIDENCE_KEYS
    ),
    NonAcceptanceAction.REJECT,
    NonAcceptanceAction.REQUIRE_SINGLE,
    _RULES["evidence.ordering"],
)

_STRATEGY_IDENTITY = StrategyIdentity(PROFILE_ID, PROFILE_VERSION)
POLICY = StrategyPolicy(
    PROFILE_ID,
    PROFILE_VERSION,
    _STRATEGY_IDENTITY,
    (StrategyDirection.BUY, StrategyDirection.SELL),
    MINIMUM_RR,
    MINIMUM_CONFIDENCE,
    EVIDENCE_KEYS,
    (),
    EXPIRATION_SECONDS,
    NUMERIC_PRECISION,
    (
        ("alternates", "empty"),
        ("primary_status", "VALID"),
        ("projection_next_wave", "WAVE_3"),
        ("sequence", "WAVE_1,WAVE_2"),
        ("violations", "empty"),
    ),
)
PROFILE = StrategyProfile.create(
    profile_id=PROFILE_ID,
    profile_version=PROFILE_VERSION,
    strategy_identity=_STRATEGY_IDENTITY,
    compatible_runtime_contract_versions=(CONTRACT_VERSION,),
    compatible_adapter_contract_versions=(FOUNDATION_SCHEMA_VERSION,),
    required_source_domains=REQUIRED_SOURCE_DOMAINS,
    optional_source_domains=(),
    required_evidence_keys=tuple(sorted(EVIDENCE_KEYS)),
    optional_evidence_keys=(),
    enabled_direction_facts=tuple(sorted(item.value for item in DirectionFactName)),
    enabled_geometry_sources=("ELLIOTT", "FIBONACCI"),
    confidence_model_reference=_CONFIDENCE.policy_identity.reference,
    evidence_taxonomy_reference=_EVIDENCE.taxonomy_identity.reference,
    mtf_requirement=_MTF.rule_identity.reference,
    mapping_rules_reference=PROFILE_REFERENCE,
)
SEMANTIC_PROFILE = StrategySemanticMappingProfile.create(
    semantic_profile_id=PROFILE_ID,
    semantic_profile_version=PROFILE_VERSION,
    parent_profile=PROFILE,
    direction_policies=_DIRECTION_POLICIES,
    mtf_direction_policy=_MTF,
    entry_policy=_ENTRY,
    stop_policy=_STOP,
    target_policy=_TARGET,
    confidence_policy=_CONFIDENCE,
    evidence_taxonomy=_EVIDENCE,
    global_conflict_action=NonAcceptanceAction.REJECT,
)

_STRUCTURAL_APPLICABILITY_RULES = frozenset(
    {"applicability.elliott-wave3", "applicability.fibonacci-wave3"}
)

_CATALOG_ENTRIES = tuple(
    SemanticRuleCatalogEntry(
        _RULES[suffix],
        family,
        (
            SemanticInvocationKind.STRUCTURAL_APPLICABILITY
            if suffix in _STRUCTURAL_APPLICABILITY_RULES
            else _INVOCATION_RESULT[family][0]
        ),
        _INVOCATION_RESULT[family][1],
        SemanticRuleCatalogState.DECLARATION_ONLY,
    )
    for family, suffixes in _FAMILY_SUFFIXES.items()
    for suffix in suffixes
)
RULE_CATALOG = SemanticRuleCatalog.create(_CATALOG_ENTRIES)

# P04-F00 has declarations but no authorized implementations. P02 manifests
# are non-empty executable closures, so absence represents the exact empty
# executable closure without manufacturing implementation bindings.
RULE_MANIFEST = None

assert RULE_CATALOG.schema_version == EXECUTION_SCHEMA_VERSION

__all__ = [
    "POLICY",
    "PROFILE",
    "RULE_CATALOG",
    "RULE_IDENTITIES",
    "RULE_MANIFEST",
    "SEMANTIC_PROFILE",
]
