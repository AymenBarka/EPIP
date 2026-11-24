"""Frozen-contract integration (read-only use of ``epip``).

Builds the frozen ``WaveSnapshot``, ``ElliottAnalysis`` and
``FibonacciSnapshot`` through their public constructors and runs the five
frozen P04-F01 rules in-process, in their governed order and with their
barriers. Nothing here subclasses, patches or mutates production code.

Numeric fields of the frozen types that would require a calibrated estimate
(``WaveCount.confidence``, ``WaveCount.probability``, confluence,
``FibonacciSnapshot.probability``) are set to ``0.0``. In this research
package ``0.0`` there means "not estimated"; the uncalibrated research score
never enters a frozen probability field.

Outcome classes (E00 prompt section 6):

- A: the research candidate is causally identified (every published primary);
- B: the frozen snapshots can represent it (constructors and bindings accept);
- C: the frozen F01 chain accepts it (all five rules succeed);
- D: it is not accepted because of a documented frozen-contract restriction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from epip.core.integrity import DataIntegrityError
from epip.elliott import (
    AlternateCount,
    CountStatus,
    ElliottAnalysis,
    Wave,
    WaveCount,
    WaveDegree,
    WaveLabel,
    WavePattern,
    WaveProjection,
    WaveQuality,
    WaveSequence,
    WaveSnapshot,
)
from epip.fibonacci import (
    FibonacciDirection,
    FibonacciExtension,
    FibonacciLevel,
    FibonacciRetracement,
    FibonacciSnapshot,
)
from epip.strategy_mapping import (
    AnalyticalSourceBinding,
    AnalyticalSourceKind,
    CandidateRuleResult,
    CandidateSelectionRequest,
    InstrumentBinding,
    RevisionIdentity,
    SelectionRuleResult,
    SemanticCandidate,
    SemanticRuleInvocationContext,
    SemanticRuleState,
    SourceExtractionRequest,
    StructuralApplicabilitySetRequest,
)
from epip.strategy_profiles.elliott_fibonacci import RULE_IDENTITIES, RULE_SET, SEMANTIC_PROFILE
from epip.strategy_runtime.mtf import TimeframeRole
from research.elliott_causal.contracts import CountCandidate, CountSearch, Direction

RETRACEMENT_RATIOS = (0.236, 0.382, 0.5, 0.618, 0.705, 0.786)
EXTENSION_RATIOS = (1.0, 1.272, 1.618)
SOURCE_CONTRACT_VERSION = "e00-research/1"

# Research scale -> frozen degree label (amplitude-derived research label, not
# a calibrated Elliott degree; G00 section 11 item 5).
_DEGREES = (
    WaveDegree.SUBMINUETTE,
    WaveDegree.MINUETTE,
    WaveDegree.MINUTE,
    WaveDegree.MINOR,
    WaveDegree.INTERMEDIATE,
    WaveDegree.PRIMARY,
)


class SnapshotMode(StrEnum):
    """FAITHFUL carries the ranked alternates; PRIMARY_ONLY omits them.

    PRIMARY_ONLY exists only to measure the frozen F01 empty-alternates
    restriction (G00 section 6). It is always reported separately and never
    replaces the FAITHFUL result.
    """

    FAITHFUL = "FAITHFUL"
    PRIMARY_ONLY = "PRIMARY_ONLY"


class OutcomeClass(StrEnum):
    C_ACCEPTED = "C_ACCEPTED"
    D_FROZEN_RESTRICTION = "D_FROZEN_RESTRICTION"
    B_NOT_REPRESENTABLE = "B_NOT_REPRESENTABLE"


@dataclass(frozen=True, slots=True)
class RuleStep:
    rule: str
    state: str
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Qualification:
    mode: SnapshotMode
    outcome: OutcomeClass
    steps: tuple[RuleStep, ...]
    restriction: str | None
    wave_snapshot_id: str | None
    fibonacci_snapshot_id: str | None


def degree_for(scale: int) -> WaveDegree:
    return _DEGREES[min(max(scale, 0), len(_DEGREES) - 1)]


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wave_count(candidate: CountCandidate, status: CountStatus) -> WaveCount:
    a, b, c = candidate.w1_start, candidate.w1_end, candidate.w2_end
    up = candidate.direction is Direction.UP
    degree = degree_for(candidate.w1_scale)
    w1 = Wave(
        WaveLabel.WAVE_1,
        degree,
        a.extreme_index,
        b.extreme_index,
        iso(a.extreme_start_ms),
        iso(b.extreme_start_ms),
        a.price,
        b.price,
        "UP" if up else "DOWN",
    )
    w2 = Wave(
        WaveLabel.WAVE_2,
        degree,
        b.extreme_index,
        c.extreme_index,
        iso(b.extreme_start_ms),
        iso(c.extreme_start_ms),
        b.price,
        c.price,
        "DOWN" if up else "UP",
    )
    sequence = WaveSequence((w1, w2), WavePattern.UNKNOWN, degree)
    return WaveCount(candidate.count_id, sequence, (), 0.0, 0.0, WaveQuality.LOW, 0.0, status)


def wave_snapshot(
    search: CountSearch, symbol: str, timeframe: str, mode: SnapshotMode
) -> WaveSnapshot:
    primary = search.primary
    assert primary is not None
    alternates = (
        tuple(
            AlternateCount(_wave_count(item, CountStatus.ALTERNATE), "e00 ranked alternate")
            for item in search.alternates
        )
        if mode is SnapshotMode.FAITHFUL
        else ()
    )
    projection = WaveProjection(WaveLabel.WAVE_3, primary.retracement, (), 0.0)
    analysis = ElliottAnalysis(_wave_count(primary, CountStatus.VALID), alternates, projection)
    return WaveSnapshot(iso(search.available_ms), symbol, timeframe, 1, 1, analysis)


def fibonacci_snapshot(
    candidate: CountCandidate, available_ms: int, symbol: str, timeframe: str
) -> FibonacciSnapshot:
    """Fibonacci anchored on W1 exactly; direction follows W1."""
    a, b, c = candidate.w1_start.price, candidate.w1_end.price, candidate.w2_end.price
    direction = (
        FibonacciDirection.BULLISH
        if candidate.direction is Direction.UP
        else FibonacciDirection.BEARISH
    )
    span = b - a
    retracement = FibonacciRetracement(
        a,
        b,
        direction,
        tuple(FibonacciLevel(r, b - r * span, f"{r:g}") for r in RETRACEMENT_RATIOS),
    )
    extension = FibonacciExtension(
        a, b, tuple(FibonacciLevel(r, c + r * span, f"{r:g}") for r in EXTENSION_RATIOS)
    )
    return FibonacciSnapshot(
        iso(available_ms), symbol, timeframe, 1, direction, retracement, extension, ()
    )


def _binding(
    kind: AnalyticalSourceKind,
    payload: WaveSnapshot | FibonacciSnapshot,
    provenance: str,
    instrument: InstrumentBinding,
    timeframe: str,
    at: str,
) -> AnalyticalSourceBinding:
    return AnalyticalSourceBinding.create(
        source_kind=kind,
        source_contract_version=SOURCE_CONTRACT_VERSION,
        source_object_id=provenance,
        instrument=instrument,
        timeframe=timeframe,
        observation_timestamp=at,
        availability_timestamp=at,
        as_of_timestamp=at,
        revision=RevisionIdentity(provenance, f"{provenance}-r0", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref=provenance,
        payload=payload,
    )


def _context(
    suffix: str, sources: tuple[AnalyticalSourceBinding, ...], at: str, timeframe: str
) -> SemanticRuleInvocationContext:
    return SemanticRuleInvocationContext(
        "e00-research",
        at,
        SEMANTIC_PROFILE.identity,
        RULE_IDENTITIES[suffix],
        sources[0].instrument.binding_id,
        timeframe,
        TimeframeRole.PRIMARY,
        tuple(item.source_binding_id for item in sources),
        tuple(item.provenance_ref for item in sources),
    )


def _step(suffix: str, state: SemanticRuleState, codes: tuple[object, ...]) -> RuleStep:
    return RuleStep(suffix, state.value, tuple(sorted(str(getattr(c, "value", c)) for c in codes)))


_RESTRICTIONS = {
    "applicability.elliott-wave3": "F01 Elliott applicability predicates (alternates must be empty)",
    "applicability.fibonacci-wave3": "F01 cross-domain anchor/orientation equality",
    "extract.elliott": "F01 Elliott extraction",
    "extract.fibonacci": "F01 Fibonacci extraction",
    "select.wave1-anchor": "F01 W1 anchor selection",
}


def qualify(search: CountSearch, symbol: str, timeframe: str, mode: SnapshotMode) -> Qualification:
    """Run the frozen F01 chain on the primary count of ``search``."""
    primary = search.primary
    assert primary is not None
    at = iso(search.available_ms)
    try:
        instrument = InstrumentBinding.create(symbol.lower(), symbol, (), "1")
        ws = wave_snapshot(search, symbol, timeframe, mode)
        fs = fibonacci_snapshot(primary, search.available_ms, symbol, timeframe)
        tag = f"e00:{primary.count_id}:{mode.value}"
        es = _binding(AnalyticalSourceKind.ELLIOTT, ws, f"{tag}:elliott", instrument, timeframe, at)
        fb = _binding(
            AnalyticalSourceKind.FIBONACCI, fs, f"{tag}:fibonacci", instrument, timeframe, at
        )
    except DataIntegrityError as exc:  # frozen constructors fail closed
        return Qualification(
            mode, OutcomeClass.B_NOT_REPRESENTABLE, (), f"{type(exc).__name__}: {exc}", None, None
        )
    steps: list[RuleStep] = []

    def done(failed: str | None) -> Qualification:
        return Qualification(
            mode,
            OutcomeClass.C_ACCEPTED if failed is None else OutcomeClass.D_FROZEN_RESTRICTION,
            tuple(steps),
            None if failed is None else _RESTRICTIONS[failed],
            es.source_binding_id,
            fb.source_binding_id,
        )

    def invoke_extract(
        suffix: str, source: AnalyticalSourceBinding
    ) -> tuple[SemanticCandidate, ...] | None:
        result = RULE_SET.invoke(
            RULE_IDENTITIES[suffix],
            SourceExtractionRequest(_context(suffix, (source,), at, timeframe), source),
        )
        steps.append(_step(suffix, result.state, tuple(result.diagnostic_codes)))
        if result.state is not SemanticRuleState.SUCCESS:
            return None
        assert isinstance(result, CandidateRuleResult)
        return result.candidates

    ec = invoke_extract("extract.elliott", es)
    if ec is None:
        return done("extract.elliott")
    suffix = "applicability.elliott-wave3"
    result = RULE_SET.invoke(
        RULE_IDENTITIES[suffix],
        StructuralApplicabilitySetRequest(_context(suffix, (es,), at, timeframe), ec, (es,)),
    )
    steps.append(_step(suffix, result.state, tuple(result.diagnostic_codes)))
    if result.state is not SemanticRuleState.SUCCESS:
        return done(suffix)
    fc = invoke_extract("extract.fibonacci", fb)
    if fc is None:
        return done("extract.fibonacci")
    suffix = "applicability.fibonacci-wave3"
    candidates = (*ec, *fc)
    result = RULE_SET.invoke(
        RULE_IDENTITIES[suffix],
        StructuralApplicabilitySetRequest(
            _context(suffix, (es, fb), at, timeframe), candidates, (es, fb)
        ),
    )
    steps.append(_step(suffix, result.state, tuple(result.diagnostic_codes)))
    if result.state is not SemanticRuleState.SUCCESS:
        return done(suffix)
    suffix = "select.wave1-anchor"
    selected = RULE_SET.invoke(
        RULE_IDENTITIES[suffix],
        CandidateSelectionRequest(_context(suffix, (es, fb), at, timeframe), candidates, None),
    )
    steps.append(_step(suffix, selected.state, tuple(selected.diagnostic_codes)))
    assert isinstance(selected, SelectionRuleResult)
    if selected.state is not SemanticRuleState.SUCCESS or set(
        selected.selected_candidate_ids or ()
    ) != {item.candidate_id for item in ec}:
        return done(suffix)
    return done(None)
