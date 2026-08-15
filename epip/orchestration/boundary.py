"""Fail-closed enforcement of the EPIP-017 foundational system boundary.

Origin ADRs: ADR-EPIP017-01, Decision sections 1-6 and Invariants 1-17;
ADR-EPIP017-15, Handoff Authority and Boundary Acceptance Authority.
Blueprint: Programme A Phase 1 v1.1, A01-F Foundational Boundary.
Responsibility: authority separation, authority-scope validation, prohibited-
operation detection, and protection of the EPIP-016 handoff boundary.

The declarations here authorize no planning, scheduling, producer execution,
result commitment, replay, persistence, recovery, or handoff implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Final

from epip.core.exceptions import BoundaryViolationError


class OrchestrationAuthority(str, Enum):
    """Programme A Blueprint v1.1 A01-F authorities governed by ADR-01 and ADR-15."""

    CONTROL_PLANE = "control_plane"
    EXECUTION_PLANE = "execution_plane"
    PRODUCER = "producer"
    REGISTRY = "registry"
    EXECUTION_LEDGER = "execution_ledger"
    DURABLE_RESULT = "durable_result"
    CACHE = "cache"
    REPLAY = "replay"
    AUDIT = "audit"
    HANDOFF = "handoff"
    BOUNDARY_ACCEPTANCE = "boundary_acceptance"
    EPIP016 = "epip016"


class BoundaryOperation(str, Enum):
    """Programme A Blueprint v1.1 A01-F operations governed by ADR-01 and ADR-15."""

    ADMIT_PIPELINE_REQUEST = "admit_pipeline_request"
    SELECT_REGISTRY_SNAPSHOT = "select_registry_snapshot"
    RESOLVE_DECLARED_DEPENDENCIES = "resolve_declared_dependencies"
    CONSTRUCT_SEMANTIC_GRAPH = "construct_semantic_graph"
    CONSTRUCT_SEMANTIC_PLAN = "construct_semantic_plan"
    DEFINE_EVIDENCE_COMPLETENESS = "define_evidence_completeness"
    AUTHORIZE_DISPATCH = "authorize_dispatch"
    DETERMINE_HANDOFF_ELIGIBILITY = "determine_handoff_eligibility"
    DISPATCH_AUTHORIZED_INVOCATION = "dispatch_authorized_invocation"
    ENFORCE_OPERATIONAL_RULES = "enforce_operational_rules"
    RECORD_ATTEMPT = "record_attempt"
    SUBMIT_CANDIDATE_RESULT = "submit_candidate_result"
    PRODUCE_OPERATIONAL_TELEMETRY = "produce_operational_telemetry"
    EXECUTE_ANALYTICAL_TRANSFORMATION = "execute_analytical_transformation"
    ADMIT_PRODUCER = "admit_producer"
    PUBLISH_REGISTRY_SNAPSHOT = "publish_registry_snapshot"
    RECORD_INVOCATION_TRANSITION = "record_invocation_transition"
    COMMIT_DURABLE_RESULT = "commit_durable_result"
    PROVIDE_ACCELERATION_STATE = "provide_acceleration_state"
    SUPPLY_REPLAY_BOUNDARY = "supply_replay_boundary"
    EVALUATE_AUTHORITATIVE_RECORDS = "evaluate_authoritative_records"
    VALIDATE_HANDOFF_MANIFEST = "validate_handoff_manifest"
    ACCEPT_OR_REJECT_HANDOFF = "accept_or_reject_handoff"
    REGISTER_EVIDENCE = "register_evidence"
    PERFORM_INFERENCE = "perform_inference"
    BUILD_DECISION_GRAPH = "build_decision_graph"
    GENERATE_CANDIDATE = "generate_candidate"
    ASSESS_CONFIDENCE = "assess_confidence"
    SELECT_DECISION = "select_decision"


class OrchestrationBoundaryViolation(BoundaryViolationError):
    """Programme A Blueprint v1.1 A01-F rejection governed by ADR-01 and ADR-15."""


_AUTHORITY_SCOPES: Final[Mapping[OrchestrationAuthority, frozenset[BoundaryOperation]]] = (
    MappingProxyType(
        {
            OrchestrationAuthority.CONTROL_PLANE: frozenset(
                {
                    BoundaryOperation.ADMIT_PIPELINE_REQUEST,
                    BoundaryOperation.SELECT_REGISTRY_SNAPSHOT,
                    BoundaryOperation.RESOLVE_DECLARED_DEPENDENCIES,
                    BoundaryOperation.CONSTRUCT_SEMANTIC_GRAPH,
                    BoundaryOperation.CONSTRUCT_SEMANTIC_PLAN,
                    BoundaryOperation.DEFINE_EVIDENCE_COMPLETENESS,
                    BoundaryOperation.AUTHORIZE_DISPATCH,
                    BoundaryOperation.DETERMINE_HANDOFF_ELIGIBILITY,
                }
            ),
            OrchestrationAuthority.EXECUTION_PLANE: frozenset(
                {
                    BoundaryOperation.DISPATCH_AUTHORIZED_INVOCATION,
                    BoundaryOperation.ENFORCE_OPERATIONAL_RULES,
                    BoundaryOperation.RECORD_ATTEMPT,
                    BoundaryOperation.SUBMIT_CANDIDATE_RESULT,
                    BoundaryOperation.PRODUCE_OPERATIONAL_TELEMETRY,
                }
            ),
            OrchestrationAuthority.PRODUCER: frozenset(
                {BoundaryOperation.EXECUTE_ANALYTICAL_TRANSFORMATION}
            ),
            OrchestrationAuthority.REGISTRY: frozenset(
                {
                    BoundaryOperation.ADMIT_PRODUCER,
                    BoundaryOperation.PUBLISH_REGISTRY_SNAPSHOT,
                }
            ),
            OrchestrationAuthority.EXECUTION_LEDGER: frozenset(
                {BoundaryOperation.RECORD_INVOCATION_TRANSITION}
            ),
            OrchestrationAuthority.DURABLE_RESULT: frozenset(
                {BoundaryOperation.COMMIT_DURABLE_RESULT}
            ),
            OrchestrationAuthority.CACHE: frozenset({BoundaryOperation.PROVIDE_ACCELERATION_STATE}),
            OrchestrationAuthority.REPLAY: frozenset({BoundaryOperation.SUPPLY_REPLAY_BOUNDARY}),
            OrchestrationAuthority.AUDIT: frozenset(
                {BoundaryOperation.EVALUATE_AUTHORITATIVE_RECORDS}
            ),
            OrchestrationAuthority.HANDOFF: frozenset(
                {BoundaryOperation.VALIDATE_HANDOFF_MANIFEST}
            ),
            OrchestrationAuthority.BOUNDARY_ACCEPTANCE: frozenset(
                {BoundaryOperation.ACCEPT_OR_REJECT_HANDOFF}
            ),
            OrchestrationAuthority.EPIP016: frozenset(
                {
                    BoundaryOperation.REGISTER_EVIDENCE,
                    BoundaryOperation.PERFORM_INFERENCE,
                    BoundaryOperation.BUILD_DECISION_GRAPH,
                    BoundaryOperation.GENERATE_CANDIDATE,
                    BoundaryOperation.ASSESS_CONFIDENCE,
                    BoundaryOperation.SELECT_DECISION,
                }
            ),
        }
    )
)


def enforce_authority_scope(
    authority: OrchestrationAuthority,
    operation: BoundaryOperation,
) -> None:
    """Accept an explicitly owned operation or reject it fail-closed.

    Programme A Blueprint v1.1 section A01-F acceptance criterion: an authority
    can exercise only responsibilities assigned by ADR-EPIP017-01 and
    ADR-EPIP017-15. Unknown values and cross-authority calls are rejected; this
    function performs no authorized operation itself.
    """

    if not isinstance(authority, OrchestrationAuthority):
        raise OrchestrationBoundaryViolation("unknown orchestration authority")
    if not isinstance(operation, BoundaryOperation):
        raise OrchestrationBoundaryViolation("unknown boundary operation")
    if operation not in _AUTHORITY_SCOPES[authority]:
        raise OrchestrationBoundaryViolation(
            f"{authority.value} is not authorized for {operation.value}"
        )
