# mypy: disable-error-code="arg-type"
"""P02-F17 evidence freshness cardinality proofs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from epip.strategy_mapping import (
    AnalyticalSourceBinding,
    AnalyticalSourceKind,
    EvidenceRequirement,
    FreshnessBasis,
    FreshnessPolicy,
    InstrumentBinding,
    NonAcceptanceAction,
    RevisionIdentity,
    RuleIdentity,
    SemanticCandidate,
    SemanticValue,
    SemanticValueKind,
)
from epip.strategy_mapping._evidence_freshness import (
    _EvidenceFreshnessResolution,
    _resolve_evidence_freshness,
)
from epip.strategy_runtime.protocols import FactAdapterState
from epip.strategy_runtime.result import (
    DiagnosticSeverity,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
)
from epip.swing import SwingSequence

EVALUATION = "2026-01-01T10:00:00.000000Z"


def _policy(basis: FreshnessBasis = FreshnessBasis.OBSERVATION) -> FreshnessPolicy:
    return FreshnessPolicy(
        RuleIdentity("freshness", "1", "p02-f00-v1", "a" * 64),
        basis,
        60,
        NonAcceptanceAction.REJECT,
    )


def _source(
    name: str,
    *,
    observation: str = "2026-01-01T09:59:30Z",
    availability: str | None = None,
    timeframe: str = "H1",
) -> AnalyticalSourceBinding:
    instrument = InstrumentBinding.create("instrument", "EURUSD", (), "1")
    available = observation if availability is None else availability
    return AnalyticalSourceBinding.create(
        source_kind=AnalyticalSourceKind.SWING,
        source_contract_version="1",
        source_object_id=name,
        instrument=instrument,
        timeframe=timeframe,
        observation_timestamp=observation,
        availability_timestamp=available,
        as_of_timestamp=max(EVALUATION, observation, available),
        revision=RevisionIdentity(name, f"revision-{name}", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref=name,
        payload=SwingSequence("EURUSD", timeframe, ()),
    )


def _candidate(source: AnalyticalSourceBinding, value: float = 1.0) -> SemanticCandidate:
    return SemanticCandidate.create(
        source_binding_id=source.source_binding_id,
        provenance_ref=source.provenance_ref,
        instrument_binding_id=source.instrument.binding_id,
        timeframe=source.timeframe,
        source_rule_identity=RuleIdentity("extract", "1", "p02-f00-v1", "b" * 64),
        value=SemanticValue(SemanticValueKind.FINITE_FLOAT, float_value=value),
    )


def _resolve(
    sources: tuple[AnalyticalSourceBinding, ...],
    *,
    candidates: tuple[SemanticCandidate, ...] | None = None,
    basis: FreshnessBasis = FreshnessBasis.OBSERVATION,
    requirement: EvidenceRequirement = EvidenceRequirement.REQUIRED,
) -> _EvidenceFreshnessResolution:
    selected = candidates or tuple(
        _candidate(source, float(index + 1)) for index, source in enumerate(sources)
    )
    return _resolve_evidence_freshness(
        evidence_key="evidence",
        selected_candidates=selected,
        source_bindings=sources,
        policy=_policy(basis),
        evaluation_timestamp=EVALUATION,
        requirement=requirement,
    )


@pytest.mark.parametrize("requirement", list(EvidenceRequirement))
def test_single_fresh_source_is_included(requirement: EvidenceRequirement) -> None:
    result = _resolve((_source("fresh"),), requirement=requirement)
    assert result.fresh is True
    assert result.omitted is False
    assert result.terminal_state is None
    assert result.diagnostics == ()


@pytest.mark.parametrize(
    ("requirement", "omitted", "terminal", "severity"),
    [
        (EvidenceRequirement.REQUIRED, False, FactAdapterState.REJECTED, DiagnosticSeverity.ERROR),
        (EvidenceRequirement.OPTIONAL, True, None, DiagnosticSeverity.WARNING),
    ],
)
def test_single_stale_source_uses_governed_consequence(
    requirement: EvidenceRequirement,
    omitted: bool,
    terminal: FactAdapterState | None,
    severity: DiagnosticSeverity,
) -> None:
    source = _source("stale", observation="2026-01-01T09:58:59Z")
    result = _resolve((source,), requirement=requirement)
    assert (result.fresh, result.omitted, result.terminal_state) == (False, omitted, terminal)
    assert result.stale_source_binding_ids == (source.source_binding_id,)
    assert result.diagnostics[0].severity is severity


@pytest.mark.parametrize(
    ("ages", "expected"),
    [
        ((30, 45), True),
        ((30, 61), False),
        ((61, 90), False),
        ((1, 30, 60), True),
        ((1, 61, 2), False),
    ],
)
def test_all_reduction_for_multiple_sources(ages: tuple[int, ...], expected: bool) -> None:
    evaluation = datetime.fromisoformat(EVALUATION).astimezone(UTC)
    sources = tuple(
        _source(
            f"source-{index}",
            observation=(evaluation - timedelta(seconds=age)).isoformat().replace("+00:00", "Z"),
        )
        for index, age in enumerate(ages)
    )
    result = _resolve(sources)
    assert result.fresh is expected


def test_core_mixed_case_has_no_privileged_source() -> None:
    sources = (
        _source("a"),
        _source("b", observation="2026-01-01T09:58:00Z"),
        _source("c"),
    )
    result = _resolve(sources)
    assert result.fresh is False
    assert result.stale_source_binding_ids == (sources[1].source_binding_id,)


@pytest.mark.parametrize("basis", list(FreshnessBasis))
def test_each_basis_uses_only_its_configured_timestamp(basis: FreshnessBasis) -> None:
    source = _source(
        "basis",
        observation="2026-01-01T09:58:00Z",
        availability="2026-01-01T09:59:30Z",
    )
    assert _resolve((source,), basis=basis).fresh is (basis is FreshnessBasis.AVAILABILITY)


@pytest.mark.parametrize("basis", list(FreshnessBasis))
def test_exact_threshold_is_fresh_and_next_second_is_stale(basis: FreshnessBasis) -> None:
    exact = _source(
        "exact", observation="2026-01-01T09:59:00Z", availability="2026-01-01T09:59:00Z"
    )
    stale = _source(
        "stale", observation="2026-01-01T09:58:59Z", availability="2026-01-01T09:58:59Z"
    )
    assert _resolve((exact,), basis=basis).fresh is True
    assert _resolve((stale,), basis=basis).fresh is False


@pytest.mark.parametrize("basis", list(FreshnessBasis))
def test_future_selected_timestamp_is_invalid(basis: FreshnessBasis) -> None:
    source = _source(
        "future", observation="2026-01-01T10:00:01Z", availability="2026-01-01T10:00:01Z"
    )
    result = _resolve((source,), basis=basis, requirement=EvidenceRequirement.OPTIONAL)
    assert result.terminal_state is FactAdapterState.INVALID_INPUT
    assert result.fresh is None and not result.omitted


@pytest.mark.parametrize("field", ["observation_timestamp", "availability_timestamp"])
def test_malformed_selected_timestamp_is_invalid(field: str) -> None:
    source = _source("malformed")
    object.__setattr__(source, field, "not-a-timestamp")
    basis = (
        FreshnessBasis.OBSERVATION
        if field.startswith("observation")
        else FreshnessBasis.AVAILABILITY
    )
    result = _resolve((source,), basis=basis)
    assert result.terminal_state is FactAdapterState.INVALID_INPUT


def test_selected_subset_ignores_unselected_stale_source() -> None:
    fresh_a, fresh_b = _source("a"), _source("b")
    stale = _source("unselected", observation="2026-01-01T09:00:00Z")
    selected = (_candidate(fresh_a), _candidate(fresh_b))
    result = _resolve((fresh_a, fresh_b), candidates=selected)
    assert result.fresh is True
    assert stale.source_binding_id not in result.evaluated_source_binding_ids


def test_duplicate_candidate_lineage_is_evaluated_once_per_source() -> None:
    source_x, source_y = _source("x"), _source("y")
    candidates = (_candidate(source_x, 1.0), _candidate(source_x, 2.0), _candidate(source_y, 3.0))
    result = _resolve((source_y, source_x), candidates=candidates)
    assert result.fresh is True
    assert result.evaluated_source_binding_ids == tuple(
        sorted((source_x.source_binding_id, source_y.source_binding_id))
    )


def test_duplicate_equal_source_bindings_are_deduplicated() -> None:
    source = _source("same")
    result = _resolve((source, source), candidates=(_candidate(source),))
    assert result.fresh is True
    assert result.evaluated_source_binding_ids == (source.source_binding_id,)


def test_different_sources_with_same_timestamp_remain_distinct() -> None:
    source_a, source_b = _source("a"), _source("b")
    result = _resolve((source_a, source_b))
    assert len(result.evaluated_source_binding_ids) == 2


def test_order_independence_and_repeated_determinism() -> None:
    source_a = _source("a")
    source_b = _source("b", observation="2026-01-01T09:58:00Z")
    first = _resolve((source_a, source_b))
    second = _resolve(
        (source_b, source_a), candidates=(_candidate(source_b, 2.0), _candidate(source_a, 1.0))
    )
    assert first == second == _resolve((source_a, source_b))


@pytest.mark.parametrize(
    ("candidates", "sources"),
    [((), ()), ((), (_source("orphan"),))],
)
def test_empty_selection_fails_closed(
    candidates: tuple[SemanticCandidate, ...],
    sources: tuple[AnalyticalSourceBinding, ...],
) -> None:
    result = _resolve_evidence_freshness(
        evidence_key="evidence",
        selected_candidates=candidates,
        source_bindings=sources,
        policy=_policy(),
        evaluation_timestamp=EVALUATION,
        requirement=EvidenceRequirement.REQUIRED,
    )
    assert result.terminal_state is FactAdapterState.INVALID_INPUT


def test_full_invalidity_scan_outranks_staleness_in_every_order() -> None:
    stale = _source("stale", observation="2026-01-01T09:00:00Z")
    future = _source(
        "future", observation="2026-01-01T10:00:01Z", availability="2026-01-01T10:00:01Z"
    )
    for sources in ((stale, future), (future, stale)):
        result = _resolve(sources, requirement=EvidenceRequirement.OPTIONAL)
        assert result.terminal_state is FactAdapterState.INVALID_INPUT
        assert result.fresh is None and not result.omitted


def test_lineage_mismatch_and_unselected_binding_fail_closed() -> None:
    source_a, source_b = _source("a"), _source("b")
    wrong = _candidate(source_a)
    object.__setattr__(wrong, "provenance_ref", "wrong")
    assert (
        _resolve((source_a,), candidates=(wrong,)).terminal_state is FactAdapterState.INVALID_INPUT
    )
    assert (
        _resolve((source_a, source_b), candidates=(_candidate(source_a),)).terminal_state
        is FactAdapterState.INVALID_INPUT
    )


def test_diagnostics_are_sanitized_and_lineage_aware() -> None:
    source = _source("stale-source", observation="2026-01-01T09:00:00Z")
    result = _resolve((source,))
    diagnostic = result.diagnostics[0]
    assert diagnostic.code is RuntimeDiagnosticCode.TEMPORAL_FAILURE
    assert diagnostic.stage is RuntimeDiagnosticStage.TEMPORAL
    assert diagnostic.subject_ref == "evidence"
    assert diagnostic.source_refs == ("stale-source",)
    assert diagnostic.message == "TEMPORAL_FAILURE"


def test_naive_evaluation_and_source_timestamps_are_invalid() -> None:
    source = _source("naive")
    object.__setattr__(source, "observation_timestamp", "2026-01-01T09:59:30")
    assert _resolve((source,)).terminal_state is FactAdapterState.INVALID_INPUT
    result = _resolve_evidence_freshness(
        evidence_key="evidence",
        selected_candidates=(_candidate(_source("valid")),),
        source_bindings=(_source("valid"),),
        policy=_policy(),
        evaluation_timestamp="2026-01-01T10:00:00",
        requirement=EvidenceRequirement.REQUIRED,
    )
    assert result.terminal_state is FactAdapterState.INVALID_INPUT


def test_helper_is_private_and_does_not_expand_public_contracts() -> None:
    import epip.strategy_mapping as public
    from epip.strategy_mapping import resolved_rules, serialization, source_resolution

    assert "_resolve_evidence_freshness" not in public.__all__
    assert not hasattr(public, "EvidenceFreshnessResolution")
    assert (
        "freshness"
        not in resolved_rules.ResolvedSemanticRuleSet.validate_profile_closure.__code__.co_names
    )
    assert not hasattr(serialization, "EvidenceFreshnessResolution")
    assert source_resolution.__all__ == ["resolve_source_bindings"]
