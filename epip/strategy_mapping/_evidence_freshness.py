"""Private deterministic freshness reduction for mapped evidence lineage."""

from __future__ import annotations

from typing import NamedTuple

from epip.strategy_mapping._base import instant, timestamp
from epip.strategy_mapping.evidence_policy import (
    EvidenceRequirement,
    FreshnessBasis,
    FreshnessPolicy,
)
from epip.strategy_mapping.rule_values import SemanticCandidate
from epip.strategy_mapping.source_binding import AnalyticalSourceBinding
from epip.strategy_runtime.protocols import FactAdapterState
from epip.strategy_runtime.result import (
    DiagnosticSeverity,
    RuntimeDiagnostic,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
)


class _EvidenceFreshnessResolution(NamedTuple):
    fresh: bool | None
    omitted: bool
    terminal_state: FactAdapterState | None
    diagnostics: tuple[RuntimeDiagnostic, ...]
    evaluated_source_binding_ids: tuple[str, ...]
    stale_source_binding_ids: tuple[str, ...]


def _diagnostic(
    evidence_key: str,
    source_refs: tuple[str, ...],
    *,
    severity: DiagnosticSeverity,
) -> RuntimeDiagnostic:
    return RuntimeDiagnostic(
        RuntimeDiagnosticCode.TEMPORAL_FAILURE,
        RuntimeDiagnosticStage.TEMPORAL,
        severity,
        evidence_key,
        source_refs,
        RuntimeDiagnosticCode.TEMPORAL_FAILURE.value,
    )


def _invalid(
    evidence_key: object, source_refs: tuple[str, ...] = ()
) -> _EvidenceFreshnessResolution:
    subject = evidence_key if type(evidence_key) is str and evidence_key.strip() else "evidence"
    refs = tuple(sorted({item for item in source_refs if type(item) is str and item.strip()}))
    return _EvidenceFreshnessResolution(
        None,
        False,
        FactAdapterState.INVALID_INPUT,
        (_diagnostic(subject, refs, severity=DiagnosticSeverity.ERROR),),
        (),
        (),
    )


def _resolve_evidence_freshness(
    *,
    evidence_key: str,
    selected_candidates: tuple[SemanticCandidate, ...],
    source_bindings: tuple[AnalyticalSourceBinding, ...],
    policy: FreshnessPolicy,
    evaluation_timestamp: str,
    requirement: EvidenceRequirement,
) -> _EvidenceFreshnessResolution:
    """Reduce mapped selected sources using the frozen all-sources-fresh invariant."""
    if (
        type(evidence_key) is not str
        or not evidence_key.strip()
        or type(selected_candidates) is not tuple
        or not selected_candidates
        or any(type(item) is not SemanticCandidate for item in selected_candidates)
        or type(source_bindings) is not tuple
        or not source_bindings
        or any(type(item) is not AnalyticalSourceBinding for item in source_bindings)
        or type(policy) is not FreshnessPolicy
        or type(evaluation_timestamp) is not str
        or type(requirement) is not EvidenceRequirement
    ):
        return _invalid(evidence_key)

    selected_ids = {item.source_binding_id for item in selected_candidates}
    by_id: dict[str, AnalyticalSourceBinding] = {}
    for source in source_bindings:
        existing = by_id.get(source.source_binding_id)
        if existing is not None and existing != source:
            return _invalid(evidence_key, tuple(item.provenance_ref for item in source_bindings))
        by_id[source.source_binding_id] = source
    if selected_ids != set(by_id):
        return _invalid(evidence_key, tuple(item.provenance_ref for item in source_bindings))

    sources = tuple(by_id[source_id] for source_id in sorted(selected_ids))
    for candidate in selected_candidates:
        source = by_id[candidate.source_binding_id]
        if (
            candidate.provenance_ref != source.provenance_ref
            or candidate.instrument_binding_id != source.instrument.binding_id
            or candidate.timeframe != source.timeframe
        ):
            return _invalid(evidence_key, (source.provenance_ref,))

    try:
        evaluation = instant(timestamp(evaluation_timestamp, "evaluation_timestamp"))
        selected_times = tuple(
            (
                source,
                instant(
                    timestamp(
                        (
                            source.observation_timestamp
                            if policy.basis is FreshnessBasis.OBSERVATION
                            else source.availability_timestamp
                        ),
                        "selected_basis_timestamp",
                    )
                ),
            )
            for source in sources
        )
    except (AttributeError, TypeError, ValueError):
        return _invalid(evidence_key, tuple(source.provenance_ref for source in sources))

    future = tuple(source for source, timestamp in selected_times if timestamp > evaluation)
    if future:
        return _invalid(evidence_key, tuple(source.provenance_ref for source in future))

    stale = tuple(
        source
        for source, timestamp in selected_times
        if int((evaluation - timestamp).total_seconds()) > policy.max_age_seconds
    )
    evaluated_ids = tuple(source.source_binding_id for source in sources)
    stale_ids = tuple(source.source_binding_id for source in stale)
    if not stale:
        return _EvidenceFreshnessResolution(True, False, None, (), evaluated_ids, ())

    source_refs = tuple(source.provenance_ref for source in stale)
    optional = requirement is EvidenceRequirement.OPTIONAL
    diagnostic = _diagnostic(
        evidence_key,
        source_refs,
        severity=DiagnosticSeverity.WARNING if optional else DiagnosticSeverity.ERROR,
    )
    return _EvidenceFreshnessResolution(
        False,
        optional,
        None if optional else FactAdapterState.REJECTED,
        (diagnostic,),
        evaluated_ids,
        stale_ids,
    )


__all__: tuple[str, ...] = ()
