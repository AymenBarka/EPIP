"""Private mechanical confidence-input cardinality reduction."""

from __future__ import annotations

from typing import NamedTuple

from epip.strategy_mapping.confidence_policy import (
    ConfidenceInput,
    ConfidenceModelKind,
    ConfidencePolicy,
)
from epip.strategy_mapping.direction_policy import NonAcceptanceAction
from epip.strategy_mapping.rule_execution import SemanticRuleState
from epip.strategy_mapping.rule_results import CandidateRuleResult
from epip.strategy_mapping.rule_values import ConfidenceInputValue
from epip.strategy_runtime.protocols import FactAdapterState
from epip.strategy_runtime.result import (
    DiagnosticSeverity,
    RuntimeDiagnostic,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
)


class _ConfidenceInputResolution(NamedTuple):
    value: ConfidenceInputValue | None
    omitted: bool
    terminal_state: FactAdapterState | None
    diagnostics: tuple[RuntimeDiagnostic, ...]
    source_state: SemanticRuleState | None


class _ConfidencePolicyResolution(NamedTuple):
    included: tuple[ConfidenceInputValue, ...]
    omitted_input_keys: tuple[str, ...]
    terminal_state: FactAdapterState | None
    diagnostics: tuple[RuntimeDiagnostic, ...]
    processed_count: int


def _diagnostic(
    code: RuntimeDiagnosticCode,
    subject_ref: str,
    message: str,
    *,
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
    source_refs: tuple[str, ...] = (),
) -> RuntimeDiagnostic:
    return RuntimeDiagnostic(
        code,
        RuntimeDiagnosticStage.ADAPTER,
        severity,
        subject_ref,
        source_refs,
        message,
    )


def _terminal_rule_result(
    item: ConfidenceInput, result: CandidateRuleResult
) -> _ConfidenceInputResolution:
    mapping = {
        SemanticRuleState.REJECTED: (
            FactAdapterState.REJECTED,
            RuntimeDiagnosticCode.ADAPTER_REJECTED,
        ),
        SemanticRuleState.INVALID_INPUT: (
            FactAdapterState.INVALID_INPUT,
            RuntimeDiagnosticCode.INVALID_REQUEST,
        ),
        SemanticRuleState.FAILED: (
            FactAdapterState.FAILED,
            RuntimeDiagnosticCode.ADAPTER_FAILED,
        ),
    }
    state, code = mapping[result.state]
    messages = tuple(x.value for x in result.diagnostic_codes) or (result.state.value,)
    diagnostics = tuple(_diagnostic(code, item.input_key, message) for message in messages)
    return _ConfidenceInputResolution(None, False, state, diagnostics, result.state)


def _activated_action(
    item: ConfidenceInput,
    action: NonAcceptanceAction,
    *,
    missing: bool,
    source_state: SemanticRuleState,
    source_refs: tuple[str, ...],
) -> _ConfidenceInputResolution:
    if action is NonAcceptanceAction.REQUIRE_EXPLICIT_SELECTION_RULE:
        return _ConfidenceInputResolution(
            None,
            False,
            FactAdapterState.INVALID_INPUT,
            (
                _diagnostic(
                    RuntimeDiagnosticCode.INVALID_REQUEST,
                    item.input_key,
                    "CONFIDENCE_SELECTION_RULE_UNAVAILABLE",
                    source_refs=source_refs,
                ),
            ),
            source_state,
        )
    if action is NonAcceptanceAction.NO_FACT and not item.required:
        message = "CONFIDENCE_INPUT_OMITTED" if missing else "CONFIDENCE_INPUT_CONFLICT_OMITTED"
        code = (
            RuntimeDiagnosticCode.MISSING_FACT
            if missing
            else RuntimeDiagnosticCode.ADAPTER_REJECTED
        )
        return _ConfidenceInputResolution(
            None,
            True,
            None,
            (
                _diagnostic(
                    code,
                    item.input_key,
                    message,
                    severity=DiagnosticSeverity.WARNING,
                    source_refs=source_refs,
                ),
            ),
            source_state,
        )
    message = "CONFIDENCE_INPUT_MISSING" if missing else "CONFIDENCE_INPUT_CONFLICT"
    code = RuntimeDiagnosticCode.MISSING_FACT if missing else RuntimeDiagnosticCode.ADAPTER_REJECTED
    return _ConfidenceInputResolution(
        None,
        False,
        FactAdapterState.REJECTED,
        (_diagnostic(code, item.input_key, message, source_refs=source_refs),),
        source_state,
    )


def _reduce_confidence_input(
    item: ConfidenceInput, policy: ConfidencePolicy, result: object
) -> _ConfidenceInputResolution:
    """Reduce one already-extracted result without rule dispatch or candidate selection."""
    if type(item) is not ConfidenceInput or type(policy) is not ConfidencePolicy:
        return _ConfidenceInputResolution(
            None,
            False,
            FactAdapterState.INVALID_INPUT,
            (
                _diagnostic(
                    RuntimeDiagnosticCode.INVALID_REQUEST,
                    (
                        policy.policy_identity.reference
                        if type(policy) is ConfidencePolicy
                        else "confidence-policy"
                    ),
                    "RULE_OUTPUT_INVALID",
                ),
            ),
            None,
        )
    if type(result) is not CandidateRuleResult:
        return _ConfidenceInputResolution(
            None,
            False,
            FactAdapterState.INVALID_INPUT,
            (
                _diagnostic(
                    RuntimeDiagnosticCode.INVALID_REQUEST,
                    item.input_key,
                    "RULE_OUTPUT_INVALID",
                ),
            ),
            None,
        )
    if result.state is SemanticRuleState.NO_MATCH:
        return _activated_action(
            item,
            policy.missing_action,
            missing=True,
            source_state=result.state,
            source_refs=(),
        )
    if result.state is not SemanticRuleState.SUCCESS:
        return _terminal_rule_result(item, result)
    assert result.candidates is not None
    if len(result.candidates) == 1:
        return _ConfidenceInputResolution(
            ConfidenceInputValue(item.input_key, result.candidates[0], item.required),
            False,
            None,
            (),
            result.state,
        )
    source_refs = tuple(candidate.provenance_ref for candidate in result.candidates)
    return _activated_action(
        item,
        policy.missing_action if not result.candidates else policy.conflict_action,
        missing=not result.candidates,
        source_state=result.state,
        source_refs=source_refs,
    )


def _reduce_confidence_policy(
    policy: ConfidencePolicy,
    extracted: tuple[tuple[ConfidenceInput, object], ...],
) -> _ConfidencePolicyResolution:
    """Collect included inputs in policy order and stop at the first terminal outcome."""
    if type(policy) is not ConfidencePolicy or type(extracted) is not tuple:
        return _invalid_policy_resolution(policy)
    if (
        len(extracted) != len(policy.inputs)
        or any(type(pair) is not tuple or len(pair) != 2 for pair in extracted)
        or tuple(pair[0] for pair in extracted) != policy.inputs
    ):
        return _invalid_policy_resolution(policy)
    included: list[ConfidenceInputValue] = []
    omitted: list[str] = []
    diagnostics: list[RuntimeDiagnostic] = []
    for processed, (item, result) in enumerate(extracted, 1):
        resolution = _reduce_confidence_input(item, policy, result)
        diagnostics.extend(resolution.diagnostics)
        if resolution.terminal_state is not None:
            return _ConfidencePolicyResolution(
                tuple(included),
                tuple(omitted),
                resolution.terminal_state,
                tuple(diagnostics),
                processed,
            )
        if resolution.omitted:
            omitted.append(item.input_key)
        else:
            assert resolution.value is not None
            included.append(resolution.value)
    valid_count = (
        len(included) == 1 if policy.model_kind is ConfidenceModelKind.DIRECT else bool(included)
    )
    if not valid_count:
        diagnostics.append(
            _diagnostic(
                RuntimeDiagnosticCode.MISSING_FACT,
                policy.policy_identity.reference,
                "CONFIDENCE_INPUT_SET_EMPTY",
            )
        )
        return _ConfidencePolicyResolution(
            tuple(included),
            tuple(omitted),
            FactAdapterState.REJECTED,
            tuple(diagnostics),
            len(extracted),
        )
    return _ConfidencePolicyResolution(
        tuple(included), tuple(omitted), None, tuple(diagnostics), len(extracted)
    )


def _invalid_policy_resolution(policy: object) -> _ConfidencePolicyResolution:
    subject = (
        policy.policy_identity.reference
        if type(policy) is ConfidencePolicy
        else "confidence-policy"
    )
    return _ConfidencePolicyResolution(
        (),
        (),
        FactAdapterState.INVALID_INPUT,
        (_diagnostic(RuntimeDiagnosticCode.INVALID_REQUEST, subject, "RULE_OUTPUT_INVALID"),),
        0,
    )


__all__: tuple[str, ...] = ()
