# EPIP-017 Foundational Orchestration Boundary

## Scope

Programme A gate A01-F implements only the system boundary established by
ADR-EPIP017-01. It enforces the separation between the orchestration control
plane, execution plane, producers, state authorities, Boundary Acceptance
Authority, and the EPIP-016 Decision Framework.

## Public infrastructure

- `OrchestrationAuthority` represents only authorities and bounded roles
  jointly governed by ADR-EPIP017-01 and ADR-EPIP017-15 under Programme A
  Blueprint v1.1 section A01-F.
- `BoundaryOperation` represents only responsibilities jointly governed by
  ADR-EPIP017-01 and ADR-EPIP017-15 under Programme A Blueprint v1.1 section
  A01-F.
- `enforce_authority_scope()` accepts an explicit authority/operation pairing
  or rejects it with `OrchestrationBoundaryViolation`.

Validation is allowlist-based and fail-closed. Unknown authorities, unknown
operations, and cross-authority operations are rejected.

## Constitutional boundary

The implementation performs no authorized operation. In particular, it does
not plan, schedule, execute producers, dispatch work, commit results, cache,
replay, recover, migrate, or hand evidence to EPIP-016. It only validates
whether an operation belongs to the authority requesting it.

The EPIP-016 boundary remains protected: producer, execution-plane, control-
plane, audit, and cache authorities cannot exercise EPIP-016 decision
responsibilities. The Boundary Acceptance Authority alone owns atomic handoff
acceptance or rejection; EPIP-016 does not own that boundary operation.

The handoff adapter is not an authority. A01-F grants it no operation.
Representation translation remains outside this implementation because ADR-15
permits it only under separately certified semantic and behavioral equivalence.

## Maturity

This is the A01-F foundational maturity gate. It does not implement or claim
completion of `EvidencePipeline`, `EvidencePlanner`, `EvidenceExecutionPlan`,
`EvidenceScheduler`, `EvidenceContext`, or `EvidenceExecutionResult`.
