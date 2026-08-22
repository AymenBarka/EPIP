"""Deterministic immutable execution tracking for A04-E08."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.execution import ExecutionResult
from epip.evidence.model import DiagnosticCode, DiagnosticReason, ResolutionProfile
from epip.evidence.orchestration import ExecutionSchedule
from epip.governance import GovernanceEpoch, RegistrySnapshot
from epip.producer import ProducerExecutionOutput

_ExecutionKey = tuple[str, str]
_ExecutionRecord = tuple[str, str, ProducerExecutionOutput]
_ExecutionBarrier = tuple[int, tuple[_ExecutionKey, ...]]


class TrackingDiagnostics(NamedTuple):
    """Immutable diagnostics preserving the complete execution trace context."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    execution_schedule: ExecutionSchedule
    execution_ordering: tuple[_ExecutionKey, ...]
    execution_barriers: tuple[_ExecutionBarrier, ...]
    producer_identities: tuple[str, ...]
    requirement_identities: tuple[str, ...]
    dependency_identities: tuple[tuple[str, str], ...]
    execution_outcomes: tuple[_ExecutionRecord, ...]
    execution_trace: tuple[_ExecutionRecord, ...]
    reasons: tuple[DiagnosticReason, ...]


class ExecutionTrace(NamedTuple):
    """Immutable declarative history projected from one verified E07 result."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    resolution_profile: ResolutionProfile
    execution_schedule: ExecutionSchedule
    dependency_ordering: tuple[str, ...]
    execution_ordering: tuple[_ExecutionKey, ...]
    execution_barriers: tuple[_ExecutionBarrier, ...]
    producer_identities: tuple[str, ...]
    requirement_identities: tuple[str, ...]
    execution_history: tuple[_ExecutionRecord, ...]
    diagnostics: TrackingDiagnostics


class ExecutionTracker:
    """Project one immutable E07 result into canonical tracking history."""

    __slots__ = ()

    @classmethod
    def track(
        cls,
        result: ExecutionResult,
        schedule: ExecutionSchedule,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
    ) -> ExecutionTrace:
        if not isinstance(result, ExecutionResult):
            raise DataIntegrityError("result must be immutable ExecutionResult")
        if not isinstance(schedule, ExecutionSchedule):
            raise DataIntegrityError("schedule must be immutable ExecutionSchedule")
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be immutable RegistrySnapshot")
        if not isinstance(profile, ResolutionProfile):
            raise DataIntegrityError("profile must be immutable ResolutionProfile")

        reason = cls._inconsistency_reason(result, schedule, snapshot, profile)
        history = result.outcomes if reason is None else ()
        ordering = result.execution_ordering if reason is None else ()
        barriers = result.execution_barriers if reason is None else ()
        requirements = tuple(requirement for requirement, _ in ordering)
        producers = tuple(identity for _, identity in ordering)
        dependency_identities = tuple(
            sorted(set(schedule.resolution_plan.dependency_graph.diagnostics.dependency_identities))
        )
        reasons = result.diagnostics.reasons
        if reason is not None:
            reasons = (*reasons, reason)

        diagnostics = TrackingDiagnostics(
            schedule.snapshot_identity,
            schedule.manifest_reference,
            schedule.governance_epoch,
            schedule,
            ordering,
            barriers,
            producers,
            requirements,
            dependency_identities,
            history,
            history,
            reasons,
        )
        return ExecutionTrace(
            schedule.snapshot_identity,
            schedule.manifest_reference,
            schedule.governance_epoch,
            profile,
            schedule,
            schedule.dependency_ordering,
            ordering,
            barriers,
            producers,
            requirements,
            history,
            diagnostics,
        )

    @classmethod
    def _inconsistency_reason(
        cls,
        result: ExecutionResult,
        schedule: ExecutionSchedule,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
    ) -> DiagnosticReason | None:
        diagnostics = result.diagnostics
        if (
            result.snapshot_identity != snapshot.snapshot_identity
            or result.manifest_reference != snapshot.manifest_reference
            or result.governance_epoch != snapshot.governance_epoch
            or result.resolution_profile != profile
            or result.execution_schedule != schedule
            or schedule.snapshot_identity != snapshot.snapshot_identity
            or schedule.manifest_reference != snapshot.manifest_reference
            or schedule.governance_epoch != snapshot.governance_epoch
            or schedule.resolution_profile != profile
            or schedule.scheduled_executions
            != tuple(item for layer in schedule.execution_layers for item in layer)
            or schedule.execution_barriers
            != tuple((index, layer) for index, layer in enumerate(schedule.execution_layers))
        ):
            return cls._reason("execution tracking context is inconsistent")
        if (
            diagnostics.snapshot_identity != result.snapshot_identity
            or diagnostics.manifest_reference != result.manifest_reference
            or diagnostics.governance_epoch != result.governance_epoch
            or diagnostics.execution_schedule != schedule
            or diagnostics.execution_layers != schedule.execution_layers
            or diagnostics.executed_provider_identities
            != tuple(identity for _, identity in result.execution_ordering)
            or diagnostics.execution_ordering != result.execution_ordering
            or diagnostics.execution_barriers != result.execution_barriers
            or diagnostics.outcomes != result.outcomes
            or diagnostics.reasons != schedule.diagnostics.reasons
        ):
            return cls._reason("execution diagnostics are inconsistent")
        expected_ordering = schedule.scheduled_executions
        expected_barriers = schedule.execution_barriers
        outcome_keys = tuple(
            (requirement, identity) for requirement, identity, _ in result.outcomes
        )
        if (
            result.execution_ordering != expected_ordering
            or result.execution_barriers != expected_barriers
            or outcome_keys != expected_ordering
        ):
            return cls._reason("execution history is incomplete or non-canonical")

        registry_entries = {
            f"{entry.producer_identity}@{entry.producer_version}": entry
            for entry in snapshot.entries
        }
        for requirement, identity, output in result.outcomes:
            producer_identity, producer_version = identity.rsplit("@", 1)
            if (
                not requirement
                or identity not in registry_entries
                or not isinstance(output, ProducerExecutionOutput)
                or output.input_manifest_reference != result.manifest_reference
                or output.producer_identity != producer_identity
                or output.producer_version != producer_version
                or output.contract_version != registry_entries[identity].producer_contract_version
                or output.outcome not in {"success", "valid_empty"}
            ):
                return cls._reason("execution outcome is inconsistent")
        return None

    @staticmethod
    def _reason(reason: str) -> DiagnosticReason:
        return DiagnosticReason(DiagnosticCode.INVALID_DEPENDENCY, "tracking", reason)
