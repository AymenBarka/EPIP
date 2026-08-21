"""Deterministic declarative dependency-graph construction for A04-E04."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.model import (
    DependencyType,
    DiagnosticCode,
    DiagnosticReason,
    EvidenceRequirement,
)
from epip.evidence.selection import SelectionDiagnostics
from epip.governance import GovernanceEpoch, RegistrySnapshot


class DependencyDiagnostics(NamedTuple):
    """Immutable graph diagnostics bound to one frozen registry context."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    requirement_identities: tuple[str, ...]
    selected_candidate_identities: tuple[tuple[str, tuple[str, ...]], ...]
    dependency_identities: tuple[tuple[str, str], ...]
    graph_nodes: tuple[str, ...]
    graph_edges: tuple[tuple[str, str], ...]
    reasons: tuple[DiagnosticReason, ...]


class DependencyGraph(NamedTuple):
    """Immutable canonical dependency graph without execution semantics."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    selected_candidates: tuple[tuple[str, tuple[str, ...]], ...]
    diagnostics: DependencyDiagnostics


class DependencyGraphBuilder:
    """Expand verified selections into one canonical declarative graph."""

    __slots__ = ()

    @classmethod
    def build(
        cls,
        snapshot: RegistrySnapshot,
        selections: tuple[tuple[EvidenceRequirement, SelectionDiagnostics], ...],
        dependency_edges: tuple[tuple[str, str], ...] = (),
    ) -> DependencyGraph:
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be immutable RegistrySnapshot")
        bindings = cls._require_selections(selections)
        facts = tuple(sorted(set(cls._require_edges(dependency_edges))))
        requirements = {requirement.requirement_id: requirement for requirement, _ in bindings}
        if len(requirements) != len(bindings):
            raise DataIntegrityError("selection requirement identities must be unique")

        ordered = tuple(sorted(bindings, key=lambda item: item[0].requirement_id))
        reasons: list[DiagnosticReason] = []
        selected: list[tuple[str, tuple[str, ...]]] = []
        nodes = {cls._requirement_node(identifier) for identifier in requirements}
        edges: set[tuple[str, str]] = set()
        fatal = False

        for requirement, selection in ordered:
            reasons.extend(selection.diagnostics)
            identities = tuple(
                sorted(
                    f"{entry.producer_identity}@{entry.producer_version}"
                    for entry in selection.selected_candidates
                )
            )
            selected.append((requirement.requirement_id, identities))
            if not cls._selection_matches(snapshot, selection):
                reasons.append(
                    cls._reason(
                        DiagnosticCode.INVALID_DEPENDENCY,
                        requirement,
                        "selection context does not match the registry snapshot",
                    )
                )
                fatal = True
                continue
            if not identities and requirement.dependency_type is not DependencyType.OPTIONAL:
                reasons.append(
                    cls._reason(
                        DiagnosticCode.MISSING_MANDATORY_DEPENDENCY,
                        requirement,
                        "the dependency has no selected governed candidate",
                    )
                )
                fatal = True
            requirement_node = cls._requirement_node(requirement.requirement_id)
            for identity in identities:
                provider_node = cls._provider_node(identity)
                nodes.add(provider_node)
                edges.add((requirement_node, provider_node))

        for dependent, prerequisite in facts:
            if dependent not in requirements or prerequisite not in requirements:
                endpoint_requirement = requirements.get(dependent) or requirements.get(prerequisite)
                reasons.append(
                    cls._reason_for_identity(
                        DiagnosticCode.INVALID_DEPENDENCY,
                        (
                            endpoint_requirement.requirement_id
                            if endpoint_requirement is not None
                            else "graph"
                        ),
                        (
                            endpoint_requirement.semantic_version
                            if endpoint_requirement is not None
                            else None
                        ),
                        "dependency edge endpoint is absent",
                    )
                )
                fatal = True
                continue
            edges.add(
                (
                    cls._requirement_node(dependent),
                    cls._requirement_node(prerequisite),
                )
            )

        canonical_edges = tuple(sorted(edges))
        cycle_node = cls._cycle_node(tuple(sorted(nodes)), canonical_edges)
        if cycle_node is not None:
            identity = cycle_node.removeprefix("requirement:")
            requirement = requirements[identity]
            reasons.append(
                cls._reason(
                    DiagnosticCode.CYCLIC_DEPENDENCY,
                    requirement,
                    "dependency graph contains a cycle",
                )
            )
            fatal = True

        graph_nodes = () if fatal else tuple(sorted(nodes))
        graph_edges = () if fatal else canonical_edges
        selected_candidates = tuple(selected)
        diagnostics = DependencyDiagnostics(
            snapshot.snapshot_identity,
            snapshot.manifest_reference,
            snapshot.governance_epoch,
            tuple(sorted(requirements)),
            selected_candidates,
            facts,
            graph_nodes,
            graph_edges,
            tuple(reasons),
        )
        return DependencyGraph(
            snapshot.snapshot_identity,
            snapshot.manifest_reference,
            snapshot.governance_epoch,
            graph_nodes,
            graph_edges,
            selected_candidates,
            diagnostics,
        )

    @staticmethod
    def _require_selections(
        value: object,
    ) -> tuple[tuple[EvidenceRequirement, SelectionDiagnostics], ...]:
        if not isinstance(value, tuple):
            raise DataIntegrityError("selections must be an immutable tuple")
        for item in value:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], EvidenceRequirement)
                or not isinstance(item[1], SelectionDiagnostics)
            ):
                raise DataIntegrityError(
                    "selections must bind EvidenceRequirement to SelectionDiagnostics"
                )
        return value

    @staticmethod
    def _require_edges(value: object) -> tuple[tuple[str, str], ...]:
        if not isinstance(value, tuple):
            raise DataIntegrityError("dependency_edges must be an immutable tuple")
        for edge in value:
            if (
                not isinstance(edge, tuple)
                or len(edge) != 2
                or not all(isinstance(endpoint, str) and endpoint.strip() for endpoint in edge)
            ):
                raise DataIntegrityError("dependency edges must contain two non-empty identities")
        return value

    @staticmethod
    def _selection_matches(snapshot: RegistrySnapshot, selection: SelectionDiagnostics) -> bool:
        return (
            selection.snapshot_identity == snapshot.snapshot_identity
            and selection.manifest_reference == snapshot.manifest_reference
            and selection.governance_epoch == snapshot.governance_epoch
        )

    @staticmethod
    def _requirement_node(identity: str) -> str:
        return f"requirement:{identity}"

    @staticmethod
    def _provider_node(identity: str) -> str:
        return f"provider:{identity}"

    @staticmethod
    def _cycle_node(nodes: tuple[str, ...], edges: tuple[tuple[str, str], ...]) -> str | None:
        indegree = {node: 0 for node in nodes}
        outgoing: dict[str, list[str]] = {node: [] for node in nodes}
        for source, target in edges:
            outgoing[source].append(target)
            indegree[target] += 1
        ready = sorted(node for node, degree in indegree.items() if degree == 0)
        visited = 0
        while ready:
            node = ready.pop(0)
            visited += 1
            for target in sorted(outgoing[node]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
                    ready.sort()
        if visited == len(nodes):
            return None
        return min(
            node
            for node, degree in indegree.items()
            if degree > 0 and node.startswith("requirement:")
        )

    @classmethod
    def _reason(
        cls,
        code: DiagnosticCode,
        requirement: EvidenceRequirement,
        reason: str,
    ) -> DiagnosticReason:
        return cls._reason_for_identity(
            code,
            requirement.requirement_id,
            requirement.semantic_version,
            reason,
        )

    @staticmethod
    def _reason_for_identity(
        code: DiagnosticCode,
        requirement_id: str,
        semantic_version: str | None,
        reason: str,
    ) -> DiagnosticReason:
        return DiagnosticReason(code, requirement_id, reason, None, semantic_version)
