"""Deterministic declarative execution orchestration for A04-E06."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.graph import DependencyGraph
from epip.evidence.model import DiagnosticCode, DiagnosticReason, ResolutionProfile
from epip.evidence.resolution import ResolutionPlan
from epip.governance import GovernanceEpoch, RegistrySnapshot


class OrchestrationDiagnostics(NamedTuple):
    """Immutable orchestration diagnostics preserving all scheduling context."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    resolution_plan: ResolutionPlan
    dependency_graph: DependencyGraph
    execution_layers: tuple[tuple[tuple[str, str], ...], ...]
    execution_schedule: tuple[tuple[int, tuple[tuple[str, str], ...]], ...]
    selected_candidates: tuple[tuple[str, tuple[str, ...]], ...]
    reasons: tuple[DiagnosticReason, ...]


class ExecutionSchedule(NamedTuple):
    """Immutable barrier-preserving declarative execution schedule."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    resolution_profile: ResolutionProfile
    resolution_plan: ResolutionPlan
    dependency_ordering: tuple[str, ...]
    execution_layers: tuple[tuple[tuple[str, str], ...], ...]
    execution_barriers: tuple[tuple[int, tuple[tuple[str, str], ...]], ...]
    scheduled_executions: tuple[tuple[str, str], ...]
    diagnostics: OrchestrationDiagnostics


class ExecutionOrchestrator:
    """Project one verified E05 plan into canonical declarative barriers."""

    __slots__ = ()

    @classmethod
    def orchestrate(
        cls,
        plan: ResolutionPlan,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
    ) -> ExecutionSchedule:
        if not isinstance(plan, ResolutionPlan):
            raise DataIntegrityError("plan must be immutable ResolutionPlan")
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be immutable RegistrySnapshot")
        if not isinstance(profile, ResolutionProfile):
            raise DataIntegrityError("profile must be immutable ResolutionProfile")

        reason = cls._completeness_reason(plan, snapshot, profile)
        layers = plan.execution_layers if reason is None else ()
        ordering = plan.dependency_ordering if reason is None else ()
        barriers = tuple((index, layer) for index, layer in enumerate(layers))
        scheduled = tuple(binding for layer in layers for binding in layer)
        reasons = plan.diagnostics.reasons
        if reason is not None:
            reasons = (*reasons, reason)

        diagnostics = OrchestrationDiagnostics(
            plan.snapshot_identity,
            plan.manifest_reference,
            plan.governance_epoch,
            plan,
            plan.dependency_graph,
            layers,
            barriers,
            plan.selected_candidates,
            reasons,
        )
        return ExecutionSchedule(
            plan.snapshot_identity,
            plan.manifest_reference,
            plan.governance_epoch,
            profile,
            plan,
            ordering,
            layers,
            barriers,
            scheduled,
            diagnostics,
        )

    @classmethod
    def _completeness_reason(
        cls,
        plan: ResolutionPlan,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
    ) -> DiagnosticReason | None:
        diagnostics = plan.diagnostics
        if (
            plan.snapshot_identity != snapshot.snapshot_identity
            or plan.manifest_reference != snapshot.manifest_reference
            or plan.governance_epoch != snapshot.governance_epoch
            or plan.resolution_profile != profile
            or diagnostics.snapshot_identity != plan.snapshot_identity
            or diagnostics.manifest_reference != plan.manifest_reference
            or diagnostics.governance_epoch != plan.governance_epoch
        ):
            return cls._reason("orchestration context is inconsistent")
        if (
            plan.dependency_graph != diagnostics.dependency_graph
            or plan.dependency_ordering != diagnostics.dependency_ordering
            or plan.execution_layers != diagnostics.execution_layers
            or plan.selected_candidates != diagnostics.selected_candidate_identities
        ):
            return cls._reason("resolution plan diagnostics are incomplete")
        requirements = tuple(requirement for requirement, _ in plan.selected_candidates)
        if (
            requirements != tuple(sorted(set(requirements)))
            or plan.dependency_ordering != tuple(dict.fromkeys(plan.dependency_ordering))
            or set(plan.dependency_ordering) != set(requirements)
            or any(
                layer != tuple(sorted(set(layer))) or not layer for layer in plan.execution_layers
            )
        ):
            return cls._reason("resolution plan ordering is incomplete or non-canonical")

        expected = {
            (requirement, candidate)
            for requirement, candidates in plan.selected_candidates
            for candidate in candidates
        }
        scheduled = tuple(binding for layer in plan.execution_layers for binding in layer)
        if len(scheduled) != len(set(scheduled)) or set(scheduled) != expected:
            return cls._reason("resolution plan candidate schedule is incomplete")
        layer_by_requirement = {
            requirement: index
            for index, layer in enumerate(plan.execution_layers)
            for requirement, _ in layer
        }
        order_index = {
            requirement: index for index, requirement in enumerate(plan.dependency_ordering)
        }
        for dependent, prerequisite in plan.dependency_graph.diagnostics.dependency_identities:
            if order_index[prerequisite] >= order_index[dependent]:
                return cls._reason("resolution plan violates dependency ordering")
            if (
                dependent in layer_by_requirement
                and prerequisite in layer_by_requirement
                and layer_by_requirement[prerequisite] >= layer_by_requirement[dependent]
            ):
                return cls._reason("resolution plan violates execution barriers")
        fatal_codes = {
            DiagnosticCode.CYCLIC_DEPENDENCY,
            DiagnosticCode.INVALID_DEPENDENCY,
            DiagnosticCode.MISSING_MANDATORY_DEPENDENCY,
        }
        if any(reason.code in fatal_codes for reason in diagnostics.reasons):
            return cls._reason("resolution plan is marked invalid")
        return None

    @staticmethod
    def _reason(reason: str) -> DiagnosticReason:
        return DiagnosticReason(DiagnosticCode.INVALID_DEPENDENCY, "orchestration", reason)
