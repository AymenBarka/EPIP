"""Tests for the deterministic EPIP-016 evidence infrastructure."""

from __future__ import annotations

from dataclasses import replace

import pytest

from epip.core import evidence_engine
from epip.core.integrity import DataIntegrityError, RelationshipIntegrityError
from epip.decision.domain import (
    Confidence,
    ConfidenceLevel,
    DecisionDigest,
    DecisionMetadata,
    Evidence,
    EvidenceCategory,
    EvidenceReference,
    Quality,
    QualityLevel,
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.evidence import (
    EvidenceBuilder,
    EvidenceCollection,
    EvidenceDiagnostics,
    EvidenceDigest,
    EvidenceEngine,
    EvidenceLifecycleState,
    EvidenceReferenceResolver,
    EvidenceRegistry,
    EvidenceSnapshot,
    EvidenceValidator,
)


def _evidence(
    identifier: str = "evidence-1",
    *,
    category: EvidenceCategory = EvidenceCategory.MARKET_DATA,
    source: str = "feed-a",
    dependencies: tuple[str, ...] = (),
) -> Evidence:
    return EvidenceBuilder().build(
        evidence_id=identifier,
        category=category,
        source=source,
        source_version=1,
        payload=(("symbol", "EURUSD"), ("price", "1.10000")),
        confidence=Confidence(0.8, ConfidenceLevel.HIGH),
        quality=Quality(0.9, QualityLevel.VERY_HIGH),
        validity=Validity(1.0, ValidityLevel.VALID),
        uncertainty=Uncertainty(0.2),
        dependencies=dependencies,
        metadata=DecisionMetadata(1, "42", "programme-b"),
    )


def test_digest_is_canonical_and_rejects_invalid_values() -> None:
    first = EvidenceDigest.from_value({"b": 2, "a": 1})
    second = EvidenceDigest.from_value({"a": 1, "b": 2})
    assert first == second
    assert first.algorithm == "sha256"
    with pytest.raises(RelationshipIntegrityError):
        EvidenceDigest("0" * 63)
    with pytest.raises(RelationshipIntegrityError):
        EvidenceDigest("z" * 64)
    with pytest.raises(RelationshipIntegrityError):
        EvidenceDigest("0" * 64, "sha1")


def test_collection_is_immutable_ordered_unique_and_queryable() -> None:
    one = _evidence("a", source="one")
    two = _evidence("b", category=EvidenceCategory.RISK, source="two")
    collection = EvidenceCollection((two, one))
    assert tuple(collection) == (one, two)
    assert len(collection) == 2
    assert collection.get("a") is one
    assert collection.get("missing") is None
    assert collection.by_category(EvidenceCategory.RISK).items == (two,)
    assert collection.by_source("one").items == (one,)
    assert collection.group_by_category() == (
        (EvidenceCategory.MARKET_DATA, EvidenceCollection((one,))),
        (EvidenceCategory.RISK, EvidenceCollection((two,))),
    )
    assert collection.to_data() == [one.to_dict(), two.to_dict()]
    with pytest.raises(RelationshipIntegrityError):
        EvidenceCollection([one])  # type: ignore[arg-type]
    with pytest.raises(RelationshipIntegrityError):
        EvidenceCollection((one, one))


def test_registry_lifecycle_and_indexes_are_deterministic() -> None:
    one = _evidence("a")
    two = _evidence("b", category=EvidenceCategory.RISK, source="risk")
    registry = EvidenceRegistry().register(two).register(one)
    assert tuple(item.evidence.evidence_id for item in registry.entries) == ("a", "b")
    assert registry.entry("a").state is EvidenceLifecycleState.REGISTERED
    assert registry.get("a") == one
    assert registry.get("missing") is None
    assert registry.by_type(Evidence).items == (one, two)
    assert registry.by_category(EvidenceCategory.RISK).items == (two,)
    assert registry.by_source("risk").items == (two,)
    assert registry.by_reference(EvidenceReference("a", 1)) == one
    assert registry.by_reference(EvidenceReference("a", 2)) is None
    assert registry.by_reference(EvidenceReference("missing", 1)) is None
    assert registry.by_digest(one.content_digest) == one
    assert registry.by_digest(one.content_digest.value) == one
    assert registry.by_digest("f" * 64) is None
    assert len(registry.collection(EvidenceLifecycleState.REGISTERED)) == 2
    assert registry.digest() == EvidenceRegistry().register(two).register(one).digest()
    with pytest.raises(KeyError):
        registry.entry("missing")
    with pytest.raises(RelationshipIntegrityError):
        registry.register(one)
    with pytest.raises(RelationshipIntegrityError):
        registry.transition("a", EvidenceLifecycleState.ARCHIVED)

    for target in (
        EvidenceLifecycleState.AVAILABLE,
        EvidenceLifecycleState.SNAPSHOTTED,
        EvidenceLifecycleState.ARCHIVED,
        EvidenceLifecycleState.DISCARDED,
    ):
        registry = registry.transition("a", target)
    assert registry.entry("a").state is EvidenceLifecycleState.DISCARDED
    with pytest.raises(RelationshipIntegrityError):
        registry.transition("a", EvidenceLifecycleState.CREATED)


def test_registry_rejects_invalid_entries() -> None:
    registry = EvidenceRegistry().register(_evidence())
    entry = registry.entries[0]
    with pytest.raises(RelationshipIntegrityError):
        EvidenceRegistry((entry, entry))
    object.__setattr__(entry, "state", "invalid")
    with pytest.raises(RelationshipIntegrityError):
        EvidenceRegistry((entry,))


def test_builder_normalizes_and_validator_checks_structure() -> None:
    evidence = _evidence(dependencies=("z", "a", "z"))
    assert evidence.payload == (("price", "1.10000"), ("symbol", "EURUSD"))
    assert evidence.dependencies == ("a", "z")
    validator = EvidenceValidator()
    validator.validate(evidence)
    validator.validate_references(evidence, ("a", "z"))
    with pytest.raises(RelationshipIntegrityError):
        validator.validate_references(evidence, ("a",))

    cases: list[tuple[str, object]] = [
        ("evidence_id", ""),
        ("source", ""),
        ("source_version", 0),
        ("category", "unknown"),
        ("content_digest", DecisionDigest("f" * 64)),
        ("dependencies", (evidence.evidence_id,)),
    ]
    for field, value in cases:
        invalid = replace(evidence)
        object.__setattr__(invalid, field, value)
        with pytest.raises(DataIntegrityError):
            validator.validate(invalid)

    self_dependent = replace(evidence)
    object.__setattr__(self_dependent, "dependencies", (evidence.evidence_id,))
    object.__setattr__(
        self_dependent,
        "content_digest",
        EvidenceDigest.from_value(
            {
                key: value
                for key, value in self_dependent.to_dict().items()
                if key != "content_digest"
            }
        ),
    )
    with pytest.raises(RelationshipIntegrityError, match="depend on itself"):
        validator.validate(self_dependent)


def test_reference_resolver_resolves_versions_and_orders_results() -> None:
    one = _evidence("a")
    two = _evidence("b")
    resolver = EvidenceReferenceResolver(EvidenceRegistry().register(two).register(one))
    assert resolver.resolve(EvidenceReference("a", 1)) == one
    assert resolver.resolve_all((EvidenceReference("b", 1), EvidenceReference("a", 1))).items == (
        one,
        two,
    )
    with pytest.raises(KeyError):
        resolver.resolve(EvidenceReference("a", 2))


def test_snapshot_round_trip_is_byte_stable_and_identity_preserving() -> None:
    registry = EvidenceRegistry().register(_evidence("a"))
    registry = registry.transition("a", EvidenceLifecycleState.AVAILABLE)
    snapshot = EvidenceSnapshot.create("snapshot-1", 1, registry)
    restored = EvidenceSnapshot.from_json(snapshot.to_json())
    assert restored == snapshot
    assert hash(restored) == hash(snapshot)
    assert restored.to_json() == snapshot.to_json()
    assert restored.entries[0][0].evidence_id == "a"

    with pytest.raises(DataIntegrityError):
        EvidenceSnapshot("", 1, snapshot.entries, snapshot.registry_digest, snapshot.content_digest)
    with pytest.raises(DataIntegrityError):
        EvidenceSnapshot(
            "x", 0, snapshot.entries, snapshot.registry_digest, snapshot.content_digest
        )
    with pytest.raises(RelationshipIntegrityError):
        EvidenceSnapshot(
            "x", 1, snapshot.entries, snapshot.registry_digest, EvidenceDigest("f" * 64)
        )
    with pytest.raises(RelationshipIntegrityError):
        EvidenceSnapshot(
            snapshot.snapshot_id,
            snapshot.version,
            snapshot.entries,
            EvidenceDigest("f" * 64),
            snapshot.content_digest,
        )


def test_snapshot_rejects_duplicate_and_unordered_entries() -> None:
    registry = EvidenceRegistry().register(_evidence("a")).register(_evidence("b"))
    snapshot = EvidenceSnapshot.create("snapshot", 1, registry)
    with pytest.raises(RelationshipIntegrityError):
        EvidenceSnapshot(
            snapshot.snapshot_id,
            snapshot.version,
            tuple(reversed(snapshot.entries)),
            snapshot.registry_digest,
            snapshot.content_digest,
        )

    forged_registry_digest = EvidenceDigest("f" * 64)
    forged_content_digest = EvidenceDigest.from_value(
        {
            "snapshot_id": snapshot.snapshot_id,
            "version": snapshot.version,
            "entries": [
                {"evidence": evidence.to_dict(), "state": state.value}
                for evidence, state in snapshot.entries
            ],
            "registry_digest": {
                "value": forged_registry_digest.value,
                "algorithm": forged_registry_digest.algorithm,
            },
        }
    )
    with pytest.raises(RelationshipIntegrityError, match="registry digest"):
        EvidenceSnapshot(
            snapshot.snapshot_id,
            snapshot.version,
            snapshot.entries,
            forged_registry_digest,
            forged_content_digest,
        )
    with pytest.raises(RelationshipIntegrityError):
        EvidenceSnapshot(
            snapshot.snapshot_id,
            snapshot.version,
            (snapshot.entries[0], snapshot.entries[0]),
            snapshot.registry_digest,
            snapshot.content_digest,
        )


def test_engine_registration_snapshot_audit_and_rejections() -> None:
    one = _evidence("a")
    two = _evidence("b")
    engine = EvidenceEngine().register(one).register(two)
    engine = engine.make_available("a")
    engine, snapshot = engine.snapshot("decision-evidence")
    assert engine.registry.entry("a").state is EvidenceLifecycleState.SNAPSHOTTED
    assert engine.registry.entry("b").state is EvidenceLifecycleState.REGISTERED
    assert snapshot.entries[0][0] == one
    audit = engine.audit()
    assert audit.statistics.total == 2
    assert audit.statistics.by_category == ((EvidenceCategory.MARKET_DATA.value, 2),)
    assert audit.statistics.by_source == (("feed-a", 2),)
    assert audit.registered_identifiers == ("a", "b")

    rejected, accepted = engine.try_register(one)
    assert not accepted
    assert rejected.audit().statistics.duplicate_rejections == 1
    invalid = replace(_evidence("bad"), content_digest=DecisionDigest("f" * 64))
    rejected, accepted = rejected.try_register(invalid)
    assert not accepted
    assert rejected.audit().statistics.validation_failures == 1
    assert len(rejected.audit().rejection_messages) == 2


def test_diagnostics_report_objective_inconsistencies_without_mutation() -> None:
    evidence = _evidence("a", dependencies=("missing",))
    registry = EvidenceRegistry().register(evidence)
    clean = EvidenceDiagnostics.inspect(EvidenceRegistry().register(_evidence("clean")))
    assert clean.is_consistent
    snapshot = EvidenceSnapshot.create("other", 1, EvidenceRegistry().register(_evidence("other")))
    diagnostics = EvidenceDiagnostics.inspect(registry, snapshot)
    assert diagnostics.invalid_references == ("a:missing",)
    assert diagnostics.inconsistencies == ("snapshot:other:registry-digest",)
    assert not diagnostics.is_consistent

    corrupted = replace(evidence)
    object.__setattr__(corrupted, "evidence_id", "")
    object.__setattr__(corrupted, "source", "")
    object.__setattr__(corrupted, "category", "unknown")
    object.__setattr__(corrupted, "content_digest", DecisionDigest("f" * 64))
    entry = registry.entries[0]
    object.__setattr__(entry, "evidence", corrupted)
    object.__setattr__(registry, "entries", (entry, entry))
    diagnostics = EvidenceDiagnostics.inspect(registry)
    assert diagnostics.duplicates == ("",)
    assert diagnostics.unknown_categories == ("<missing-id>",)
    assert diagnostics.missing_fields == ("<missing-id>",)
    assert diagnostics.inconsistencies == ("",)


def test_core_lazy_export_exposes_evidence_module() -> None:
    assert evidence_engine.EvidenceEngine is EvidenceEngine
