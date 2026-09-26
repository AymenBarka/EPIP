# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def,misc"
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pytest

import epip.strategy_mapping.rule_requests as request_module
from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.fibonacci import (
    FibonacciDirection,
    FibonacciExtension,
    FibonacciRetracement,
    FibonacciSnapshot,
)
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import TimeframeRole
from epip.swing import SwingSequence


def _instrument(identity: str = "eurusd") -> InstrumentBinding:
    return InstrumentBinding.create(identity, "EURUSD", (), "1")


def _source(
    index: int = 1,
    *,
    fibonacci: bool = False,
    instrument: InstrumentBinding | None = None,
    timeframe: str = "H1",
) -> AnalyticalSourceBinding:
    instrument = _instrument() if instrument is None else instrument
    source_id = f"source-{index}"
    payload: FibonacciSnapshot | SwingSequence
    if fibonacci:
        direction = FibonacciDirection.BULLISH
        payload = FibonacciSnapshot(
            "2026-01-01T10:00:00Z",
            "EURUSD",
            timeframe,
            1,
            direction,
            FibonacciRetracement(100.0, 120.0, direction, ()),
            FibonacciExtension(100.0, 120.0, ()),
            (),
        )
        kind = AnalyticalSourceKind.FIBONACCI
        version = "fibonacci-v1"
    else:
        payload = SwingSequence("EURUSD", timeframe, ())
        kind = AnalyticalSourceKind.SWING
        version = "swing-v1"
    return AnalyticalSourceBinding.create(
        source_kind=kind,
        source_contract_version=version,
        source_object_id=source_id,
        instrument=instrument,
        timeframe=timeframe,
        observation_timestamp="2026-01-01T10:00:00Z",
        availability_timestamp="2026-01-01T10:01:00Z",
        as_of_timestamp="2026-01-01T10:02:00Z",
        revision=RevisionIdentity(f"series-{index}", f"revision-{index}", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref=source_id,
        payload=payload,
    )


def _context(rule, semantic_profile, sources):
    return SemanticRuleInvocationContext(
        "evaluation",
        "2026-01-01T10:03:00Z",
        semantic_profile.identity,
        rule,
        sources[0].instrument.binding_id,
        "H1",
        TimeframeRole.PRIMARY,
        tuple(source.source_binding_id for source in sources),
        tuple(source.provenance_ref for source in sources),
    )


def _candidate(
    rule,
    source,
    value: float = 1.0,
    role=SemanticCandidateRole.ANCHOR_START,
    fact=None,
):
    return SemanticCandidate.create(
        source_binding_id=source.source_binding_id,
        provenance_ref=source.provenance_ref,
        instrument_binding_id=source.instrument.binding_id,
        timeframe=source.timeframe,
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=value),
        role=role,
        fact_identity=fact,
    )


def test_exact_shape_one_candidate_immutability_and_direction(rule, semantic_profile):
    source = _source()
    candidate = _candidate(rule, source)
    request = DirectionalCandidateSourceSetRequest(
        _context(rule, semantic_profile, (source,)),
        (candidate,),
        (source,),
        StrategyDirection.BUY,
    )
    assert tuple(field.name for field in fields(request)) == (
        "context",
        "candidates",
        "sources",
        "direction",
    )
    assert request.direction is StrategyDirection.BUY
    with pytest.raises(FrozenInstanceError):
        request.direction = StrategyDirection.SELL


def test_two_role_addressed_anchors_and_typed_fibonacci_source(rule, semantic_profile):
    source = _source(fibonacci=True)
    candidates = (
        _candidate(rule, source, 100.0, SemanticCandidateRole.ANCHOR_START),
        _candidate(rule, source, 120.0, SemanticCandidateRole.ANCHOR_END),
    )
    request = DirectionalCandidateSourceSetRequest(
        _context(rule, semantic_profile, (source,)),
        candidates,
        (source,),
        StrategyDirection.BUY,
    )
    assert {candidate.role for candidate in request.candidates} == {
        SemanticCandidateRole.ANCHOR_START,
        SemanticCandidateRole.ANCHOR_END,
    }
    assert request.sources[0].source_kind is AnalyticalSourceKind.FIBONACCI
    assert type(request.sources[0].payload) is FibonacciSnapshot


def test_same_value_different_fact_identities_are_distinct(rule, semantic_profile):
    source = _source()
    candidates = tuple(
        _candidate(
            rule,
            source,
            fact=SemanticFactIdentity("example.domain", name, "1"),
        )
        for name in ("first-state", "second-state")
    )
    request = DirectionalCandidateSourceSetRequest(
        _context(rule, semantic_profile, (source,)),
        candidates,
        (source,),
        StrategyDirection.BUY,
    )
    assert len(request.candidates) == 2
    assert {item.fact_identity for item in request.candidates} == {
        SemanticFactIdentity("example.domain", "first-state", "1"),
        SemanticFactIdentity("example.domain", "second-state", "1"),
    }


def test_candidate_and_source_permutations_are_canonical(rule, semantic_profile):
    sources = (_source(1), _source(2))
    candidates = (
        _candidate(rule, sources[0], 1.0),
        _candidate(rule, sources[1], 2.0, SemanticCandidateRole.ANCHOR_END),
    )
    context = _context(rule, semantic_profile, sources)
    forward = DirectionalCandidateSourceSetRequest(
        context, candidates, sources, StrategyDirection.SELL
    )
    reverse = DirectionalCandidateSourceSetRequest(
        context, candidates[::-1], sources[::-1], StrategyDirection.SELL
    )
    assert forward == reverse and hash(forward) == hash(reverse)
    assert to_json(forward) == to_json(reverse)
    assert from_json(DirectionalCandidateSourceSetRequest, to_json(reverse)) == forward
    assert tuple(item.candidate_id for item in forward.candidates) == tuple(
        sorted(item.candidate_id for item in candidates)
    )
    assert tuple(item.source_binding_id for item in forward.sources) == tuple(
        sorted(item.source_binding_id for item in sources)
    )


def test_populations_are_non_empty_exact_typed_tuples(rule, semantic_profile):
    source = _source()
    candidate = _candidate(rule, source)
    context = _context(rule, semantic_profile, (source,))
    for candidates, sources in (
        ((), (source,)),
        ((candidate,), ()),
        ([candidate], (source,)),
        ((candidate,), [source]),
        ((object(),), (source,)),
        ((candidate,), (object(),)),
    ):
        with pytest.raises(DataIntegrityError):
            DirectionalCandidateSourceSetRequest(
                context, candidates, sources, StrategyDirection.BUY
            )


def test_duplicate_candidate_and_source_identities_fail_closed(rule, semantic_profile, monkeypatch):
    source = _source()
    candidate = _candidate(rule, source, fact=SemanticFactIdentity("example.domain", "state", "1"))
    context = _context(rule, semantic_profile, (source,))

    def forbidden_sort(*args, **kwargs):
        pytest.fail("invalid population reached sorting")

    monkeypatch.setattr(request_module, "sorted", forbidden_sort, raising=False)
    with pytest.raises(DataIntegrityError, match="duplicate candidates"):
        DirectionalCandidateSourceSetRequest(
            context, (candidate, candidate), (source,), StrategyDirection.BUY
        )
    with pytest.raises(DataIntegrityError, match="duplicate source bindings"):
        DirectionalCandidateSourceSetRequest(
            context, (candidate,), (source, source), StrategyDirection.BUY
        )


def test_candidate_must_reference_a_supplied_source(rule, semantic_profile):
    sources = (_source(1), _source(2))
    candidate = _candidate(rule, sources[1])
    with pytest.raises(DataIntegrityError):
        DirectionalCandidateSourceSetRequest(
            _context(rule, semantic_profile, sources),
            (candidate,),
            sources[:1],
            StrategyDirection.BUY,
        )


@pytest.mark.parametrize(
    "candidate_change",
    [
        {"source_binding_id": "missing"},
        {"provenance_ref": "missing"},
        {"instrument_binding_id": "missing"},
        {"timeframe": "M5"},
    ],
)
def test_candidate_context_relationships_fail_closed(rule, semantic_profile, candidate_change):
    source = _source()
    values = {
        "source_binding_id": source.source_binding_id,
        "provenance_ref": source.provenance_ref,
        "instrument_binding_id": source.instrument.binding_id,
        "timeframe": source.timeframe,
    }
    values.update(candidate_change)
    candidate = SemanticCandidate.create(
        **values,
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=1.0),
    )
    with pytest.raises(DataIntegrityError):
        DirectionalCandidateSourceSetRequest(
            _context(rule, semantic_profile, (source,)),
            (candidate,),
            (source,),
            StrategyDirection.BUY,
        )


@pytest.mark.parametrize("mismatch", ["binding", "provenance", "instrument", "timeframe"])
def test_source_context_relationships_fail_closed(rule, semantic_profile, mismatch, monkeypatch):
    source = _source()
    extra = _source(
        2,
        instrument=_instrument("other") if mismatch == "instrument" else None,
        timeframe="M5" if mismatch == "timeframe" else "H1",
    )
    context = _context(rule, semantic_profile, (source, extra))
    if mismatch == "binding":
        context = replace(context, source_binding_ids=(source.source_binding_id,))
    if mismatch == "provenance":
        context = replace(context, provenance_refs=(source.provenance_ref,))
    candidate = _candidate(rule, source)

    def forbidden_sort(*args, **kwargs):
        pytest.fail("invalid source relationship reached sorting")

    monkeypatch.setattr(request_module, "sorted", forbidden_sort, raising=False)
    with pytest.raises(DataIntegrityError, match="source does not match invocation context"):
        DirectionalCandidateSourceSetRequest(
            context, (candidate,), (source, extra), StrategyDirection.BUY
        )


def test_exact_source_provenance_is_validated_before_sorting(rule, semantic_profile, monkeypatch):
    sources = (_source(1), _source(2))
    context = _context(rule, semantic_profile, sources)
    candidate = SemanticCandidate.create(
        source_binding_id=sources[0].source_binding_id,
        provenance_ref=sources[1].provenance_ref,
        instrument_binding_id=sources[0].instrument.binding_id,
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=1.0),
    )

    def forbidden_sort(*args, **kwargs):
        pytest.fail("invalid precise-source provenance reached sorting")

    monkeypatch.setattr(request_module, "sorted", forbidden_sort, raising=False)
    with pytest.raises(DataIntegrityError, match="provenance does not match its exact source"):
        DirectionalCandidateSourceSetRequest(context, (candidate,), sources, StrategyDirection.BUY)


def test_producer_identities_are_preserved_independently_of_consumer(rule, semantic_profile):
    source = _source()
    other_producer = replace(rule, rule_id="other-producer")
    consumer = replace(rule, rule_id="consumer")
    candidates = (_candidate(rule, source), _candidate(other_producer, source))
    request = DirectionalCandidateSourceSetRequest(
        _context(consumer, semantic_profile, (source,)),
        candidates,
        (source,),
        StrategyDirection.BUY,
    )
    assert {item.source_rule_identity for item in request.candidates} == {rule, other_producer}
    assert request.context.rule_identity == consumer


def test_exact_types_and_serialization_round_trip(rule, semantic_profile):
    source = _source()
    candidate = _candidate(
        rule,
        source,
        fact=SemanticFactIdentity("example.domain", "state", "1"),
    )
    request = DirectionalCandidateSourceSetRequest(
        _context(rule, semantic_profile, (source,)),
        (candidate,),
        (source,),
        StrategyDirection.BUY,
    )
    assert from_json(DirectionalCandidateSourceSetRequest, to_json(request)) == request
    assert from_dict(DirectionalCandidateSourceSetRequest, to_dict(request)) == request
    for change in (
        {"context": object()},
        {"direction": "BUY"},
    ):
        with pytest.raises(DataIntegrityError):
            DirectionalCandidateSourceSetRequest(
                change.get("context", request.context),
                request.candidates,
                request.sources,
                change.get("direction", request.direction),
            )
