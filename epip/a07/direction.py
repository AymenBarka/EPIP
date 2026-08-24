"""A07-E03 immutable directional-resolution contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a07.evidence import EvidenceValidation
from epip.a07.foundation import StrategyDirection
from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError, require_text

__all__ = [
    "DirectionDiagnostics",
    "DirectionValidation",
    "DirectionalDecision",
    "DirectionalFacts",
]

_KNOWN_DIAGNOSTICS = frozenset(
    {
        "DIRECTIONAL_CONFLICT",
        "DIRECTION_DISABLED_BY_POLICY",
        "EVIDENCE_INVALID",
        "NO_DIRECTIONAL_CONSENSUS",
        "PRIMARY_ALTERNATE_CONFLICT",
    }
)


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy direction model")

    def _init(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _Record)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


def _direction(value: object, field: str) -> StrategyDirection:
    if type(value) is not StrategyDirection:
        raise DataIntegrityError(f"{field} must be a StrategyDirection")
    assert isinstance(value, StrategyDirection)
    return value


def _diagnostics(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("diagnostics must be an immutable tuple")
    result = tuple(sorted(require_text(item, "diagnostic").strip() for item in value))
    if len(result) != len(set(result)):
        raise DataIntegrityError("diagnostics must not contain duplicates")
    if any(item not in _KNOWN_DIAGNOSTICS for item in result):
        raise DataIntegrityError("diagnostics contains an unknown E03 code")
    return result


class DirectionalFacts(_Record):
    """Caller-supplied normalized immutable directional facts."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "elliott_direction",
        "trend_direction",
        "structure_direction",
        "mtf_direction",
        "primary_direction",
        "alternate_direction",
    )
    _field_names = __slots__
    elliott_direction: StrategyDirection
    trend_direction: StrategyDirection
    structure_direction: StrategyDirection
    mtf_direction: StrategyDirection
    primary_direction: StrategyDirection
    alternate_direction: StrategyDirection

    def __init__(
        self,
        elliott_direction: object,
        trend_direction: object,
        structure_direction: object,
        mtf_direction: object,
        primary_direction: object,
        alternate_direction: object,
    ) -> None:
        self._init(
            {
                "elliott_direction": _direction(elliott_direction, "elliott_direction"),
                "trend_direction": _direction(trend_direction, "trend_direction"),
                "structure_direction": _direction(structure_direction, "structure_direction"),
                "mtf_direction": _direction(mtf_direction, "mtf_direction"),
                "primary_direction": _direction(primary_direction, "primary_direction"),
                "alternate_direction": _direction(alternate_direction, "alternate_direction"),
            }
        )


def _fact_values(facts: DirectionalFacts) -> tuple[StrategyDirection, ...]:
    return facts._values()  # type: ignore[return-value]


class DirectionalDecision(_Record):
    """Immutable direction derived from policy, evidence, and normalized facts."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "policy",
        "evidence_validation",
        "directional_facts",
        "direction",
    )
    _field_names = __slots__
    policy: StrategyPolicy
    evidence_validation: EvidenceValidation
    directional_facts: DirectionalFacts
    direction: StrategyDirection

    def __init__(
        self,
        policy: object,
        evidence_validation: object,
        directional_facts: object,
    ) -> None:
        if type(policy) is not StrategyPolicy:
            raise DataIntegrityError("policy must be a StrategyPolicy")
        if type(evidence_validation) is not EvidenceValidation:
            raise DataIntegrityError("evidence_validation must be an EvidenceValidation")
        if type(directional_facts) is not DirectionalFacts:
            raise DataIntegrityError("directional_facts must be DirectionalFacts")
        assert isinstance(policy, StrategyPolicy)
        assert isinstance(evidence_validation, EvidenceValidation)
        assert isinstance(directional_facts, DirectionalFacts)
        if evidence_validation.binding.policy != policy:
            raise DataIntegrityError("evidence validation policy does not match decision policy")
        values = _fact_values(directional_facts)
        direction = StrategyDirection.NO_TRADE
        if evidence_validation.valid and all(item is StrategyDirection.BUY for item in values):
            if StrategyDirection.BUY in policy.enabled_directions:
                direction = StrategyDirection.BUY
        elif (
            evidence_validation.valid
            and all(item is StrategyDirection.SELL for item in values)
            and StrategyDirection.SELL in policy.enabled_directions
        ):
            direction = StrategyDirection.SELL
        self._init(
            {
                "policy": policy,
                "evidence_validation": evidence_validation,
                "directional_facts": directional_facts,
                "direction": direction,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        policy: object,
        evidence_validation: object,
        directional_facts: object,
        direction: object,
    ) -> DirectionalDecision:
        supplied = _direction(direction, "direction")
        result = cls(policy, evidence_validation, directional_facts)
        if result.direction is not supplied:
            raise DataIntegrityError("direction does not match canonical resolution")
        return result


class DirectionDiagnostics(_Record):
    """Canonical immutable E03 direction diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        self._init({"diagnostics": _diagnostics(diagnostics)})


class DirectionValidation(_Record):
    """Immutable actionable-direction validation derived from a decision."""

    __slots__ = ("decision", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    decision: DirectionalDecision
    valid: bool
    diagnostics: DirectionDiagnostics

    def __init__(self, decision: object) -> None:
        if type(decision) is not DirectionalDecision:
            raise DataIntegrityError("decision must be a DirectionalDecision")
        assert isinstance(decision, DirectionalDecision)
        facts = _fact_values(decision.directional_facts)
        codes: set[str] = set()
        if not decision.evidence_validation.valid:
            codes.add("EVIDENCE_INVALID")
        if StrategyDirection.BUY in facts and StrategyDirection.SELL in facts:
            codes.add("DIRECTIONAL_CONFLICT")
        if (
            decision.directional_facts.primary_direction
            is not decision.directional_facts.alternate_direction
        ):
            codes.add("PRIMARY_ALTERNATE_CONFLICT")
        unanimous_buy = all(item is StrategyDirection.BUY for item in facts)
        unanimous_sell = all(item is StrategyDirection.SELL for item in facts)
        if not unanimous_buy and not unanimous_sell:
            codes.add("NO_DIRECTIONAL_CONSENSUS")
        resolved = (
            StrategyDirection.BUY
            if unanimous_buy
            else StrategyDirection.SELL if unanimous_sell else None
        )
        if resolved is not None and resolved not in decision.policy.enabled_directions:
            codes.add("DIRECTION_DISABLED_BY_POLICY")
        diagnostics = DirectionDiagnostics(tuple(codes))
        self._init(
            {
                "decision": decision,
                "valid": not diagnostics.diagnostics,
                "diagnostics": diagnostics,
            }
        )

    @classmethod
    def reconstruct(
        cls, decision: object, valid: object, diagnostics: object
    ) -> DirectionValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not DirectionDiagnostics:
            raise DataIntegrityError("diagnostics must be DirectionDiagnostics")
        result = cls(decision)
        if result.valid is not valid or result.diagnostics != diagnostics:
            raise DataIntegrityError(
                "validation fields do not match canonical direction validation"
            )
        return result
