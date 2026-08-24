"""Strategy Runtime request, result, and structured diagnostic contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import CONTRACT_VERSION, digest, text, unique_texts
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.facts import AnalyticalInputBundle
from epip.strategy_runtime.profile import StrategyProfileIdentity
from epip.strategy_runtime.provenance import FactAdapterIdentity
from epip.strategy_runtime.signal_envelope import StrategySignalEnvelope


class StrategyRuntimeState(Enum):
    ACCEPTED_SIGNAL = "ACCEPTED_SIGNAL"
    NO_SIGNAL = "NO_SIGNAL"
    REJECTED = "REJECTED"
    INVALID_INPUT = "INVALID_INPUT"
    ADAPTER_FAILURE = "ADAPTER_FAILURE"
    A07_REJECTION = "A07_REJECTION"


class DiagnosticSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RuntimeDiagnosticStage(Enum):
    REQUEST = "REQUEST"
    COHERENCE = "COHERENCE"
    TEMPORAL = "TEMPORAL"
    PROFILE = "PROFILE"
    ADAPTER = "ADAPTER"
    A07_E00 = "A07_E00"
    A07_E01 = "A07_E01"
    A07_E02 = "A07_E02"
    A07_E03 = "A07_E03"
    A07_E04 = "A07_E04"
    A07_E05 = "A07_E05"
    A07_E06 = "A07_E06"
    A07_E07 = "A07_E07"
    A07_E08 = "A07_E08"
    A07_E09 = "A07_E09"
    RESULT = "RESULT"


class RuntimeDiagnosticCode(Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    COHERENCE_FAILURE = "COHERENCE_FAILURE"
    TEMPORAL_FAILURE = "TEMPORAL_FAILURE"
    PROFILE_MISMATCH = "PROFILE_MISMATCH"
    MISSING_FACT = "MISSING_FACT"
    ADAPTER_REJECTED = "ADAPTER_REJECTED"
    ADAPTER_FAILED = "ADAPTER_FAILED"
    A07_REJECTED = "A07_REJECTED"
    NO_SIGNAL = "NO_SIGNAL"
    SIGNAL_ACCEPTED = "SIGNAL_ACCEPTED"


@dataclass(frozen=True, slots=True)
class RuntimeDiagnostic:
    code: RuntimeDiagnosticCode
    stage: RuntimeDiagnosticStage
    severity: DiagnosticSeverity
    subject_ref: str
    source_refs: tuple[str, ...]
    message: str

    def __post_init__(self) -> None:
        if (
            type(self.code) is not RuntimeDiagnosticCode
            or type(self.stage) is not RuntimeDiagnosticStage
        ):
            raise DataIntegrityError("diagnostic code/stage has the wrong type")
        if type(self.severity) is not DiagnosticSeverity:
            raise DataIntegrityError("diagnostic severity has the wrong type")
        object.__setattr__(self, "subject_ref", text(self.subject_ref, "subject_ref"))
        object.__setattr__(self, "source_refs", unique_texts(self.source_refs, "source_refs"))
        object.__setattr__(self, "message", text(self.message, "message"))


@dataclass(frozen=True, slots=True)
class StrategyRuntimeDiagnostics:
    diagnostics_id: str
    final_state: StrategyRuntimeState
    last_completed_stage: RuntimeDiagnosticStage
    entries: tuple[RuntimeDiagnostic, ...]

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple or any(
            type(item) is not RuntimeDiagnostic for item in self.entries
        ):
            raise DataIntegrityError("diagnostic entries have the wrong type")
        entries = tuple(
            sorted(
                set(self.entries),
                key=lambda item: (
                    item.stage.value,
                    item.severity.value,
                    item.code.value,
                    item.subject_ref,
                ),
            )
        )
        object.__setattr__(self, "entries", entries)
        if self.diagnostics_id != digest(self, exclude=frozenset({"diagnostics_id"})):
            raise DataIntegrityError("diagnostics_id does not match canonical entries")

    @classmethod
    def create(
        cls,
        final_state: StrategyRuntimeState,
        last_completed_stage: RuntimeDiagnosticStage,
        entries: tuple[RuntimeDiagnostic, ...],
    ) -> StrategyRuntimeDiagnostics:
        canonical_entries = tuple(
            sorted(
                set(entries),
                key=lambda item: (
                    item.stage.value,
                    item.severity.value,
                    item.code.value,
                    item.subject_ref,
                ),
            )
        )
        candidate = object.__new__(cls)
        values = (final_state, last_completed_stage, canonical_entries)
        object.__setattr__(candidate, "diagnostics_id", "")
        for name, value in zip(
            ("final_state", "last_completed_stage", "entries"), values, strict=True
        ):
            object.__setattr__(candidate, name, value)
        return cls(digest(candidate, exclude=frozenset({"diagnostics_id"})), *values)


@dataclass(frozen=True, slots=True)
class StrategyRuntimeOptions:
    validate_optional_freshness: bool = True
    fail_on_warnings: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.validate_optional_freshness) is not bool
            or type(self.fail_on_warnings) is not bool
        ):
            raise DataIntegrityError("runtime options must be bool values")


@dataclass(frozen=True, slots=True)
class StrategyRuntimeRequest:
    contract_version: str
    request_id: str
    context: EvaluationContext
    inputs: AnalyticalInputBundle
    policy: StrategyPolicy
    profile_identity: StrategyProfileIdentity
    adapter_identity: FactAdapterIdentity
    runtime_contract_version: str
    options: StrategyRuntimeOptions

    def __post_init__(self) -> None:
        if (
            self.contract_version != CONTRACT_VERSION
            or self.runtime_contract_version != CONTRACT_VERSION
        ):
            raise DataIntegrityError("unsupported runtime request version")
        if self.profile_identity != self.context.profile_identity:
            raise DataIntegrityError("request and context profiles differ")
        if self.request_id != digest(self, exclude=frozenset({"request_id"})):
            raise DataIntegrityError("request_id does not match canonical request")


@dataclass(frozen=True, slots=True)
class StrategyRuntimeResult:
    contract_version: str
    result_id: str
    request_id: str
    state: StrategyRuntimeState
    fact_bundle_id: str | None
    signal_envelope: StrategySignalEnvelope | None
    diagnostics: StrategyRuntimeDiagnostics
    runtime_version: str

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported runtime result version")
        for name in ("request_id", "runtime_version"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        accepted = self.state is StrategyRuntimeState.ACCEPTED_SIGNAL
        if accepted != (self.signal_envelope is not None):
            raise DataIntegrityError("only ACCEPTED_SIGNAL may contain an envelope")
        if self.diagnostics.final_state is not self.state:
            raise DataIntegrityError("result and diagnostics states differ")
        if self.result_id != digest(self, exclude=frozenset({"result_id"})):
            raise DataIntegrityError("result_id does not match canonical result")
