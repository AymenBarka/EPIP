# ADR-H006 — Exception Taxonomy and Error Boundaries

## Status

Accepted for Hardening-006 Programme B.

## Context

EPIP historically exposes domain-local exception families. Their runtime
behaviour must remain stable, while institutional operation requires a single,
auditable vocabulary for classification and propagation.

## Decision

EPIP defines a canonical, single-parent hierarchy rooted at `EPIPError`.
`ExceptionContract` classifies every canonical type, while
`ExceptionBoundary` describes capture, translation, propagation, wrapping,
logging ownership, visibility, and recovery expectations. The declarations are
held by an immutable `ExceptionRegistry`.

Programme B is descriptive only. Existing exceptions are not re-parented and
no runtime translation, retry, logging, or compensation is activated.

## Consequences

- The hierarchy is deterministic and free of multiple inheritance.
- Public and technical error vocabularies can be distinguished explicitly.
- Missing exceptions and boundaries produce stable audit diagnostics.
- Runtime adoption requires a separately reviewed programme.
