"""EPIP-017 A01-F foundational orchestration boundary.

Traceability: ADR-EPIP017-01 and ADR-EPIP017-15; Programme A Blueprint
v1.1, gate A01-F.
This package exposes boundary enforcement only.  It does not implement any
composite A01 artifact or any downstream work package.
"""

from epip.orchestration.boundary import (
    BoundaryOperation,
    OrchestrationAuthority,
    OrchestrationBoundaryViolation,
    enforce_authority_scope,
)

__all__ = [
    "BoundaryOperation",
    "OrchestrationAuthority",
    "OrchestrationBoundaryViolation",
    "enforce_authority_scope",
]
