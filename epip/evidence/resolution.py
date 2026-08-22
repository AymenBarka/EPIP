"""Deterministic declarative dependency-resolution planning for A04-E05."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.graph import DependencyGraph
from epip.evidence.model import DiagnosticCode, DiagnosticReason, ResolutionProfile
from epip.governance import GovernanceEpoch, RegistrySnapshot


class ResolutionDiagnostics(NamedTuple):
    """Immutable planning diagnostics preserving the complete graph context."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    requirement_identities: tuple[str, ...]
    dependency_graph: DependencyGraph
    dependency_ordering: tuple[str, ...]
    execution_layers: tuple[tuple[tuple[str, str], ...], ...]
    selected_candidate_identities: tuple[tuple[str, tuple[str, ...]], ...]
    reasons: tuple[DiagnosticReason, ...]


class ResolutionPlan(NamedTuple):
    """Immutable dependency-safe declarative plan without runtime semantics."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    resolution_profile: ResolutionProfile
    dependency_graph: DependencyGraph
    dependency_ordering: tuple[str, ...]
    execution_layers: tuple[tuple[tuple[str, str], ...], ...]
    selected_candidates: tuple[tuple[str, tuple[str, ...]], ...]
    diagnostics: ResolutionDiagnostics


class ResolutionPlanner:
    """Derive canonical dependency-safe layers from one verified E04 graph."""

    __slots__ = ()

    @classmethod
    def plan(
        cls,
        graph: DependencyGraph,
        profile: ResolutionProfile,
        snapshot: RegistrySnapshot,
    ) -> ResolutionPlan:
        if not isinstance(graph, DependencyGraph):
            raise DataIntegrityError("graph must be immutable DependencyGraph")
        if not isinstance(profile, ResolutionProfile):
            raise DataIntegrityError("profile must be immutable ResolutionProfile")
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be immutable RegistrySnapshot")

        reason = cls._completeness_reason(graph, snapshot)
        requirement_layers: tuple[tuple[str, ...], ...] = ()
        if reason is None:
            requirement_layers = cls._requirement_layers(graph)
            if not requirement_layers and graph.diagnostics.requirement_identities:
                reason = cls._reason(
                    DiagnosticCode.CYCLIC_DEPENDENCY,
                    "graph",
                    "dependency graph cannot produce an acyclic planning order",
                )

        dependency_ordering = tuple(
            requirement for layer in requirement_layers for requirement in layer
        )
        selected = graph.selected_candidates
        selected_by_requirement = dict(selected)
        execution_layers = tuple(
            tuple(
                sorted(
                    (requirement, candidate)
                    for requirement in layer
                    for candidate in selected_by_requirement[requirement]
                )
            )
            for layer in requirement_layers
            if any(selected_by_requirement[requirement] for requirement in layer)
        )
        reasons = graph.diagnostics.reasons
        if reason is not None:
            dependency_ordering = ()
            execution_layers = ()
            reasons = (*reasons, reason)

        diagnostics = ResolutionDiagnostics(
            graph.snapshot_identity,
            graph.manifest_reference,
            graph.governance_epoch,
            graph.diagnostics.requirement_identities,
            graph,
            dependency_ordering,
            execution_layers,
            selected,
            reasons,
        )
        return ResolutionPlan(
            graph.snapshot_identity,
            graph.manifest_reference,
            graph.governance_epoch,
            profile,
            graph,
            dependency_ordering,
            execution_layers,
            selected,
            diagnostics,
        )

    @classmethod
    def _completeness_reason(
        cls, graph: DependencyGraph, snapshot: RegistrySnapshot
    ) -> DiagnosticReason | None:
        diagnostics = graph.diagnostics
        if (
            graph.snapshot_identity != snapshot.snapshot_identity
            or graph.manifest_reference != snapshot.manifest_reference
            or graph.governance_epoch != snapshot.governance_epoch
            or diagnostics.snapshot_identity != graph.snapshot_identity
            or diagnostics.manifest_reference != graph.manifest_reference
            or diagnostics.governance_epoch != graph.governance_epoch
        ):
            return cls._reason(
                DiagnosticCode.INVALID_DEPENDENCY,
                "graph",
                "dependency graph context does not match the registry snapshot",
            )
        if (
            graph.nodes != tuple(sorted(set(graph.nodes)))
            or graph.edges != tuple(sorted(set(graph.edges)))
            or graph.selected_candidates
            != tuple(sorted(graph.selected_candidates, key=lambda item: item[0]))
            or diagnostics.graph_nodes != graph.nodes
            or diagnostics.graph_edges != graph.edges
            or diagnostics.selected_candidate_identities != graph.selected_candidates
        ):
            return cls._reason(
                DiagnosticCode.INVALID_DEPENDENCY,
                "graph",
                "dependency graph is not canonical or diagnostics-bound",
            )
        requirements = tuple(requirement for requirement, _ in graph.selected_candidates)
        if (
            len(set(requirements)) != len(requirements)
            or diagnostics.requirement_identities != requirements
            or diagnostics.dependency_identities
            != tuple(sorted(set(diagnostics.dependency_identities)))
        ):
            return cls._reason(
                DiagnosticCode.INVALID_DEPENDENCY,
                "graph",
                "dependency requirements are incomplete or non-canonical",
            )

        requirement_nodes = {f"requirement:{identity}" for identity in requirements}
        selected_bindings = {
            (f"requirement:{requirement}", f"provider:{candidate}")
            for requirement, candidates in graph.selected_candidates
            for candidate in candidates
        }
        provider_nodes = {target for _, target in selected_bindings}
        dependency_edges = {
            (f"requirement:{dependent}", f"requirement:{prerequisite}")
            for dependent, prerequisite in diagnostics.dependency_identities
        }
        fatal_codes = {
            DiagnosticCode.CYCLIC_DEPENDENCY,
            DiagnosticCode.INVALID_DEPENDENCY,
            DiagnosticCode.MISSING_MANDATORY_DEPENDENCY,
        }
        if any(item.code in fatal_codes for item in diagnostics.reasons):
            code = next(item.code for item in diagnostics.reasons if item.code in fatal_codes)
            return cls._reason(code, "graph", "dependency graph is marked invalid")
        if (
            set(graph.nodes) != requirement_nodes | provider_nodes
            or set(graph.edges) != selected_bindings | dependency_edges
            or any(
                dependent not in requirements or prerequisite not in requirements
                for dependent, prerequisite in diagnostics.dependency_identities
            )
        ):
            return cls._reason(
                DiagnosticCode.INVALID_DEPENDENCY,
                "graph",
                "dependency graph topology is incomplete",
            )
        registry_identities = tuple(
            f"{entry.producer_identity}@{entry.producer_version}" for entry in snapshot.entries
        )
        if any(
            registry_identities.count(candidate) != 1
            for _, candidates in graph.selected_candidates
            for candidate in candidates
        ):
            return cls._reason(
                DiagnosticCode.INELIGIBLE_PROVIDER,
                "graph",
                "selected candidate is not uniquely registry-bound",
            )
        return None

    @staticmethod
    def _requirement_layers(graph: DependencyGraph) -> tuple[tuple[str, ...], ...]:
        dependencies: dict[str, set[str]] = {
            requirement: set() for requirement in graph.diagnostics.requirement_identities
        }
        for dependent, prerequisite in graph.diagnostics.dependency_identities:
            dependencies[dependent].add(prerequisite)
        layers: list[tuple[str, ...]] = []
        while dependencies:
            ready = tuple(sorted(node for node, values in dependencies.items() if not values))
            if not ready:
                return ()
            layers.append(ready)
            for node in ready:
                del dependencies[node]
            for values in dependencies.values():
                values.difference_update(ready)
        return tuple(layers)

    @staticmethod
    def _reason(code: DiagnosticCode, requirement_id: str, reason: str) -> DiagnosticReason:
        return DiagnosticReason(code, requirement_id, reason)
