# mypy: disable-error-code="arg-type,unused-ignore,no-untyped-def"
from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from epip.a07.foundation import StrategyIdentity
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_mapping._base import exact_tuple
from epip.strategy_runtime._base import CONTRACT_VERSION
from epip.strategy_runtime.context import EvaluationContext, RuntimeMode
from epip.strategy_runtime.mtf import MultiTimeframeInputSet, TimeframeInput, TimeframeRole
from epip.strategy_runtime.profile import StrategyProfile
from epip.strategy_runtime.provenance import (
    FactAdapterIdentity,
    FactProvenance,
    ProvenanceManifest,
    SourceProvenance,
)
from epip.swing import SwingSequence


def instrument(symbol: str = "EURUSD", identity: str = "eurusd") -> InstrumentBinding:
    return InstrumentBinding.create(identity, symbol, (InstrumentAlias("feed", "EUR/USD"),), "1")


def parent_profile() -> StrategyProfile:
    return StrategyProfile.create(
        profile_id="parent",
        profile_version="1",
        strategy_identity=StrategyIdentity("s", "1"),
        compatible_runtime_contract_versions=(CONTRACT_VERSION,),
        compatible_adapter_contract_versions=(FOUNDATION_SCHEMA_VERSION,),
        required_source_domains=("SWING",),
        optional_source_domains=(),
        required_evidence_keys=("key",),
        optional_evidence_keys=(),
        enabled_direction_facts=("PRIMARY",),
        enabled_geometry_sources=("SWING",),
        confidence_model_reference="confidence",
        evidence_taxonomy_reference="taxonomy",
        mtf_requirement="mtf",
        mapping_rules_reference="mapping",
    )


def context(**overrides: object) -> EvaluationContext:
    values: dict[str, object] = {
        "instrument_id": "eurusd",
        "symbol": "EURUSD",
        "primary_timeframe": "H1",
        "evaluation_timestamp": "2026-01-01T10:03:00+00:00",
        "event_timestamp": "2026-01-01T10:00:00Z",
        "receipt_timestamp": None,
        "runtime_mode": RuntimeMode.HISTORICAL,
        "profile_identity": parent_profile().identity,
        "source_set_id": "set",
        "run_id": "run",
    }
    values.update(overrides)
    return EvaluationContext.create(**values)  # type: ignore[arg-type]


def source(**overrides: object) -> AnalyticalSourceBinding:
    values: dict[str, object] = {
        "source_kind": AnalyticalSourceKind.SWING,
        "source_contract_version": "swing-v1",
        "source_object_id": "swing-1",
        "instrument": instrument(),
        "timeframe": "H1",
        "observation_timestamp": "2026-01-01T10:00:00+00:00",
        "availability_timestamp": "2026-01-01T10:01:00+00:00",
        "as_of_timestamp": "2026-01-01T10:02:00+00:00",
        "revision": RevisionIdentity("series", "revision-1", 0, None),
        "superseded_at": None,
        "closed": True,
        "provenance_ref": "swing-1",
        "payload": SwingSequence("EURUSD", "H1", ()),
    }
    values.update(overrides)
    return AnalyticalSourceBinding.create(**values)  # type: ignore[arg-type]


def manifest(ctx: EvaluationContext | None = None) -> ProvenanceManifest:
    ctx = ctx or context()
    src = SourceProvenance(
        "SWING",
        "epip.swing.models.SwingSequence",
        "swing-v1",
        "swing-1",
        "2026-01-01T10:00:00Z",
        "1",
        None,
        "b" * 64,
    )
    adapter = FactAdapterIdentity("adapter", "1", CONTRACT_VERSION, "c" * 64)
    fact = FactProvenance(
        "key",
        ("swing-1",),
        "adapter",
        "1",
        ctx.profile_identity.profile_id,
        ctx.profile_identity.profile_version,
        "rule",
        "1",
        "d" * 64,
    )
    return ProvenanceManifest.create(
        (src,), (fact,), ctx.profile_identity, adapter, ctx.evaluation_id
    )


def timeframe() -> TimeframeInput:
    return TimeframeInput(
        "H1",
        TimeframeRole.PRIMARY,
        "2026-01-01T09:00:00Z",
        "2026-01-01T10:00:00Z",
        "2026-01-01T10:02:00Z",
        True,
        ("swing-1",),
        ("swing-1",),
    )


def test_instrument_binding_identity_aliases_and_failures() -> None:
    obj = instrument()
    assert obj.admits(None, "EURUSD") and obj.admits("feed", "EUR/USD")
    assert not obj.admits("feed", "GBP/USD")
    assert hash(obj.aliases[0]) and len(obj.binding_id) == 64
    with pytest.raises(FrozenInstanceError):
        obj.instrument_id = "x"  # type: ignore[misc]
    for aliases in (
        (InstrumentAlias("feed", "A"), InstrumentAlias("feed", "B")),
        (InstrumentAlias("feed", "A"),) * 2,
    ):
        with pytest.raises(DataIntegrityError):
            InstrumentBinding.create("id", "X", aliases, "1")  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        InstrumentBinding.create("id", "X", (object(),), "1")  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        replace(obj, binding_id="0" * 64)
    with pytest.raises(DataIntegrityError):
        replace(obj, aliases=(object(),))


def test_revision_and_source_timestamp_contracts() -> None:
    obj = source()
    assert obj.observation_timestamp.endswith(".000000Z")
    assert obj.canonical_key()[-1] == "revision-1"
    with pytest.raises(DataIntegrityError):
        RevisionIdentity("s", "r", -1, None)
    with pytest.raises(DataIntegrityError):
        RevisionIdentity("s", "r", 0, "r")
    with pytest.raises(DataIntegrityError):
        RevisionIdentity("s", "r", 0, "old")
    for kwargs in (
        {"payload": object()},
        {"availability_timestamp": "2026-01-01T09:59:00Z"},
        {"as_of_timestamp": "2026-01-01T10:00:30Z"},
        {"closed": False},
        {"payload": SwingSequence("GBPUSD", "H1", ())},
        {"payload": SwingSequence("EURUSD", "M5", ())},
        {"superseded_at": "2026-01-01T10:00:30Z"},
    ):
        with pytest.raises(DataIntegrityError):
            source(**kwargs)
    with pytest.raises(DataIntegrityError):
        replace(obj, source_contract="wrong")
    with pytest.raises(DataIntegrityError):
        replace(obj, payload=object())
    with pytest.raises(DataIntegrityError):
        replace(obj, source_binding_id="0" * 64)
    with pytest.raises(DataIntegrityError):
        exact_tuple([], InstrumentAlias, "aliases")
    with pytest.raises(DataIntegrityError):
        exact_tuple((), InstrumentAlias, "aliases", empty=False)
    assert exact_tuple((obj.instrument.aliases[0],), InstrumentAlias, "aliases")


def test_source_context_provenance_and_lookahead() -> None:
    obj, ctx, proof = source(), context(), manifest()
    obj.validate_for(ctx, proof)
    equal = source(
        availability_timestamp=ctx.evaluation_timestamp, as_of_timestamp=ctx.evaluation_timestamp
    )
    equal.validate_for(ctx, proof)
    for candidate in (
        source(
            availability_timestamp="2026-01-01T10:04:00Z", as_of_timestamp="2026-01-01T10:04:00Z"
        ),
        source(as_of_timestamp="2026-01-01T10:04:00Z"),
        source(superseded_at="2026-01-01T10:02:00Z"),
    ):
        with pytest.raises(DataIntegrityError):
            candidate.validate_for(ctx, proof)
    with pytest.raises(DataIntegrityError):
        obj.validate_for(context(instrument_id="other"), proof)
    with pytest.raises(DataIntegrityError):
        obj.validate_for(ctx, manifest(context(run_id="other")))
    with pytest.raises(DataIntegrityError):
        source(provenance_ref="missing").validate_for(ctx, proof)
    mismatched = replace(proof.sources[0], source_contract_version="other")
    bad_proof = ProvenanceManifest.create(
        (mismatched,),
        proof.facts,
        proof.profile_identity,
        proof.adapter_identity,
        proof.evaluation_id,
    )
    with pytest.raises(DataIntegrityError):
        obj.validate_for(ctx, bad_proof)


def test_typed_frame_and_bundle_contract() -> None:
    src, frame = source(), timeframe()
    typed = TimeframeAnalyticalFrame.create(frame, (src,), ("swing-1",))
    coherence = MultiTimeframeInputSet.create("H1", "2026-01-01T10:02:00.000000Z", (frame,))
    proof, ctx = manifest(), context()
    bundle = MultiTimeframeAnalyticalBundle.create(
        instrument(), coherence, (typed,), proof.manifest_id
    )
    bundle.validate_for(ctx, proof)
    assert bundle.frames == (typed,)
    for kwargs in (
        {"sources": ()},
        {"sources": (src, src)},
        {"provenance_refs": ("bad",)},
        {"provenance_refs": ["swing-1"]},
        {"frame_id": "0" * 64},
    ):
        with pytest.raises(DataIntegrityError):
            replace(typed, **kwargs)
    with pytest.raises(DataIntegrityError):
        replace(bundle, frames=())
    with pytest.raises(DataIntegrityError):
        replace(bundle, frames=[])
    with pytest.raises(DataIntegrityError):
        replace(typed, frame=replace(frame, source_refs=("other",)))
    wrong = source(timeframe="M5", payload=SwingSequence("EURUSD", "M5", ()))
    with pytest.raises(DataIntegrityError):
        replace(typed, sources=(wrong,), provenance_refs=("swing-1",))
    with pytest.raises(DataIntegrityError):
        replace(bundle, bundle_id="0" * 64)
    with pytest.raises(DataIntegrityError):
        replace(bundle, instrument=instrument(identity="other"))
    higher = TimeframeInput(
        "H4",
        TimeframeRole.HIGHER,
        "2026-01-01T06:00:00Z",
        "2026-01-01T10:00:00Z",
        "2026-01-01T10:02:00Z",
        True,
        ("swing-1",),
        ("swing-1",),
    )
    extra = MultiTimeframeInputSet.create("H1", "2026-01-01T10:02:00.000000Z", (frame, higher))
    with pytest.raises(DataIntegrityError):
        MultiTimeframeAnalyticalBundle.create(instrument(), extra, (typed,), proof.manifest_id)
    future = source(
        availability_timestamp="2026-01-01T10:03:00Z",
        as_of_timestamp="2026-01-01T10:03:00Z",
    )
    future_frame = TimeframeAnalyticalFrame.create(frame, (future,), ("swing-1",))
    with pytest.raises(DataIntegrityError):
        MultiTimeframeAnalyticalBundle.create(
            instrument(), coherence, (future_frame,), proof.manifest_id
        )
    with pytest.raises(DataIntegrityError):
        MultiTimeframeAnalyticalBundle.create(
            instrument(), coherence, (typed,), "wrong"
        ).validate_for(ctx, proof)
    with pytest.raises(DataIntegrityError):
        MultiTimeframeAnalyticalBundle.create(
            instrument(identity="other"), coherence, (typed,), proof.manifest_id
        ).validate_for(ctx, proof)
    other_instrument = instrument(identity="other")
    other_source = source(instrument=other_instrument)
    other_typed = TimeframeAnalyticalFrame.create(frame, (other_source,), ("swing-1",))
    other_bundle = MultiTimeframeAnalyticalBundle.create(
        other_instrument, coherence, (other_typed,), proof.manifest_id
    )
    with pytest.raises(DataIntegrityError):
        other_bundle.validate_for(ctx, proof)
    with pytest.raises(DataIntegrityError):
        bundle.validate_for(context(primary_timeframe="M5"), proof)


@pytest.mark.parametrize("obj_factory", [instrument, source])
def test_serialization_round_trip_and_tamper(obj_factory) -> None:
    obj = obj_factory()
    encoded = to_json(obj)
    assert from_json(type(obj), encoded) == obj
    assert from_dict(type(obj), to_dict(obj)) == obj
    payload = copy.deepcopy(to_dict(obj))
    identity = "binding_id" if isinstance(obj, InstrumentBinding) else "source_binding_id"
    payload["fields"][identity] = "0" * 64
    with pytest.raises(DataIntegrityError):
        from_dict(type(obj), payload)
    with pytest.raises(DataIntegrityError):
        from_json(type(obj), "[]")


def test_dependency_and_phase_isolation() -> None:
    forbidden = {"epip.risk", "epip.execution", "epip.portfolio", "random", "time", "os"}
    for path in Path("epip/strategy_mapping").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        assert not forbidden & imports
    adapter = Path("epip/strategy_mapping/adapter.py")
    assert adapter.exists()
    tree = ast.parse(adapter.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not forbidden & imports
    assert not Path("epip/strategy_mapping/runtime.py").exists()
