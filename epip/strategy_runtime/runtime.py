"""P03 canonical single-evaluation Strategy Runtime orchestration."""

from __future__ import annotations

from typing import Protocol

from epip.a07.confidence import ConfidenceValidation, SignalExpiration, StrategyConfidence
from epip.a07.direction import DirectionalDecision, DirectionValidation
from epip.a07.entry import EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation
from epip.a07.foundation import StrategyDirection, StrategyEvaluationRequest
from epip.a07.policy import PolicyValidation, StrategyPolicy
from epip.a07.reward_risk import RewardRiskOutcome, RewardRiskValidation
from epip.a07.signal import SignalValidation, StrategySignal
from epip.a07.stop import StopLoss, StopValidation
from epip.a07.target import TakeProfit, TargetValidation
from epip.strategy_runtime._base import CONTRACT_VERSION, digest
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.facts import AnalyticalInputBundle, StrategyFactBundle
from epip.strategy_runtime.profile import (
    StrategyProfile,
    StrategyProfileIdentity,
    StrategyProfileRegistryProtocol,
)
from epip.strategy_runtime.protocols import (
    FactAdapterProtocol,
    FactAdapterResult,
    FactAdapterState,
)
from epip.strategy_runtime.provenance import FactAdapterIdentity
from epip.strategy_runtime.result import (
    DiagnosticSeverity,
    RuntimeDiagnostic,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
    StrategyRuntimeDiagnostics,
    StrategyRuntimeOptions,
    StrategyRuntimeRequest,
    StrategyRuntimeResult,
    StrategyRuntimeState,
)
from epip.strategy_runtime.signal_envelope import StrategySignalEnvelope

__all__ = ["StrategyRuntime", "StrategyRuntimeProtocol"]

RUNTIME_VERSION = "p03-f00-v1"


class StrategyRuntimeProtocol(Protocol):
    """Behavioral boundary for one complete logical strategy evaluation."""

    def evaluate(self, request: StrategyRuntimeRequest) -> StrategyRuntimeResult: ...


def _entry(
    code: RuntimeDiagnosticCode,
    stage: RuntimeDiagnosticStage,
    severity: DiagnosticSeverity,
    subject_ref: str,
    message: str,
) -> RuntimeDiagnostic:
    return RuntimeDiagnostic(code, stage, severity, subject_ref, (), message)


def _result(
    request_id: str,
    state: StrategyRuntimeState,
    stage: RuntimeDiagnosticStage,
    entries: tuple[RuntimeDiagnostic, ...],
    *,
    bundle: StrategyFactBundle | None = None,
    envelope: StrategySignalEnvelope | None = None,
) -> StrategyRuntimeResult:
    diagnostics = StrategyRuntimeDiagnostics.create(state, stage, entries)
    fact_bundle_id = None if bundle is None else bundle.bundle_id
    values = {
        "contract_version": CONTRACT_VERSION,
        "request_id": request_id,
        "state": state,
        "fact_bundle_id": fact_bundle_id,
        "signal_envelope": envelope,
        "diagnostics": diagnostics,
        "runtime_version": RUNTIME_VERSION,
    }
    return StrategyRuntimeResult(
        CONTRACT_VERSION,
        digest(values),
        request_id,
        state,
        fact_bundle_id,
        envelope,
        diagnostics,
        RUNTIME_VERSION,
    )


class StrategyRuntime:
    """Pure stateless orchestrator over exact injected dependencies."""

    __slots__ = ("_adapter", "_profiles")

    def __init__(
        self,
        profiles: StrategyProfileRegistryProtocol,
        adapter: FactAdapterProtocol,
    ) -> None:
        self._profiles = profiles
        self._adapter = adapter

    def evaluate(self, request: StrategyRuntimeRequest) -> StrategyRuntimeResult:
        """Evaluate one immutable request without retry, fallback, or ambient state."""
        request_id = self._request_id(request)
        profile, failure_stage = self._resolve_dependencies(request)
        if profile is None:
            return self._invalid(request_id, failure_stage)

        try:
            adapted = self._adapter.adapt(
                request.context,
                request.inputs,
                profile,
                request.policy,
            )
        except Exception:  # noqa: BLE001 - governed sanitizing adapter boundary
            return self._adapter_failure(request.request_id)

        if type(adapted) is not FactAdapterResult:
            return self._adapter_failure(request.request_id)
        terminal = {
            FactAdapterState.REJECTED: StrategyRuntimeState.REJECTED,
            FactAdapterState.INVALID_INPUT: StrategyRuntimeState.INVALID_INPUT,
            FactAdapterState.FAILED: StrategyRuntimeState.ADAPTER_FAILURE,
        }
        if adapted.state in terminal:
            return _result(
                request.request_id,
                terminal[adapted.state],
                RuntimeDiagnosticStage.ADAPTER,
                adapted.diagnostics,
            )
        if adapted.state is not FactAdapterState.ACCEPTED or adapted.bundle is None:
            return self._adapter_failure(request.request_id)
        if not self._bundle_matches(request, adapted.bundle):
            return self._invalid(
                request.request_id,
                RuntimeDiagnosticStage.COHERENCE,
                bundle=adapted.bundle,
            )
        return self._evaluate_a07(request, adapted.bundle)

    @staticmethod
    def _request_id(request: object) -> str:
        value = getattr(request, "request_id", None)
        return value if type(value) is str and value.strip() else "invalid-request"

    def _resolve_dependencies(
        self, request: StrategyRuntimeRequest
    ) -> tuple[StrategyProfile | None, RuntimeDiagnosticStage]:
        if type(request) is not StrategyRuntimeRequest:
            return None, RuntimeDiagnosticStage.REQUEST
        try:
            if (
                request.contract_version != CONTRACT_VERSION
                or request.runtime_contract_version != CONTRACT_VERSION
                or request.request_id != digest(request, exclude=frozenset({"request_id"}))
                or type(request.context) is not EvaluationContext
                or type(request.inputs) is not AnalyticalInputBundle
                or type(request.policy) is not StrategyPolicy
                or type(request.profile_identity) is not StrategyProfileIdentity
                or type(request.adapter_identity) is not FactAdapterIdentity
                or type(request.options) is not StrategyRuntimeOptions
            ):
                return None, RuntimeDiagnosticStage.REQUEST
            adapter_identity = self._adapter.identity
            if adapter_identity != request.adapter_identity:
                return None, RuntimeDiagnosticStage.ADAPTER
            profile = self._profiles.resolve(request.profile_identity)
            if type(profile) is not StrategyProfile or profile.identity != request.profile_identity:
                return None, RuntimeDiagnosticStage.PROFILE
            if profile.strategy_identity != request.policy.strategy_identity:
                return None, RuntimeDiagnosticStage.COHERENCE
            if request.runtime_contract_version not in profile.compatible_runtime_contract_versions:
                return None, RuntimeDiagnosticStage.PROFILE
            if (
                adapter_identity.contract_version
                not in profile.compatible_adapter_contract_versions
            ):
                return None, RuntimeDiagnosticStage.PROFILE
            context = request.context
            inputs = request.inputs
            if context.profile_identity != request.profile_identity:
                return None, RuntimeDiagnosticStage.COHERENCE
            if inputs.mtf_context.primary_timeframe != context.primary_timeframe:
                return None, RuntimeDiagnosticStage.TEMPORAL
            if inputs.mtf_context.alignment_timestamp != context.evaluation_timestamp:
                return None, RuntimeDiagnosticStage.TEMPORAL
            provenance = inputs.provenance
            if (
                provenance.profile_identity != request.profile_identity
                or provenance.adapter_identity != request.adapter_identity
                or provenance.evaluation_id != context.evaluation_id
            ):
                return None, RuntimeDiagnosticStage.COHERENCE
            return profile, RuntimeDiagnosticStage.ADAPTER
        except Exception:  # noqa: BLE001 - malformed or missing dependency fails closed
            return None, RuntimeDiagnosticStage.COHERENCE

    @staticmethod
    def _bundle_matches(request: StrategyRuntimeRequest, bundle: StrategyFactBundle) -> bool:
        return (
            type(bundle) is StrategyFactBundle
            and bundle.evaluation_id == request.context.evaluation_id
            and bundle.strategy_identity == request.policy.strategy_identity
            and bundle.policy_reference == request.policy.identity.reference
            and bundle.profile_identity == request.profile_identity
            and bundle.mtf_context_id == request.inputs.mtf_context.context_id
            and bundle.provenance == request.inputs.provenance
            and bundle.evidence_identity.provenance == bundle.provenance.manifest_id
        )

    def _evaluate_a07(
        self,
        request: StrategyRuntimeRequest,
        bundle: StrategyFactBundle,
    ) -> StrategyRuntimeResult:
        stage = RuntimeDiagnosticStage.A07_E00
        try:
            foundation = StrategyEvaluationRequest(
                bundle.strategy_identity,
                bundle.evidence_identity,
                request.context.evaluation_timestamp,
                request.context.source_set_id,
                bundle.policy_reference,
            )
            stage = RuntimeDiagnosticStage.A07_E01
            policy = PolicyValidation(request.policy, foundation.policy_reference)
            if not policy.valid:
                return self._a07_rejection(request, bundle, stage)
            stage = RuntimeDiagnosticStage.A07_E02
            evidence = EvidenceValidation(EvidenceBinding(request.policy, bundle.evidence))
            if not evidence.valid:
                return self._a07_rejection(request, bundle, stage)
            stage = RuntimeDiagnosticStage.A07_E03
            direction = DirectionValidation(
                DirectionalDecision(request.policy, evidence, bundle.directional_facts)
            )
            if not direction.valid or direction.decision.direction is StrategyDirection.NO_TRADE:
                no_signal = _entry(
                    RuntimeDiagnosticCode.NO_SIGNAL,
                    stage,
                    DiagnosticSeverity.INFO,
                    request.request_id,
                    "A07 completed without an actionable signal",
                )
                return _result(
                    request.request_id,
                    StrategyRuntimeState.NO_SIGNAL,
                    stage,
                    (no_signal,),
                    bundle=bundle,
                )
            stage = RuntimeDiagnosticStage.A07_E04
            entry = EntryValidation(EntryPrice(direction, bundle.entry_facts))
            stage = RuntimeDiagnosticStage.A07_E05
            stop = StopValidation(StopLoss(entry, bundle.stop_facts))
            stage = RuntimeDiagnosticStage.A07_E06
            target = TargetValidation(TakeProfit(entry, bundle.target_facts))
            stage = RuntimeDiagnosticStage.A07_E07
            reward_risk = RewardRiskValidation(RewardRiskOutcome(entry, stop, target))
            if not reward_risk.valid:
                return self._a07_rejection(request, bundle, stage)
            stage = RuntimeDiagnosticStage.A07_E08
            confidence = StrategyConfidence(evidence, direction, reward_risk, bundle.confidence)
            expiration = SignalExpiration(foundation, confidence)
            confidence_validation = ConfidenceValidation(confidence, expiration)
            if not confidence_validation.valid:
                return self._a07_rejection(request, bundle, stage)
            stage = RuntimeDiagnosticStage.A07_E09
            signal = SignalValidation(StrategySignal(confidence_validation))
            envelope = StrategySignalEnvelope.create(
                signal=signal.signal,
                context=request.context,
                adapter_identity=request.adapter_identity,
                provenance_manifest_id=bundle.provenance.manifest_id,
                runtime_version=RUNTIME_VERSION,
            )
        except Exception:  # noqa: BLE001 - governed sanitizing A07 boundary
            return self._a07_rejection(request, bundle, stage)
        accepted = _entry(
            RuntimeDiagnosticCode.SIGNAL_ACCEPTED,
            RuntimeDiagnosticStage.RESULT,
            DiagnosticSeverity.INFO,
            request.request_id,
            "A07 signal accepted",
        )
        return _result(
            request.request_id,
            StrategyRuntimeState.ACCEPTED_SIGNAL,
            RuntimeDiagnosticStage.RESULT,
            (accepted,),
            bundle=bundle,
            envelope=envelope,
        )

    @staticmethod
    def _invalid(
        request_id: str,
        stage: RuntimeDiagnosticStage,
        *,
        bundle: StrategyFactBundle | None = None,
    ) -> StrategyRuntimeResult:
        invalid = _entry(
            RuntimeDiagnosticCode.INVALID_REQUEST,
            stage,
            DiagnosticSeverity.ERROR,
            request_id,
            "Runtime request or dependency coherence failed",
        )
        return _result(
            request_id,
            StrategyRuntimeState.INVALID_INPUT,
            stage,
            (invalid,),
            bundle=bundle,
        )

    @staticmethod
    def _adapter_failure(request_id: str) -> StrategyRuntimeResult:
        failure = _entry(
            RuntimeDiagnosticCode.ADAPTER_FAILED,
            RuntimeDiagnosticStage.ADAPTER,
            DiagnosticSeverity.ERROR,
            request_id,
            "Fact adapter failed unexpectedly",
        )
        return _result(
            request_id,
            StrategyRuntimeState.ADAPTER_FAILURE,
            RuntimeDiagnosticStage.ADAPTER,
            (failure,),
        )

    @staticmethod
    def _a07_rejection(
        request: StrategyRuntimeRequest,
        bundle: StrategyFactBundle,
        stage: RuntimeDiagnosticStage,
    ) -> StrategyRuntimeResult:
        rejection = _entry(
            RuntimeDiagnosticCode.A07_REJECTED,
            stage,
            DiagnosticSeverity.ERROR,
            request.request_id,
            "A07 rejected the accepted fact bundle",
        )
        return _result(
            request.request_id,
            StrategyRuntimeState.A07_REJECTION,
            stage,
            (rejection,),
            bundle=bundle,
        )
