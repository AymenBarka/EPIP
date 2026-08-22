"""Deterministic terminal lineage verification for A04-E09."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.execution import ExecutionResult
from epip.evidence.model import DiagnosticCode, DiagnosticReason, ResolutionProfile
from epip.evidence.orchestration import ExecutionSchedule
from epip.evidence.tracking import ExecutionTrace
from epip.governance import GovernanceEpoch, RegistrySnapshot
from epip.producer import ProducerExecutionOutput

_ExecutionKey = tuple[str, str]
_ExecutionRecord = tuple[str, str, ProducerExecutionOutput]
_ExecutionBarrier = tuple[int, tuple[_ExecutionKey, ...]]
_VerificationResult = tuple[str, bool]
_CHECKS = (
    "lineage_completeness",
    "provenance_continuity",
    "dependency_continuity",
    "producer_continuity",
    "requirement_continuity",
    "execution_ordering_continuity",
    "execution_barrier_continuity",
)


class LineageDiagnostics(NamedTuple):
    """Immutable diagnostics preserving complete lineage verification context."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    execution_schedule: ExecutionSchedule
    execution_ordering: tuple[_ExecutionKey, ...]
    execution_barriers: tuple[_ExecutionBarrier, ...]
    producer_identities: tuple[str, ...]
    requirement_identities: tuple[str, ...]
    dependency_identities: tuple[tuple[str, str], ...]
    execution_history: tuple[_ExecutionRecord, ...]
    execution_trace: ExecutionTrace
    verification_results: tuple[_VerificationResult, ...]
    reasons: tuple[DiagnosticReason, ...]


class LineageReport(NamedTuple):
    """Immutable terminal report for one lineage verification."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    resolution_profile: ResolutionProfile
    execution_schedule: ExecutionSchedule
    execution_trace: ExecutionTrace
    verification_results: tuple[_VerificationResult, ...]
    verified: bool
    diagnostics: LineageDiagnostics


class LineageVerifier:
    """Verify continuity across frozen execution and tracking facts."""

    __slots__ = ()

    @classmethod
    def verify(
        cls,
        trace: ExecutionTrace,
        result: ExecutionResult,
        schedule: ExecutionSchedule,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
    ) -> LineageReport:
        if not isinstance(trace, ExecutionTrace):
            raise DataIntegrityError("trace must be immutable ExecutionTrace")
        if not isinstance(result, ExecutionResult):
            raise DataIntegrityError("result must be immutable ExecutionResult")
        if not isinstance(schedule, ExecutionSchedule):
            raise DataIntegrityError("schedule must be immutable ExecutionSchedule")
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be immutable RegistrySnapshot")
        if not isinstance(profile, ResolutionProfile):
            raise DataIntegrityError("profile must be immutable ResolutionProfile")

        reason = cls._continuity_reason(trace, result, schedule, snapshot, profile)
        verified = reason is None
        verification_results = tuple((check, verified) for check in _CHECKS)
        reasons = trace.diagnostics.reasons
        if reason is not None:
            reasons = (*reasons, reason)
        diagnostics = LineageDiagnostics(
            trace.snapshot_identity,
            trace.manifest_reference,
            trace.governance_epoch,
            schedule,
            trace.execution_ordering,
            trace.execution_barriers,
            trace.producer_identities,
            trace.requirement_identities,
            trace.diagnostics.dependency_identities,
            trace.execution_history,
            trace,
            verification_results,
            reasons,
        )
        return LineageReport(
            trace.snapshot_identity,
            trace.manifest_reference,
            trace.governance_epoch,
            profile,
            schedule,
            trace,
            verification_results,
            verified,
            diagnostics,
        )

    @classmethod
    def _continuity_reason(
        cls,
        trace: ExecutionTrace,
        result: ExecutionResult,
        schedule: ExecutionSchedule,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
    ) -> DiagnosticReason | None:
        diagnostics = trace.diagnostics
        if (
            trace.snapshot_identity != snapshot.snapshot_identity
            or trace.manifest_reference != snapshot.manifest_reference
            or trace.governance_epoch != snapshot.governance_epoch
            or trace.resolution_profile != profile
            or trace.execution_schedule != schedule
            or result.execution_schedule != schedule
            or result.snapshot_identity != trace.snapshot_identity
            or result.manifest_reference != trace.manifest_reference
            or result.governance_epoch != trace.governance_epoch
            or result.resolution_profile != profile
            or schedule.scheduled_executions
            != tuple(item for layer in schedule.execution_layers for item in layer)
            or schedule.execution_barriers
            != tuple((index, layer) for index, layer in enumerate(schedule.execution_layers))
        ):
            return cls._reason("lineage context is inconsistent")
        if (
            diagnostics.snapshot_identity != trace.snapshot_identity
            or diagnostics.manifest_reference != trace.manifest_reference
            or diagnostics.governance_epoch != trace.governance_epoch
            or diagnostics.execution_schedule != schedule
            or diagnostics.execution_ordering != trace.execution_ordering
            or diagnostics.execution_barriers != trace.execution_barriers
            or diagnostics.producer_identities != trace.producer_identities
            or diagnostics.requirement_identities != trace.requirement_identities
            or diagnostics.execution_outcomes != trace.execution_history
            or diagnostics.execution_trace != trace.execution_history
        ):
            return cls._reason("tracking diagnostics are incomplete")
        fatal_codes = {
            DiagnosticCode.CYCLIC_DEPENDENCY,
            DiagnosticCode.INVALID_DEPENDENCY,
            DiagnosticCode.MISSING_MANDATORY_DEPENDENCY,
        }
        if any(item.code in fatal_codes for item in diagnostics.reasons):
            return cls._reason("execution trace is marked invalid")

        ordering = schedule.scheduled_executions
        history_keys = tuple(
            (requirement, identity) for requirement, identity, _ in trace.execution_history
        )
        requirements = tuple(requirement for requirement, _ in ordering)
        producers = tuple(identity for _, identity in ordering)
        if (
            trace.execution_ordering != ordering
            or trace.execution_barriers != schedule.execution_barriers
            or trace.dependency_ordering != schedule.dependency_ordering
            or trace.requirement_identities != requirements
            or trace.producer_identities != producers
            or history_keys != ordering
            or result.execution_ordering != ordering
            or result.execution_barriers != schedule.execution_barriers
            or result.outcomes != trace.execution_history
        ):
            return cls._reason("lineage history is incomplete")

        dependencies = tuple(
            sorted(set(schedule.resolution_plan.dependency_graph.diagnostics.dependency_identities))
        )
        if diagnostics.dependency_identities != dependencies:
            return cls._reason("dependency lineage is inconsistent")
        requirement_set = set(requirements)
        order_index = {requirement: index for index, requirement in enumerate(requirements)}
        layer_index = {
            requirement: index
            for index, layer in enumerate(schedule.execution_layers)
            for requirement, _ in layer
        }
        for dependent, prerequisite in dependencies:
            if (
                dependent not in requirement_set
                or prerequisite not in requirement_set
                or order_index[prerequisite] >= order_index[dependent]
                or layer_index[prerequisite] >= layer_index[dependent]
            ):
                return cls._reason("dependency lineage is broken")

        registry_entries = {
            f"{entry.producer_identity}@{entry.producer_version}": entry
            for entry in snapshot.entries
        }
        for requirement, identity, output in trace.execution_history:
            producer_identity, producer_version = identity.rsplit("@", 1)
            if (
                not requirement
                or identity not in registry_entries
                or not isinstance(output, ProducerExecutionOutput)
                or output.input_manifest_reference != trace.manifest_reference
                or output.producer_identity != producer_identity
                or output.producer_version != producer_version
                or output.contract_version != registry_entries[identity].producer_contract_version
                or output.outcome not in {"success", "valid_empty"}
            ):
                return cls._reason("producer provenance is discontinuous")
        return None

    @staticmethod
    def _reason(reason: str) -> DiagnosticReason:
        return DiagnosticReason(DiagnosticCode.INVALID_DEPENDENCY, "lineage", reason)
