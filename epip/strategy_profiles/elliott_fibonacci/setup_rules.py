"""Executable P04-F01 Elliott/Fibonacci Wave-3 setup rules."""

from __future__ import annotations

from math import isfinite
from typing import NamedTuple

from epip.elliott import CountStatus, WaveLabel, WavePattern, WaveSnapshot
from epip.fibonacci import FibonacciDirection, FibonacciSnapshot
from epip.strategy_mapping import (
    AnalyticalSourceBinding,
    AnalyticalSourceKind,
    ApplicabilityResult,
    CandidateRuleResult,
    CandidateSelectionRequest,
    RuleIdentity,
    SelectionRuleResult,
    SemanticCandidate,
    SemanticCandidateRole,
    SemanticInvocationKind,
    SemanticResultKind,
    SemanticRuleDiagnosticCode,
    SemanticRuleFamily,
    SemanticRuleRequest,
    SemanticRuleResult,
    SemanticRuleState,
    SemanticValue,
    SemanticValueKind,
    SourceExtractionRequest,
    StructuralApplicabilitySetRequest,
)
from epip.strategy_runtime.mtf import TimeframeRole

_INVALID = (SemanticRuleDiagnosticCode.RULE_INPUT_INVALID,)
_REJECTED = (SemanticRuleDiagnosticCode.RULE_REJECTED,)


def _candidate_failure(state: SemanticRuleState) -> CandidateRuleResult:
    return CandidateRuleResult(
        state, _INVALID if state is SemanticRuleState.INVALID_INPUT else _REJECTED, None
    )


def _applicability_failure(state: SemanticRuleState) -> ApplicabilityResult:
    return ApplicabilityResult(
        state, _INVALID if state is SemanticRuleState.INVALID_INPUT else _REJECTED, None
    )


def _context_is_primary(
    request: (
        SourceExtractionRequest | StructuralApplicabilitySetRequest | CandidateSelectionRequest
    ),
    identity: RuleIdentity,
) -> bool:
    context = request.context
    return (
        context.rule_identity == identity
        and context.timeframe is not None
        and context.timeframe_role is TimeframeRole.PRIMARY
    )


def _price_is_valid(value: object) -> bool:
    return type(value) is float and isfinite(value) and value > 0.0


def _candidate_matches_source(
    candidate: SemanticCandidate, source: AnalyticalSourceBinding
) -> bool:
    return (
        candidate.source_binding_id == source.source_binding_id
        and candidate.provenance_ref == source.provenance_ref
        and candidate.instrument_binding_id == source.instrument.binding_id
        and candidate.timeframe == source.timeframe
        and candidate.value.kind is SemanticValueKind.PRICE
        and _price_is_valid(candidate.value.float_value)
    )


def _anchors(
    candidates: tuple[SemanticCandidate, ...], identity: RuleIdentity
) -> dict[SemanticCandidateRole, SemanticCandidate] | None:
    selected = [item for item in candidates if item.source_rule_identity == identity]
    if len(selected) != 2:
        return None
    by_role = {item.role: item for item in selected}
    if len(by_role) != 2 or set(by_role) != {
        SemanticCandidateRole.ANCHOR_START,
        SemanticCandidateRole.ANCHOR_END,
    }:
        return None
    return by_role


class ElliottExtractionRule(NamedTuple):
    identity: RuleIdentity
    family: SemanticRuleFamily = SemanticRuleFamily.SOURCE_EXTRACTION
    invocation_kind: SemanticInvocationKind = SemanticInvocationKind.SOURCE_EXTRACTION
    result_kind: SemanticResultKind = SemanticResultKind.CANDIDATES
    implementation_id: str = "p04-f01-extract-elliott-v1"

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if type(request) is not SourceExtractionRequest or not _context_is_primary(
            request, self.identity
        ):
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        source = request.source
        if (
            source.source_kind is not AnalyticalSourceKind.ELLIOTT
            or type(source.payload) is not WaveSnapshot
        ):
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        waves = source.payload.analysis.primary.sequence.waves
        if not waves:
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        wave = waves[0]
        if wave.label is not WaveLabel.WAVE_1:
            return _candidate_failure(SemanticRuleState.REJECTED)
        if not (_price_is_valid(wave.start_price) and _price_is_valid(wave.end_price)):
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        candidates = tuple(
            SemanticCandidate.create(
                source_binding_id=source.source_binding_id,
                provenance_ref=source.provenance_ref,
                instrument_binding_id=source.instrument.binding_id,
                timeframe=source.timeframe,
                source_rule_identity=self.identity,
                value=SemanticValue(SemanticValueKind.PRICE, float_value=value),
                role=role,
            )
            for value, role in (
                (wave.start_price, SemanticCandidateRole.ANCHOR_START),
                (wave.end_price, SemanticCandidateRole.ANCHOR_END),
            )
        )
        return CandidateRuleResult(SemanticRuleState.SUCCESS, (), candidates)


class FibonacciExtractionRule(NamedTuple):
    identity: RuleIdentity
    family: SemanticRuleFamily = SemanticRuleFamily.SOURCE_EXTRACTION
    invocation_kind: SemanticInvocationKind = SemanticInvocationKind.SOURCE_EXTRACTION
    result_kind: SemanticResultKind = SemanticResultKind.CANDIDATES
    implementation_id: str = "p04-f01-extract-fibonacci-v1"

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if type(request) is not SourceExtractionRequest or not _context_is_primary(
            request, self.identity
        ):
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        source = request.source
        if (
            source.source_kind is not AnalyticalSourceKind.FIBONACCI
            or type(source.payload) is not FibonacciSnapshot
        ):
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        retracement = source.payload.retracement
        if not (
            _price_is_valid(retracement.start_price) and _price_is_valid(retracement.end_price)
        ):
            return _candidate_failure(SemanticRuleState.INVALID_INPUT)
        candidates = tuple(
            SemanticCandidate.create(
                source_binding_id=source.source_binding_id,
                provenance_ref=source.provenance_ref,
                instrument_binding_id=source.instrument.binding_id,
                timeframe=source.timeframe,
                source_rule_identity=self.identity,
                value=SemanticValue(SemanticValueKind.PRICE, float_value=value),
                role=role,
            )
            for value, role in (
                (retracement.start_price, SemanticCandidateRole.ANCHOR_START),
                (retracement.end_price, SemanticCandidateRole.ANCHOR_END),
            )
        )
        return CandidateRuleResult(SemanticRuleState.SUCCESS, (), candidates)


class ElliottWave3ApplicabilityRule(NamedTuple):
    identity: RuleIdentity
    extraction_identity: RuleIdentity
    family: SemanticRuleFamily = SemanticRuleFamily.APPLICABILITY
    invocation_kind: SemanticInvocationKind = SemanticInvocationKind.STRUCTURAL_APPLICABILITY
    result_kind: SemanticResultKind = SemanticResultKind.APPLICABILITY
    implementation_id: str = "p04-f01-applicability-elliott-wave3-v1"

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if type(request) is not StructuralApplicabilitySetRequest or not _context_is_primary(
            request, self.identity
        ):
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        if len(request.candidates) != 2 or len(request.sources) != 1:
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        source = request.sources[0]
        anchors = _anchors(request.candidates, self.extraction_identity)
        if (
            source.source_kind is not AnalyticalSourceKind.ELLIOTT
            or type(source.payload) is not WaveSnapshot
            or anchors is None
        ):
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        if any(not _candidate_matches_source(item, source) for item in anchors.values()):
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        analysis = source.payload.analysis
        primary = analysis.primary
        sequence = primary.sequence
        waves = sequence.waves
        if len(waves) != 2:
            return _applicability_failure(SemanticRuleState.REJECTED)
        w1, w2 = waves
        candidate_start = anchors[SemanticCandidateRole.ANCHOR_START].value.float_value
        candidate_end = anchors[SemanticCandidateRole.ANCHOR_END].value.float_value
        if candidate_start != w1.start_price or candidate_end != w1.end_price:
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        eligible = (
            sequence.pattern is WavePattern.UNKNOWN
            and w1.label is WaveLabel.WAVE_1
            and w2.label is WaveLabel.WAVE_2
            and primary.status is CountStatus.VALID
            and not primary.violations
            and not analysis.alternates
            and sequence.degree is w1.degree is w2.degree
            and w1.direction in ("UP", "DOWN")
            and w2.direction == ("DOWN" if w1.direction == "UP" else "UP")
            and w2.start_index == w1.end_index
            and w2.start_timestamp == w1.end_timestamp
            and w2.start_price == w1.end_price
            and (
                (w1.direction == "UP" and w2.end_price > w1.start_price)
                or (w1.direction == "DOWN" and w2.end_price < w1.start_price)
            )
            and analysis.projection is not None
            and analysis.projection.next_wave is WaveLabel.WAVE_3
        )
        return (
            ApplicabilityResult(SemanticRuleState.SUCCESS, (), True)
            if eligible
            else _applicability_failure(SemanticRuleState.REJECTED)
        )


class FibonacciWave3ApplicabilityRule(NamedTuple):
    identity: RuleIdentity
    elliott_extraction_identity: RuleIdentity
    fibonacci_extraction_identity: RuleIdentity
    family: SemanticRuleFamily = SemanticRuleFamily.APPLICABILITY
    invocation_kind: SemanticInvocationKind = SemanticInvocationKind.STRUCTURAL_APPLICABILITY
    result_kind: SemanticResultKind = SemanticResultKind.APPLICABILITY
    implementation_id: str = "p04-f01-applicability-fibonacci-wave3-v1"

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if type(request) is not StructuralApplicabilitySetRequest or not _context_is_primary(
            request, self.identity
        ):
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        if len(request.candidates) != 4 or len(request.sources) != 2:
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        elliott_sources = [
            item for item in request.sources if item.source_kind is AnalyticalSourceKind.ELLIOTT
        ]
        fibonacci_sources = [
            item for item in request.sources if item.source_kind is AnalyticalSourceKind.FIBONACCI
        ]
        ea = _anchors(request.candidates, self.elliott_extraction_identity)
        fa = _anchors(request.candidates, self.fibonacci_extraction_identity)
        if len(elliott_sources) != 1 or len(fibonacci_sources) != 1 or ea is None or fa is None:
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        es, fs = elliott_sources[0], fibonacci_sources[0]
        if type(es.payload) is not WaveSnapshot or type(fs.payload) is not FibonacciSnapshot:
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        if any(not _candidate_matches_source(item, es) for item in ea.values()) or any(
            not _candidate_matches_source(item, fs) for item in fa.values()
        ):
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        waves = es.payload.analysis.primary.sequence.waves
        if not waves:
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        w1 = waves[0]
        retracement = fs.payload.retracement
        esv, eev = (
            ea[SemanticCandidateRole.ANCHOR_START].value.float_value,
            ea[SemanticCandidateRole.ANCHOR_END].value.float_value,
        )
        fsv, fev = (
            fa[SemanticCandidateRole.ANCHOR_START].value.float_value,
            fa[SemanticCandidateRole.ANCHOR_END].value.float_value,
        )
        if (
            esv != w1.start_price
            or eev != w1.end_price
            or fsv != retracement.start_price
            or fev != retracement.end_price
        ):
            return _applicability_failure(SemanticRuleState.INVALID_INPUT)
        expected = (
            FibonacciDirection.BULLISH
            if w1.direction == "UP"
            else FibonacciDirection.BEARISH if w1.direction == "DOWN" else None
        )
        eligible = (
            fsv == esv
            and fev == eev
            and fsv != fev
            and ((w1.direction == "UP" and esv < eev) or (w1.direction == "DOWN" and esv > eev))
            and expected is not None
            and fs.payload.direction is expected
            and retracement.direction is expected
        )
        return (
            ApplicabilityResult(SemanticRuleState.SUCCESS, (), True)
            if eligible
            else _applicability_failure(SemanticRuleState.REJECTED)
        )


class Wave1AnchorSelectionRule(NamedTuple):
    identity: RuleIdentity
    elliott_extraction_identity: RuleIdentity
    fibonacci_extraction_identity: RuleIdentity
    family: SemanticRuleFamily = SemanticRuleFamily.CANDIDATE_SELECTION
    invocation_kind: SemanticInvocationKind = SemanticInvocationKind.SELECTION
    result_kind: SemanticResultKind = SemanticResultKind.SELECTION
    implementation_id: str = "p04-f01-select-wave1-anchor-v1"

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        if type(request) is not CandidateSelectionRequest or not _context_is_primary(
            request, self.identity
        ):
            return SelectionRuleResult(SemanticRuleState.INVALID_INPUT, _INVALID, None)
        if request.direction is not None or len(request.candidates) != 4:
            return SelectionRuleResult(SemanticRuleState.REJECTED, _REJECTED, None)
        ea = _anchors(request.candidates, self.elliott_extraction_identity)
        fa = _anchors(request.candidates, self.fibonacci_extraction_identity)
        if ea is None or fa is None:
            diagnostics: tuple[SemanticRuleDiagnosticCode, ...] = _REJECTED
            known = {self.elliott_extraction_identity, self.fibonacci_extraction_identity}
            if any(
                sum(
                    item.source_rule_identity == identity and item.role is role
                    for item in request.candidates
                )
                > 1
                for identity in known
                for role in (SemanticCandidateRole.ANCHOR_START, SemanticCandidateRole.ANCHOR_END)
            ):
                diagnostics = tuple(
                    sorted(
                        (*_REJECTED, SemanticRuleDiagnosticCode.AMBIGUOUS_CANDIDATE),
                        key=lambda item: item.value,
                    )
                )
            return SelectionRuleResult(SemanticRuleState.REJECTED, diagnostics, None)
        if (
            ea[SemanticCandidateRole.ANCHOR_START].value
            != fa[SemanticCandidateRole.ANCHOR_START].value
            or ea[SemanticCandidateRole.ANCHOR_END].value
            != fa[SemanticCandidateRole.ANCHOR_END].value
        ):
            return SelectionRuleResult(SemanticRuleState.REJECTED, _REJECTED, None)
        selected = tuple(item.candidate_id for item in ea.values())
        return SelectionRuleResult(SemanticRuleState.SUCCESS, (), selected)


__all__ = [
    "ElliottExtractionRule",
    "ElliottWave3ApplicabilityRule",
    "FibonacciExtractionRule",
    "FibonacciWave3ApplicabilityRule",
    "Wave1AnchorSelectionRule",
]
