"""A07-E01 immutable strategy-policy contracts."""

from __future__ import annotations

import json
import re
from dataclasses import FrozenInstanceError
from decimal import Decimal
from hashlib import sha256
from math import isfinite
from typing import ClassVar

from epip.a07.foundation import StrategyDirection, StrategyIdentity
from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text

__all__ = [
    "PolicyDiagnostics",
    "PolicyValidation",
    "StrategyPolicy",
    "StrategyPolicyIdentity",
]

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*", re.ASCII)
_FINGERPRINT = re.compile(r"[0-9a-f]{64}", re.ASCII)
_REFERENCE = re.compile(
    r"a07-policy:1:([A-Za-z0-9][A-Za-z0-9._-]*):"
    r"([A-Za-z0-9][A-Za-z0-9._-]*):sha256:([0-9a-f]{64})",
    re.ASCII,
)
_KNOWN_DIAGNOSTICS = frozenset({"POLICY_REFERENCE_MISMATCH"})


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy policy model")

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


def _identifier(value: object, field: str) -> str:
    result = _text(value, field)
    if _IDENTIFIER.fullmatch(result) is None:
        raise DataIntegrityError(f"{field} must be a canonical identifier")
    return result


def _fingerprint(value: object) -> str:
    result = _text(value, "fingerprint")
    if _FINGERPRINT.fullmatch(result) is None:
        raise DataIntegrityError("fingerprint must be a lowercase SHA-256 digest")
    return result


def _reference(value: object, field: str) -> str:
    result = _text(value, field)
    if result != value or _REFERENCE.fullmatch(result) is None:
        raise DataIntegrityError(f"{field} must be a canonical A07 policy reference")
    return result


def _float(value: object, field: str, *, unit_interval: bool = False) -> float:
    if not isinstance(value, float) or not isfinite(value):
        raise DataIntegrityError(f"{field} must be a finite float")
    if unit_interval:
        if not 0.0 <= value <= 1.0:
            raise DataIntegrityError(f"{field} must be between 0.0 and 1.0")
    elif value <= 0.0:
        raise DataIntegrityError(f"{field} must be greater than zero")
    return value


def _decimal_text(value: float) -> str:
    if value == 0.0:
        return "0"
    result = format(Decimal(str(value)), "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result


def _integer(value: object, field: str, *, positive: bool) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DataIntegrityError(f"{field} must be an integer")
    if (positive and value <= 0) or (not positive and value < 0):
        qualifier = "positive" if positive else "non-negative"
        raise DataIntegrityError(f"{field} must be {qualifier}")
    return value


def _text_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    result = tuple(sorted(_text(item, field) for item in value))
    if len(result) != len(set(result)):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return result


def _directions(value: object) -> tuple[StrategyDirection, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("enabled_directions must be an immutable tuple")
    if not value:
        raise MissingFieldError("enabled_directions must not be empty")
    if any(type(item) is not StrategyDirection for item in value):
        raise DataIntegrityError("enabled_directions must contain StrategyDirection values")
    if StrategyDirection.NO_TRADE in value:
        raise DataIntegrityError("NO_TRADE cannot be an enabled direction")
    if len(value) != len(set(value)):
        raise DataIntegrityError("enabled_directions must not contain duplicates")
    return tuple(item for item in StrategyDirection if item in value)


def _elliott(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("elliott_policy must be an immutable tuple")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DataIntegrityError("elliott_policy entries must be key/value tuples")
        pairs.append((_text(item[0], "elliott_policy key"), _text(item[1], "elliott_policy value")))
    keys = tuple(key for key, _ in pairs)
    if len(keys) != len(set(keys)):
        raise DataIntegrityError("elliott_policy keys must be unique")
    return tuple(sorted(pairs))


class StrategyPolicyIdentity(_Record):
    """Domain-qualified identity of immutable strategy-policy content."""

    __slots__ = ("policy_id", "policy_version", "fingerprint")  # noqa: RUF023
    _field_names = __slots__
    policy_id: str
    policy_version: str
    fingerprint: str

    def __init__(self, policy_id: object, policy_version: object, fingerprint: object) -> None:
        self._init(
            {
                "policy_id": _identifier(policy_id, "policy_id"),
                "policy_version": _identifier(policy_version, "policy_version"),
                "fingerprint": _fingerprint(fingerprint),
            }
        )

    @property
    def reference(self) -> str:
        return f"a07-policy:1:{self.policy_id}:{self.policy_version}:" f"sha256:{self.fingerprint}"


class StrategyPolicy(_Record):
    """Canonical immutable E01 strategy-policy configuration."""

    __slots__ = (  # noqa: RUF023 - normative fingerprint/equality field order
        "identity",
        "strategy_identity",
        "enabled_directions",
        "minimum_rr",
        "minimum_confidence",
        "required_evidence",
        "optional_evidence",
        "expiration_seconds",
        "numeric_precision",
        "elliott_policy",
    )
    _field_names = __slots__
    identity: StrategyPolicyIdentity
    strategy_identity: StrategyIdentity
    enabled_directions: tuple[StrategyDirection, ...]
    minimum_rr: float
    minimum_confidence: float
    required_evidence: tuple[str, ...]
    optional_evidence: tuple[str, ...]
    expiration_seconds: int
    numeric_precision: int
    elliott_policy: tuple[tuple[str, str], ...]

    def __init__(
        self,
        policy_id: object,
        policy_version: object,
        strategy_identity: object,
        enabled_directions: object,
        minimum_rr: object,
        minimum_confidence: object,
        required_evidence: object,
        optional_evidence: object,
        expiration_seconds: object,
        numeric_precision: object,
        elliott_policy: object,
    ) -> None:
        identifier = _identifier(policy_id, "policy_id")
        version = _identifier(policy_version, "policy_version")
        if type(strategy_identity) is not StrategyIdentity:
            raise DataIntegrityError("strategy_identity must be a StrategyIdentity")
        directions = _directions(enabled_directions)
        rr = _float(minimum_rr, "minimum_rr")
        confidence = _float(minimum_confidence, "minimum_confidence", unit_interval=True)
        required = _text_tuple(required_evidence, "required_evidence")
        optional = _text_tuple(optional_evidence, "optional_evidence")
        if set(required).intersection(optional):
            raise DataIntegrityError("required_evidence and optional_evidence must be disjoint")
        expiration = _integer(expiration_seconds, "expiration_seconds", positive=True)
        precision = _integer(numeric_precision, "numeric_precision", positive=False)
        elliott = _elliott(elliott_policy)
        assert isinstance(strategy_identity, StrategyIdentity)
        payload: list[object] = [
            "a07-strategy-policy",
            "1",
            "epip-json-v1",
            "sha256-v1",
            identifier,
            version,
            [strategy_identity.strategy_id, strategy_identity.strategy_version],
            [item.value for item in directions],
            _decimal_text(rr),
            _decimal_text(confidence),
            list(required),
            list(optional),
            expiration,
            precision,
            [list(item) for item in elliott],
        ]
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        identity = StrategyPolicyIdentity(identifier, version, sha256(encoded).hexdigest())
        self._init(
            {
                "identity": identity,
                "strategy_identity": strategy_identity,
                "enabled_directions": directions,
                "minimum_rr": rr,
                "minimum_confidence": confidence,
                "required_evidence": required,
                "optional_evidence": optional,
                "expiration_seconds": expiration,
                "numeric_precision": precision,
                "elliott_policy": elliott,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        identity: object,
        strategy_identity: object,
        enabled_directions: object,
        minimum_rr: object,
        minimum_confidence: object,
        required_evidence: object,
        optional_evidence: object,
        expiration_seconds: object,
        numeric_precision: object,
        elliott_policy: object,
    ) -> StrategyPolicy:
        if type(identity) is not StrategyPolicyIdentity:
            raise DataIntegrityError("identity must be a StrategyPolicyIdentity")
        assert isinstance(identity, StrategyPolicyIdentity)
        result = cls(
            identity.policy_id,
            identity.policy_version,
            strategy_identity,
            enabled_directions,
            minimum_rr,
            minimum_confidence,
            required_evidence,
            optional_evidence,
            expiration_seconds,
            numeric_precision,
            elliott_policy,
        )
        if result.identity != identity:
            raise DataIntegrityError("policy identity does not match canonical content")
        return result


class PolicyDiagnostics(_Record):
    """Canonical immutable E01 policy diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        values = _text_tuple(diagnostics, "diagnostics")
        if any(item not in _KNOWN_DIAGNOSTICS for item in values):
            raise DataIntegrityError("diagnostics contains an unknown E01 code")
        self._init({"diagnostics": values})


class PolicyValidation(_Record):
    """Immutable result of comparing a policy with an opaque E00 reference."""

    __slots__ = (  # noqa: RUF023 - normative validation equality field order
        "policy_reference",
        "expected_policy_reference",
        "valid",
        "diagnostics",
    )
    _field_names = __slots__
    policy_reference: str
    expected_policy_reference: str
    valid: bool
    diagnostics: PolicyDiagnostics

    def __init__(self, policy: object, expected_policy_reference: object) -> None:
        if type(policy) is not StrategyPolicy:
            raise DataIntegrityError("policy must be a StrategyPolicy")
        assert isinstance(policy, StrategyPolicy)
        expected = _reference(expected_policy_reference, "expected_policy_reference")
        actual = policy.identity.reference
        valid = actual == expected
        diagnostics = PolicyDiagnostics(() if valid else ("POLICY_REFERENCE_MISMATCH",))
        self._init(
            {
                "policy_reference": actual,
                "expected_policy_reference": expected,
                "valid": valid,
                "diagnostics": diagnostics,
            }
        )
