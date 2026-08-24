"""A07-E02 immutable evidence-binding contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a07.foundation import StrategyEvidenceIdentity, StrategyIdentity
from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError, require_text

__all__ = [
    "EvidenceBinding",
    "EvidenceDiagnostics",
    "EvidenceValidation",
    "StrategyEvidenceSnapshot",
]

_KNOWN_DIAGNOSTICS = frozenset(
    {
        "MISSING_REQUIRED_EVIDENCE",
        "STALE_OPTIONAL_EVIDENCE",
        "STALE_REQUIRED_EVIDENCE",
        "STRATEGY_IDENTITY_MISMATCH",
        "TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE",
        "TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE",
        "UNEXPECTED_EVIDENCE",
    }
)


class _Record:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable strategy evidence model")

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


def _snapshot_key(snapshot: StrategyEvidenceSnapshot) -> tuple[str, ...]:
    return (
        snapshot.evidence_key,
        snapshot.evidence_identity.evidence_id,
        snapshot.evidence_identity.provenance,
        snapshot.strategy_identity.strategy_id,
        snapshot.strategy_identity.strategy_version,
    )


def _snapshots(value: object) -> tuple[StrategyEvidenceSnapshot, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("available_evidence must be an immutable tuple")
    if any(type(item) is not StrategyEvidenceSnapshot for item in value):
        raise DataIntegrityError("available_evidence must contain StrategyEvidenceSnapshot values")
    snapshots = tuple(value)
    keys = tuple(item.evidence_key for item in snapshots)
    identities = tuple(item.evidence_identity for item in snapshots)
    if len(keys) != len(set(keys)):
        raise DataIntegrityError("available_evidence contains duplicate evidence keys")
    if len(identities) != len(set(identities)):
        raise DataIntegrityError("available_evidence contains duplicate evidence identities")
    return tuple(sorted(snapshots, key=_snapshot_key))


def _diagnostics(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError("diagnostics must be an immutable tuple")
    result = tuple(sorted(_text(item, "diagnostic") for item in value))
    if len(result) != len(set(result)):
        raise DataIntegrityError("diagnostics must not contain duplicates")
    if any(item not in _KNOWN_DIAGNOSTICS for item in result):
        raise DataIntegrityError("diagnostics contains an unknown E02 code")
    return result


class StrategyEvidenceSnapshot(_Record):
    """Immutable A07 evidence identity and supplied eligibility facts."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "strategy_identity",
        "evidence_identity",
        "evidence_key",
        "fresh",
        "temporally_eligible",
    )
    _field_names = __slots__
    strategy_identity: StrategyIdentity
    evidence_identity: StrategyEvidenceIdentity
    evidence_key: str
    fresh: bool
    temporally_eligible: bool

    def __init__(
        self,
        strategy_identity: object,
        evidence_identity: object,
        evidence_key: object,
        fresh: object,
        temporally_eligible: object,
    ) -> None:
        if type(strategy_identity) is not StrategyIdentity:
            raise DataIntegrityError("strategy_identity must be a StrategyIdentity")
        if type(evidence_identity) is not StrategyEvidenceIdentity:
            raise DataIntegrityError("evidence_identity must be a StrategyEvidenceIdentity")
        if type(fresh) is not bool:
            raise DataIntegrityError("fresh must be a bool")
        if type(temporally_eligible) is not bool:
            raise DataIntegrityError("temporally_eligible must be a bool")
        self._init(
            {
                "strategy_identity": strategy_identity,
                "evidence_identity": evidence_identity,
                "evidence_key": _text(evidence_key, "evidence_key"),
                "fresh": fresh,
                "temporally_eligible": temporally_eligible,
            }
        )


class EvidenceBinding(_Record):
    """Canonical immutable reconciliation of policy keys and evidence facts."""

    __slots__ = (  # noqa: RUF023 - normative field and equality order
        "policy",
        "available_evidence",
        "bound_required",
        "bound_optional",
        "missing_required",
        "unexpected_evidence",
    )
    _field_names = __slots__
    policy: StrategyPolicy
    available_evidence: tuple[StrategyEvidenceSnapshot, ...]
    bound_required: tuple[StrategyEvidenceSnapshot, ...]
    bound_optional: tuple[StrategyEvidenceSnapshot, ...]
    missing_required: tuple[str, ...]
    unexpected_evidence: tuple[StrategyEvidenceSnapshot, ...]

    def __init__(self, policy: object, available_evidence: object) -> None:
        if type(policy) is not StrategyPolicy:
            raise DataIntegrityError("policy must be a StrategyPolicy")
        assert isinstance(policy, StrategyPolicy)
        available = _snapshots(available_evidence)
        by_key = {item.evidence_key: item for item in available}
        required = tuple(by_key[key] for key in policy.required_evidence if key in by_key)
        optional = tuple(by_key[key] for key in policy.optional_evidence if key in by_key)
        missing = tuple(key for key in policy.required_evidence if key not in by_key)
        admitted = set(policy.required_evidence).union(policy.optional_evidence)
        unexpected = tuple(item for item in available if item.evidence_key not in admitted)
        self._init(
            {
                "policy": policy,
                "available_evidence": available,
                "bound_required": required,
                "bound_optional": optional,
                "missing_required": missing,
                "unexpected_evidence": unexpected,
            }
        )

    @classmethod
    def reconstruct(
        cls,
        policy: object,
        available_evidence: object,
        bound_required: object,
        bound_optional: object,
        missing_required: object,
        unexpected_evidence: object,
    ) -> EvidenceBinding:
        result = cls(policy, available_evidence)
        supplied = (
            policy,
            available_evidence,
            bound_required,
            bound_optional,
            missing_required,
            unexpected_evidence,
        )
        if result._values() != supplied:
            raise DataIntegrityError(
                "binding fields do not match canonical evidence reconciliation"
            )
        return result


class EvidenceDiagnostics(_Record):
    """Canonical immutable E02 evidence diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        self._init({"diagnostics": _diagnostics(diagnostics)})


class EvidenceValidation(_Record):
    """Immutable validation derived from an E02 evidence binding."""

    __slots__ = ("binding", "valid", "diagnostics")  # noqa: RUF023
    _field_names = __slots__
    binding: EvidenceBinding
    valid: bool
    diagnostics: EvidenceDiagnostics

    def __init__(self, binding: object) -> None:
        if type(binding) is not EvidenceBinding:
            raise DataIntegrityError("binding must be an EvidenceBinding")
        assert isinstance(binding, EvidenceBinding)
        codes: set[str] = set()
        if binding.missing_required:
            codes.add("MISSING_REQUIRED_EVIDENCE")
        if any(not item.fresh for item in binding.bound_required):
            codes.add("STALE_REQUIRED_EVIDENCE")
        if any(not item.fresh for item in binding.bound_optional):
            codes.add("STALE_OPTIONAL_EVIDENCE")
        if any(not item.temporally_eligible for item in binding.bound_required):
            codes.add("TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE")
        if any(not item.temporally_eligible for item in binding.bound_optional):
            codes.add("TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE")
        if any(
            item.strategy_identity != binding.policy.strategy_identity
            for item in binding.available_evidence
        ):
            codes.add("STRATEGY_IDENTITY_MISMATCH")
        if binding.unexpected_evidence:
            codes.add("UNEXPECTED_EVIDENCE")
        diagnostics = EvidenceDiagnostics(tuple(codes))
        self._init(
            {
                "binding": binding,
                "valid": not diagnostics.diagnostics,
                "diagnostics": diagnostics,
            }
        )

    @classmethod
    def reconstruct(cls, binding: object, valid: object, diagnostics: object) -> EvidenceValidation:
        if type(valid) is not bool:
            raise DataIntegrityError("valid must be a bool")
        if type(diagnostics) is not EvidenceDiagnostics:
            raise DataIntegrityError("diagnostics must be EvidenceDiagnostics")
        result = cls(binding)
        if result.valid != valid or result.diagnostics != diagnostics:
            raise DataIntegrityError("validation fields do not match canonical evidence validation")
        return result
