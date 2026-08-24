"""Typed entry, stop, and target policy schemas; no geometry selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import boolean, exact
from epip.strategy_mapping.direction_policy import NonAcceptanceAction, SourceSelector
from epip.strategy_mapping.rule_identity import RuleIdentity


def _selectors(value: object) -> tuple[SourceSelector, ...]:
    if (
        type(value) is not tuple
        or not value
        or any(type(item) is not SourceSelector for item in value)
    ):
        raise DataIntegrityError("allowed_selectors must be a non-empty SourceSelector tuple")
    result = tuple(sorted(value, key=lambda item: item.canonical_key()))
    if len(set(result)) != len(result):
        raise DataIntegrityError("allowed_selectors must be unique")
    return result


class _GeometryPolicy(Protocol):
    @property
    def policy_identity(self) -> RuleIdentity: ...

    @property
    def allowed_selectors(self) -> tuple[SourceSelector, ...]: ...

    @property
    def candidate_selector(self) -> RuleIdentity: ...

    @property
    def direction_applicability_rule(self) -> RuleIdentity: ...

    @property
    def missing_action(self) -> NonAcceptanceAction: ...

    @property
    def conflict_action(self) -> NonAcceptanceAction: ...

    @property
    def require_provenance(self) -> bool: ...


def _common(instance: _GeometryPolicy) -> None:
    exact(instance.policy_identity, RuleIdentity, "policy_identity")
    object.__setattr__(instance, "allowed_selectors", _selectors(instance.allowed_selectors))
    exact(instance.candidate_selector, RuleIdentity, "candidate_selector")
    exact(
        instance.direction_applicability_rule,
        RuleIdentity,
        "direction_applicability_rule",
    )
    exact(instance.missing_action, NonAcceptanceAction, "missing_action")
    exact(instance.conflict_action, NonAcceptanceAction, "conflict_action")
    if not boolean(instance.require_provenance, "require_provenance"):
        raise DataIntegrityError("geometry policies require provenance")


@dataclass(frozen=True, slots=True)
class EntrySourcePolicy:
    policy_identity: RuleIdentity
    allowed_selectors: tuple[SourceSelector, ...]
    candidate_selector: RuleIdentity
    ranking_rule: RuleIdentity
    required_boundary_rule: RuleIdentity
    direction_applicability_rule: RuleIdentity
    missing_action: NonAcceptanceAction
    conflict_action: NonAcceptanceAction
    require_provenance: bool

    def __post_init__(self) -> None:
        _common(self)
        exact(self.ranking_rule, RuleIdentity, "ranking_rule")
        exact(self.required_boundary_rule, RuleIdentity, "required_boundary_rule")


@dataclass(frozen=True, slots=True)
class StopSourcePolicy:
    policy_identity: RuleIdentity
    allowed_selectors: tuple[SourceSelector, ...]
    candidate_selector: RuleIdentity
    precedence_rule: RuleIdentity
    buffer_rule: RuleIdentity
    volatility_adjustment_rule: RuleIdentity | None
    direction_applicability_rule: RuleIdentity
    missing_action: NonAcceptanceAction
    conflict_action: NonAcceptanceAction
    require_provenance: bool

    def __post_init__(self) -> None:
        _common(self)
        exact(self.precedence_rule, RuleIdentity, "precedence_rule")
        exact(self.buffer_rule, RuleIdentity, "buffer_rule")
        if self.volatility_adjustment_rule is not None:
            exact(self.volatility_adjustment_rule, RuleIdentity, "volatility_adjustment_rule")


@dataclass(frozen=True, slots=True)
class TargetSourcePolicy:
    policy_identity: RuleIdentity
    allowed_selectors: tuple[SourceSelector, ...]
    candidate_selector: RuleIdentity
    ranking_rule: RuleIdentity
    threshold_rule: RuleIdentity | None
    extension_rule: RuleIdentity | None
    direction_applicability_rule: RuleIdentity
    missing_action: NonAcceptanceAction
    conflict_action: NonAcceptanceAction
    require_provenance: bool

    def __post_init__(self) -> None:
        _common(self)
        exact(self.ranking_rule, RuleIdentity, "ranking_rule")
        for name in ("threshold_rule", "extension_rule"):
            value = getattr(self, name)
            if value is not None:
                exact(value, RuleIdentity, name)


__all__ = ["EntrySourcePolicy", "StopSourcePolicy", "TargetSourcePolicy"]
