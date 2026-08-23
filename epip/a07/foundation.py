"""A07-E00 immutable strategy-foundation contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime
from enum import Enum
from typing import ClassVar

from epip.core.integrity import DataIntegrityError, require_text

__all__ = [
    "StrategyDirection",
    "StrategyEvaluationRequest",
    "StrategyEvidenceIdentity",
    "StrategyFoundationDiagnostics",
    "StrategyIdentity",
]


class StrategyDirection(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy foundation model")

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


def _text(value: object, field: str) -> str:
    return require_text(value, field).strip()


def _timestamp(value: object) -> str:
    result = _text(value, "evaluation_timestamp")
    try:
        parsed = datetime.fromisoformat(result)
    except ValueError as exc:
        raise DataIntegrityError("evaluation_timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataIntegrityError("evaluation_timestamp must include a timezone")
    return result


class StrategyIdentity(_Record):
    """Stable identity of a strategy definition."""

    __slots__ = ("strategy_id", "strategy_version")
    _field_names = __slots__
    strategy_id: str
    strategy_version: str

    def __init__(self, strategy_id: object, strategy_version: object) -> None:
        self._init(
            {
                "strategy_id": _text(strategy_id, "strategy_id"),
                "strategy_version": _text(strategy_version, "strategy_version"),
            }
        )


class StrategyEvidenceIdentity(_Record):
    """Opaque provenance identity for the evidence snapshot consumed by A07."""

    __slots__ = ("evidence_id", "provenance")
    _field_names = __slots__
    evidence_id: str
    provenance: str

    def __init__(self, evidence_id: object, provenance: object) -> None:
        self._init(
            {
                "evidence_id": _text(evidence_id, "evidence_id"),
                "provenance": _text(provenance, "provenance"),
            }
        )


class StrategyEvaluationRequest(_Record):
    """Immutable E00 request carrying identity and opaque predecessor references."""

    __slots__ = (
        "baseline_reference",
        "evaluation_timestamp",
        "evidence_identity",
        "policy_reference",
        "strategy_identity",
    )
    _field_names = __slots__
    baseline_reference: str
    evaluation_timestamp: str
    evidence_identity: StrategyEvidenceIdentity
    policy_reference: str
    strategy_identity: StrategyIdentity

    def __init__(
        self,
        strategy_identity: object,
        evidence_identity: object,
        evaluation_timestamp: object,
        baseline_reference: object,
        policy_reference: object,
    ) -> None:
        if not isinstance(strategy_identity, StrategyIdentity):
            raise DataIntegrityError("strategy_identity must be a StrategyIdentity")
        if not isinstance(evidence_identity, StrategyEvidenceIdentity):
            raise DataIntegrityError("evidence_identity must be a StrategyEvidenceIdentity")
        self._init(
            {
                "baseline_reference": _text(baseline_reference, "baseline_reference"),
                "evaluation_timestamp": _timestamp(evaluation_timestamp),
                "evidence_identity": evidence_identity,
                "policy_reference": _text(policy_reference, "policy_reference"),
                "strategy_identity": strategy_identity,
            }
        )


class StrategyFoundationDiagnostics(_Record):
    """Immutable, canonically ordered foundation diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if not isinstance(diagnostics, tuple):
            raise DataIntegrityError("diagnostics must be an immutable tuple")
        values = tuple(sorted(_text(item, "diagnostic") for item in diagnostics))
        if len(set(values)) != len(values):
            raise DataIntegrityError("diagnostics must not contain duplicates")
        self._init({"diagnostics": values})
