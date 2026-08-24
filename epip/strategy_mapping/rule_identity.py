"""Exact immutable semantic-rule identities."""

from __future__ import annotations

from dataclasses import dataclass

from epip.strategy_mapping._base import require_digest, text, version


@dataclass(frozen=True, slots=True, order=True)
class RuleIdentity:
    rule_id: str
    rule_version: str
    rule_schema_version: str
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", text(self.rule_id, "rule_id"))
        object.__setattr__(self, "rule_version", text(self.rule_version, "rule_version"))
        version(self.rule_schema_version, "rule_schema_version")
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))

    @property
    def reference(self) -> str:
        return f"{self.rule_id}@{self.rule_version}#{self.fingerprint}"


__all__ = ["RuleIdentity"]
