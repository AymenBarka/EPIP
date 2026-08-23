"""A06-E01 immutable projection-authority contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

from epip.a06.foundation import ProjectionRequest
from epip.core.integrity import DataIntegrityError, MissingFieldError, require_text
from epip.temporal.model import TemporalAuthorityReference

__all__ = ["AuthorityDiagnostics", "AuthorityValidation", "ProjectionAuthority"]


class _ImmutableRecord:
    __slots__ = ()
    _field_names: ClassVar[tuple[str, ...]]

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise FrozenInstanceError("cannot assign to immutable authority model")

    def _initialize(self, values: dict[str, object]) -> None:
        for name in self._field_names:
            object.__setattr__(self, name, values[name])

    def _values(self) -> tuple[object, ...]:
        return tuple(getattr(self, name) for name in self._field_names)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, _ImmutableRecord)
        return self._values() == other._values()

    def __hash__(self) -> int:
        return hash((type(self), self._values()))


def _text(value: object, field: str) -> str:
    return require_text(value, field).strip()


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DataIntegrityError(f"{field} must be a positive integer")
    return value


def _scope(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise DataIntegrityError(f"{field} must be an immutable tuple")
    result = tuple(sorted(_text(item, field) for item in value))
    if not result:
        raise MissingFieldError(f"{field} must not be empty")
    if len(set(result)) != len(result):
        raise DataIntegrityError(f"{field} must not contain duplicates")
    return result


class ProjectionAuthority(_ImmutableRecord):
    """Immutable authority facts applicable to a projection."""

    __slots__ = (
        "authority_identity",
        "governance_epoch",
        "permitted_scope",
        "policy_version",
        "valid_from",
        "valid_until",
    )
    _field_names = __slots__
    authority_identity: str
    governance_epoch: int
    permitted_scope: tuple[str, ...]
    policy_version: int
    valid_from: int
    valid_until: int

    def __init__(
        self,
        authority_identity: object,
        governance_epoch: object,
        permitted_scope: object,
        policy_version: object,
        valid_from: object,
        valid_until: object,
    ) -> None:
        start = _positive(valid_from, "valid_from")
        end = _positive(valid_until, "valid_until")
        if start > end:
            raise DataIntegrityError("valid_from must not be after valid_until")
        self._initialize(
            {
                "authority_identity": _text(authority_identity, "authority_identity"),
                "governance_epoch": _positive(governance_epoch, "governance_epoch"),
                "permitted_scope": _scope(permitted_scope, "permitted_scope"),
                "policy_version": _positive(policy_version, "policy_version"),
                "valid_from": start,
                "valid_until": end,
            }
        )

    @classmethod
    def from_a05_authority(
        cls,
        reference: TemporalAuthorityReference,
        permitted_scope: object,
        policy_version: object,
        valid_from: object,
        valid_until: object,
    ) -> ProjectionAuthority:
        """Construct authority facts without duplicating the A05 reference."""
        if not isinstance(reference, TemporalAuthorityReference):
            raise DataIntegrityError("reference must be a TemporalAuthorityReference")
        return cls(
            reference.authority_identity,
            reference.governance_epoch.sequence,
            permitted_scope,
            policy_version,
            valid_from,
            valid_until,
        )


class AuthorityValidation(_ImmutableRecord):
    """Immutable outcome of validating authority against an E00 request."""

    __slots__ = ("authority_identity", "request_identity", "valid")
    _field_names = __slots__
    authority_identity: str
    request_identity: str
    valid: bool

    def __init__(self, authority: ProjectionAuthority, request: ProjectionRequest) -> None:
        if not isinstance(authority, ProjectionAuthority):
            raise DataIntegrityError("authority must be a ProjectionAuthority")
        if not isinstance(request, ProjectionRequest):
            raise DataIntegrityError("request must be a ProjectionRequest")
        valid = (
            request.policy_version == authority.policy_version
            and set(request.target_scope).issubset(authority.permitted_scope)
            and authority.valid_from <= authority.governance_epoch <= authority.valid_until
        )
        self._initialize(
            {
                "authority_identity": authority.authority_identity,
                "request_identity": request.request_identity,
                "valid": valid,
            }
        )


class AuthorityDiagnostics(_ImmutableRecord):
    """Immutable deterministic authority diagnostics."""

    __slots__ = ("diagnostics",)
    _field_names = __slots__
    diagnostics: tuple[str, ...]

    def __init__(self, diagnostics: object = ()) -> None:
        if diagnostics == ():
            values: tuple[str, ...] = ()
        else:
            values = _scope(diagnostics, "diagnostics")
        self._initialize({"diagnostics": values})
