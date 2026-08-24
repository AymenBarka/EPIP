"""Immutable semantic interchange values."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import digest, exact, text, unique_texts
from epip.strategy_mapping.rule_execution import SemanticValueKind
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_runtime.mtf import TimeframeRole


def _number(value: object, field: str, *, positive: bool = False) -> float:
    if (
        type(value) is not float
        or not isfinite(value)
        or value == 0.0
        and str(value).startswith("-")
    ):
        raise DataIntegrityError(f"{field} must be an exact finite float")
    if positive and value <= 0.0:
        raise DataIntegrityError(f"{field} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class SemanticValue:
    kind: SemanticValueKind
    text_value: str | None = None
    bool_value: bool | None = None
    float_value: float | None = None
    range_lower: float | None = None
    range_upper: float | None = None

    def __post_init__(self) -> None:
        exact(self.kind, SemanticValueKind, "kind")
        fields = (
            self.text_value,
            self.bool_value,
            self.float_value,
            self.range_lower,
            self.range_upper,
        )
        if self.kind is SemanticValueKind.TEXT:
            if self.text_value is None or any(x is not None for x in fields[1:]):
                raise DataIntegrityError("TEXT requires only text_value")
            object.__setattr__(self, "text_value", text(self.text_value, "text_value"))
        elif self.kind is SemanticValueKind.BOOLEAN:
            if type(self.bool_value) is not bool or any(
                x is not None for x in (fields[0], *fields[2:])
            ):
                raise DataIntegrityError("BOOLEAN requires only bool_value")
        elif self.kind in (SemanticValueKind.FINITE_FLOAT, SemanticValueKind.PRICE):
            if self.float_value is None or any(
                x is not None for x in (fields[0], fields[1], fields[3], fields[4])
            ):
                raise DataIntegrityError("numeric value has contradictory shape")
            _number(self.float_value, "float_value", positive=self.kind is SemanticValueKind.PRICE)
        else:
            if (
                self.range_lower is None
                or self.range_upper is None
                or any(x is not None for x in fields[:3])
            ):
                raise DataIntegrityError("PRICE_RANGE requires only its bounds")
            lower = _number(self.range_lower, "range_lower", positive=True)
            upper = _number(self.range_upper, "range_upper", positive=True)
            if upper < lower:
                raise DataIntegrityError("range_upper must not be below range_lower")


@dataclass(frozen=True, slots=True)
class SemanticCandidate:
    candidate_id: str
    source_binding_id: str
    provenance_ref: str
    instrument_binding_id: str
    timeframe: str
    source_rule_identity: RuleIdentity
    value: SemanticValue

    def __post_init__(self) -> None:
        for name in ("source_binding_id", "provenance_ref", "instrument_binding_id", "timeframe"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        exact(self.source_rule_identity, RuleIdentity, "source_rule_identity")
        exact(self.value, SemanticValue, "value")
        expected = digest(self, exclude=frozenset({"candidate_id"}))
        if self.candidate_id != expected:
            raise DataIntegrityError("candidate_id does not match semantic candidate")

    @classmethod
    def create(
        cls,
        *,
        source_binding_id: str,
        provenance_ref: str,
        instrument_binding_id: str,
        timeframe: str,
        source_rule_identity: RuleIdentity,
        value: SemanticValue,
    ) -> SemanticCandidate:
        candidate = object.__new__(cls)
        values = (
            "",
            source_binding_id,
            provenance_ref,
            instrument_binding_id,
            timeframe,
            source_rule_identity,
            value,
        )
        for name, item in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, item)
        return cls(digest(candidate, exclude=frozenset({"candidate_id"})), *values[1:])


@dataclass(frozen=True, slots=True, order=True)
class ConfidenceInputValue:
    input_key: str
    candidate: SemanticCandidate
    required: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_key", text(self.input_key, "input_key"))
        exact(self.candidate, SemanticCandidate, "candidate")
        if type(self.required) is not bool:
            raise DataIntegrityError("required must be a bool")


@dataclass(frozen=True, slots=True)
class TimeframeDirectionValue:
    timeframe: str
    role: TimeframeRole
    direction: StrategyDirection
    source_binding_ids: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "timeframe", text(self.timeframe, "timeframe"))
        exact(self.role, TimeframeRole, "role")
        exact(self.direction, StrategyDirection, "direction")
        object.__setattr__(
            self,
            "source_binding_ids",
            unique_texts(self.source_binding_ids, "source_binding_ids", allow_empty=False),
        )
        object.__setattr__(
            self,
            "provenance_refs",
            unique_texts(self.provenance_refs, "provenance_refs", allow_empty=False),
        )

    def canonical_key(self) -> tuple[str, str, str]:
        return (self.role.value, self.timeframe, self.direction.value)


__all__ = ["ConfidenceInputValue", "SemanticCandidate", "SemanticValue", "TimeframeDirectionValue"]
