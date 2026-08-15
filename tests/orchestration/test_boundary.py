"""A01-F acceptance evidence for the EPIP-017 foundational boundary.

Origin: ADR-EPIP017-01 and ADR-EPIP017-15; Programme A Blueprint v1.1
gate A01-F.
"""

from __future__ import annotations

import pytest

from epip.orchestration import (
    BoundaryOperation,
    OrchestrationAuthority,
    OrchestrationBoundaryViolation,
    enforce_authority_scope,
)
from epip.orchestration.boundary import _AUTHORITY_SCOPES


@pytest.mark.parametrize(
    ("authority", "operation"),
    (
        (OrchestrationAuthority.CONTROL_PLANE, BoundaryOperation.AUTHORIZE_DISPATCH),
        (
            OrchestrationAuthority.EXECUTION_PLANE,
            BoundaryOperation.DISPATCH_AUTHORIZED_INVOCATION,
        ),
        (OrchestrationAuthority.PRODUCER, BoundaryOperation.EXECUTE_ANALYTICAL_TRANSFORMATION),
        (OrchestrationAuthority.REGISTRY, BoundaryOperation.PUBLISH_REGISTRY_SNAPSHOT),
        (OrchestrationAuthority.DURABLE_RESULT, BoundaryOperation.COMMIT_DURABLE_RESULT),
        (OrchestrationAuthority.AUDIT, BoundaryOperation.EVALUATE_AUTHORITATIVE_RECORDS),
        (
            OrchestrationAuthority.BOUNDARY_ACCEPTANCE,
            BoundaryOperation.ACCEPT_OR_REJECT_HANDOFF,
        ),
    ),
)
def test_explicit_authority_scopes_are_separated(
    authority: OrchestrationAuthority,
    operation: BoundaryOperation,
) -> None:
    enforce_authority_scope(authority, operation)


@pytest.mark.parametrize(
    ("authority", "operation"),
    (
        (OrchestrationAuthority.EXECUTION_PLANE, BoundaryOperation.CONSTRUCT_SEMANTIC_PLAN),
        (OrchestrationAuthority.CONTROL_PLANE, BoundaryOperation.COMMIT_DURABLE_RESULT),
        (OrchestrationAuthority.CACHE, BoundaryOperation.COMMIT_DURABLE_RESULT),
        (OrchestrationAuthority.AUDIT, BoundaryOperation.RECORD_INVOCATION_TRANSITION),
        (OrchestrationAuthority.PRODUCER, BoundaryOperation.DISPATCH_AUTHORIZED_INVOCATION),
    ),
)
def test_cross_authority_operations_are_rejected(
    authority: OrchestrationAuthority,
    operation: BoundaryOperation,
) -> None:
    with pytest.raises(OrchestrationBoundaryViolation):
        enforce_authority_scope(authority, operation)


@pytest.mark.parametrize(
    ("authority", "operation"),
    (
        (OrchestrationAuthority.PRODUCER, BoundaryOperation.REGISTER_EVIDENCE),
        (OrchestrationAuthority.CONTROL_PLANE, BoundaryOperation.SELECT_DECISION),
        (OrchestrationAuthority.EXECUTION_PLANE, BoundaryOperation.REGISTER_EVIDENCE),
        (OrchestrationAuthority.EPIP016, BoundaryOperation.ACCEPT_OR_REJECT_HANDOFF),
    ),
)
def test_epip016_boundary_is_protected(
    authority: OrchestrationAuthority,
    operation: BoundaryOperation,
) -> None:
    with pytest.raises(OrchestrationBoundaryViolation):
        enforce_authority_scope(authority, operation)


@pytest.mark.parametrize(
    ("authority", "operation"),
    (
        (OrchestrationAuthority.PRODUCER, BoundaryOperation.RESOLVE_DECLARED_DEPENDENCIES),
        (OrchestrationAuthority.PRODUCER, BoundaryOperation.PUBLISH_REGISTRY_SNAPSHOT),
        (
            OrchestrationAuthority.BOUNDARY_ACCEPTANCE,
            BoundaryOperation.DEFINE_EVIDENCE_COMPLETENESS,
        ),
        (OrchestrationAuthority.AUDIT, BoundaryOperation.COMMIT_DURABLE_RESULT),
    ),
)
def test_prohibited_operations_are_detected(
    authority: OrchestrationAuthority,
    operation: BoundaryOperation,
) -> None:
    with pytest.raises(OrchestrationBoundaryViolation):
        enforce_authority_scope(authority, operation)


@pytest.mark.parametrize(
    ("authority", "operation"),
    (
        ("control_plane", BoundaryOperation.ADMIT_PIPELINE_REQUEST),
        (OrchestrationAuthority.CONTROL_PLANE, "admit_pipeline_request"),
        (object(), object()),
    ),
)
def test_unknown_values_fail_closed(authority: object, operation: object) -> None:
    with pytest.raises(OrchestrationBoundaryViolation):
        enforce_authority_scope(authority, operation)  # type: ignore[arg-type]


def test_handoff_adapter_is_not_an_authority_and_translation_is_not_authorized() -> None:
    assert "handoff_adapter" not in {authority.value for authority in OrchestrationAuthority}
    assert "translate_handoff_representation" not in {
        operation.value for operation in BoundaryOperation
    }


def test_every_boundary_operation_has_exactly_one_constitutional_owner() -> None:
    owners = {
        operation: tuple(
            authority
            for authority, operations in _AUTHORITY_SCOPES.items()
            if operation in operations
        )
        for operation in BoundaryOperation
    }

    assert set(owners) == set(BoundaryOperation)
    assert all(len(authorities) == 1 for authorities in owners.values())


def test_no_composite_a01_artifact_is_exported() -> None:
    from epip import orchestration

    prohibited = {
        "EvidencePipeline",
        "EvidencePlanner",
        "EvidenceExecutionPlan",
        "EvidenceScheduler",
        "EvidenceContext",
        "EvidenceExecutionResult",
    }
    assert prohibited.isdisjoint(orchestration.__all__)
