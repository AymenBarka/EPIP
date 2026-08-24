"""Per-source and per-fact provenance contracts."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import digest, require_digest, text, timestamp, unique_texts
from epip.strategy_runtime.profile import StrategyProfileIdentity


@dataclass(frozen=True, slots=True)
class FactAdapterIdentity:
    adapter_id: str
    adapter_version: str
    contract_version: str
    fingerprint: str

    def __post_init__(self) -> None:
        for name in ("adapter_id", "adapter_version", "contract_version"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    source_domain: str
    source_contract: str
    source_contract_version: str
    source_object_id: str
    source_timestamp: str
    producer_version: str
    data_feed_id: str | None
    source_digest: str
    parent_source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "source_domain",
            "source_contract",
            "source_contract_version",
            "source_object_id",
            "producer_version",
        ):
            object.__setattr__(self, name, text(getattr(self, name), name))
        object.__setattr__(
            self, "source_timestamp", timestamp(self.source_timestamp, "source_timestamp")
        )
        if self.data_feed_id is not None:
            object.__setattr__(self, "data_feed_id", text(self.data_feed_id, "data_feed_id"))
        object.__setattr__(
            self, "source_digest", require_digest(self.source_digest, "source_digest")
        )
        object.__setattr__(
            self, "parent_source_ids", unique_texts(self.parent_source_ids, "parent_source_ids")
        )


@dataclass(frozen=True, slots=True)
class FactProvenance:
    fact_key: str
    source_refs: tuple[str, ...]
    adapter_id: str
    adapter_version: str
    profile_id: str
    profile_version: str
    transformation_id: str
    transformation_version: str
    fact_digest: str

    def __post_init__(self) -> None:
        for name in (
            "fact_key",
            "adapter_id",
            "adapter_version",
            "profile_id",
            "profile_version",
            "transformation_id",
            "transformation_version",
        ):
            object.__setattr__(self, name, text(getattr(self, name), name))
        object.__setattr__(
            self, "source_refs", unique_texts(self.source_refs, "source_refs", allow_empty=False)
        )
        object.__setattr__(self, "fact_digest", require_digest(self.fact_digest, "fact_digest"))


@dataclass(frozen=True, slots=True)
class ProvenanceManifest:
    manifest_id: str
    sources: tuple[SourceProvenance, ...]
    facts: tuple[FactProvenance, ...]
    profile_identity: StrategyProfileIdentity
    adapter_identity: FactAdapterIdentity
    evaluation_id: str

    def __post_init__(self) -> None:
        if type(self.sources) is not tuple or any(
            type(item) is not SourceProvenance for item in self.sources
        ):
            raise DataIntegrityError("sources must contain SourceProvenance values")
        if type(self.facts) is not tuple or any(
            type(item) is not FactProvenance for item in self.facts
        ):
            raise DataIntegrityError("facts must contain FactProvenance values")
        sources = tuple(sorted(self.sources, key=lambda item: item.source_object_id))
        facts = tuple(sorted(self.facts, key=lambda item: item.fact_key))
        if not sources or not facts:
            raise DataIntegrityError("provenance must contain sources and facts")
        source_ids = tuple(item.source_object_id for item in sources)
        fact_keys = tuple(item.fact_key for item in facts)
        if len(set(source_ids)) != len(source_ids) or len(set(fact_keys)) != len(fact_keys):
            raise DataIntegrityError("provenance identities must be unique")
        known = set(source_ids)
        if any(not set(item.source_refs) <= known for item in facts):
            raise DataIntegrityError("fact provenance contains dangling source references")
        if any(not set(item.parent_source_ids) <= known for item in sources):
            raise DataIntegrityError("source provenance contains dangling parent references")
        if any(
            item.profile_id != self.profile_identity.profile_id
            or item.profile_version != self.profile_identity.profile_version
            or item.adapter_id != self.adapter_identity.adapter_id
            or item.adapter_version != self.adapter_identity.adapter_version
            for item in facts
        ):
            raise DataIntegrityError("fact provenance identity mismatch")
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "facts", facts)
        object.__setattr__(self, "evaluation_id", text(self.evaluation_id, "evaluation_id"))
        expected = digest(self, exclude=frozenset({"manifest_id"}))
        if self.manifest_id != expected:
            raise DataIntegrityError("manifest_id does not match canonical provenance")

    @classmethod
    def create(
        cls,
        sources: tuple[SourceProvenance, ...],
        facts: tuple[FactProvenance, ...],
        profile_identity: StrategyProfileIdentity,
        adapter_identity: FactAdapterIdentity,
        evaluation_id: str,
    ) -> ProvenanceManifest:
        candidate = object.__new__(cls)
        values = (sources, facts, profile_identity, adapter_identity, evaluation_id)
        for name, value in zip(
            ("sources", "facts", "profile_identity", "adapter_identity", "evaluation_id"),
            values,
            strict=True,
        ):
            object.__setattr__(candidate, name, value)
        object.__setattr__(candidate, "manifest_id", "")
        return cls(digest(candidate, exclude=frozenset({"manifest_id"})), *values)
