"""Typed direction-mapping policy schemas; no mapping execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import boolean, exact, text, unique_texts
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_runtime.mtf import TimeframeRole


class AnalyticalSourceKind(Enum):
    SWING = "SWING"
    MARKET_STRUCTURE = "MARKET_STRUCTURE"
    LIQUIDITY = "LIQUIDITY"
    FIBONACCI = "FIBONACCI"
    MARKET_CONTEXT = "MARKET_CONTEXT"
    ELLIOTT = "ELLIOTT"
    DECISION = "DECISION"
    KERNEL = "KERNEL"


class SourceSelectorKind(Enum):
    DIRECT_ENUM = "DIRECT_ENUM"
    DIRECT_VALUE = "DIRECT_VALUE"
    ZONE_CANDIDATES = "ZONE_CANDIDATES"
    PRICE_CANDIDATES = "PRICE_CANDIDATES"
    HYPOTHESIS_RULE = "HYPOTHESIS_RULE"
    ELLIOTT_COUNT_RULE = "ELLIOTT_COUNT_RULE"
    CONFIDENCE_INPUT = "CONFIDENCE_INPUT"
    EVIDENCE_INPUT = "EVIDENCE_INPUT"
    MTF_RULE = "MTF_RULE"


class NonAcceptanceAction(Enum):
    REJECT = "REJECT"
    NO_FACT = "NO_FACT"
    REQUIRE_SINGLE = "REQUIRE_SINGLE"
    REQUIRE_EXPLICIT_SELECTION_RULE = "REQUIRE_EXPLICIT_SELECTION_RULE"


class DirectionFactName(Enum):
    ELLIOTT = "ELLIOTT"
    TREND = "TREND"
    STRUCTURE = "STRUCTURE"
    PRIMARY = "PRIMARY"
    ALTERNATE = "ALTERNATE"
    MTF = "MTF"


_ROLE_ORDER = {
    TimeframeRole.PRIMARY: 0,
    TimeframeRole.HIGHER: 1,
    TimeframeRole.LOWER: 2,
}


@dataclass(frozen=True, slots=True)
class SourceSelector:
    source_kind: AnalyticalSourceKind
    source_contract: str
    selector_kind: SourceSelectorKind
    selector_rule: RuleIdentity
    required_provenance: bool
    frame_roles: tuple[TimeframeRole, ...]

    def canonical_key(self) -> tuple[str, str, str, tuple[str, ...], RuleIdentity]:
        return (
            self.source_kind.value,
            self.source_contract,
            self.selector_kind.value,
            tuple(role.value for role in self.frame_roles),
            self.selector_rule,
        )

    def __post_init__(self) -> None:
        exact(self.source_kind, AnalyticalSourceKind, "source_kind")
        object.__setattr__(self, "source_contract", text(self.source_contract, "source_contract"))
        exact(self.selector_kind, SourceSelectorKind, "selector_kind")
        exact(self.selector_rule, RuleIdentity, "selector_rule")
        if not boolean(self.required_provenance, "required_provenance"):
            raise DataIntegrityError("fact-producing selectors require provenance")
        if (
            type(self.frame_roles) is not tuple
            or not self.frame_roles
            or any(type(role) is not TimeframeRole for role in self.frame_roles)
            or len(set(self.frame_roles)) != len(self.frame_roles)
        ):
            raise DataIntegrityError("frame_roles must be a non-empty unique TimeframeRole tuple")
        object.__setattr__(
            self, "frame_roles", tuple(sorted(self.frame_roles, key=_ROLE_ORDER.__getitem__))
        )


@dataclass(frozen=True, slots=True, order=True)
class EnumDirectionMapping:
    source_value: str
    strategy_direction: StrategyDirection

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_value", text(self.source_value, "source_value"))
        exact(self.strategy_direction, StrategyDirection, "strategy_direction")


@dataclass(frozen=True, slots=True)
class DirectionFactPolicy:
    fact_name: DirectionFactName
    selector: SourceSelector
    allowed_source_states: tuple[str, ...]
    enum_mappings: tuple[EnumDirectionMapping, ...]
    strategy_rule: RuleIdentity | None
    missing_action: NonAcceptanceAction
    conflict_action: NonAcceptanceAction

    def __post_init__(self) -> None:
        exact(self.fact_name, DirectionFactName, "fact_name")
        exact(self.selector, SourceSelector, "selector")
        object.__setattr__(
            self,
            "allowed_source_states",
            unique_texts(self.allowed_source_states, "allowed_source_states", allow_empty=False),
        )
        if type(self.enum_mappings) is not tuple or any(
            type(item) is not EnumDirectionMapping for item in self.enum_mappings
        ):
            raise DataIntegrityError("enum_mappings must contain EnumDirectionMapping values")
        mappings = tuple(sorted(self.enum_mappings))
        if len({item.source_value for item in mappings}) != len(mappings):
            raise DataIntegrityError("enum mappings must have unique source values")
        object.__setattr__(self, "enum_mappings", mappings)
        direct = self.selector.selector_kind is SourceSelectorKind.DIRECT_ENUM
        if direct != bool(mappings) or (not direct and self.strategy_rule is None):
            raise DataIntegrityError("direction policy selector and rule shape are inconsistent")
        if self.strategy_rule is not None:
            exact(self.strategy_rule, RuleIdentity, "strategy_rule")
        exact(self.missing_action, NonAcceptanceAction, "missing_action")
        exact(self.conflict_action, NonAcceptanceAction, "conflict_action")


@dataclass(frozen=True, slots=True)
class MtfDirectionPolicyRef:
    required_roles: tuple[TimeframeRole, ...]
    required_timeframes: tuple[str, ...]
    frame_direction_fact: DirectionFactName
    rule_identity: RuleIdentity
    missing_action: NonAcceptanceAction
    conflict_action: NonAcceptanceAction

    def __post_init__(self) -> None:
        if type(self.required_roles) is not tuple or any(
            type(item) is not TimeframeRole for item in self.required_roles
        ):
            raise DataIntegrityError("required_roles must contain TimeframeRole values")
        roles = tuple(sorted(set(self.required_roles), key=lambda item: item.value))
        if (
            not roles
            or len(roles) != len(self.required_roles)
            or TimeframeRole.PRIMARY not in roles
        ):
            raise DataIntegrityError("MTF roles must be unique and include PRIMARY")
        object.__setattr__(self, "required_roles", roles)
        object.__setattr__(
            self,
            "required_timeframes",
            unique_texts(self.required_timeframes, "required_timeframes", allow_empty=False),
        )
        exact(self.frame_direction_fact, DirectionFactName, "frame_direction_fact")
        if self.frame_direction_fact is DirectionFactName.MTF:
            raise DataIntegrityError("frame_direction_fact must reference a non-MTF policy")
        exact(self.rule_identity, RuleIdentity, "rule_identity")
        exact(self.missing_action, NonAcceptanceAction, "missing_action")
        exact(self.conflict_action, NonAcceptanceAction, "conflict_action")


__all__ = [
    "AnalyticalSourceKind",
    "DirectionFactName",
    "DirectionFactPolicy",
    "EnumDirectionMapping",
    "MtfDirectionPolicyRef",
    "NonAcceptanceAction",
    "SourceSelector",
    "SourceSelectorKind",
]
