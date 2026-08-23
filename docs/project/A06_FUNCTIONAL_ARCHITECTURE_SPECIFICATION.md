# A06 Functional Architecture Specification

Status: APPROVED
Role: NORMATIVE
Programme: A06
Predecessor baseline: A05-v1.0.0

## 1. Objectives

A06 adds a deterministic projection layer above the frozen A05 temporal baseline. It consumes immutable A05 facts, validates authority, scope, timing and compatibility, and produces immutable projection results, replay evidence, audit evidence and integrated closure without modifying or reinterpreting A05.

## 2. Domain concepts

| Concept | Owner | Immutable content |
|---|---|---|
| ProjectionRequest | E00 | request identity, target scope, temporal basis, mode, policy version |
| ProjectionIdentity | E00 | projection identity, A05 baseline tag, authority identity |
| ProjectionAuthority | E01 | authority identity, governance epoch, permitted scope, policy and validity |
| ProjectionScope | E02 | target artifacts and temporal dimensions |
| ProjectionPlan | E03 | deterministic ordered derivation plan |
| ProjectionEligibility | E04 | provisional temporal and knowledge-boundary eligibility |
| ProjectionCompatibility | E05 | compatibility with A05 and the plan |
| ProjectionResult | E06 | immutable derived result and complete lineage |
| ProjectionReplay | E07 | replay inputs, mode and lineage |
| ProjectionAudit | E08 | complete immutable audit evidence |
| IntegratedProjectionClosure | E09 | complete reconstructable A06 closure |

All concepts are immutable, hashable, canonically ordered and independently reconstructable. Invalid, missing, ambiguous, malformed or contradictory facts fail closed.

## 3. Package allocation

| Package | Owns | Consumes | Produces | Forbidden |
|---|---|---|---|---|
| E00 | foundation identity and request facts | A05 baseline identity | `ProjectionRequest`, `ProjectionIdentity`, `ProjectionFoundationDiagnostics` | authority, scope, planning, execution, replay, audit, closure |
| E01 | authority validation | E00 and A05 authority facts | `ProjectionAuthority`, `AuthorityValidation`, `AuthorityDiagnostics` | scope, planning, eligibility, execution |
| E02 | scope definition and validation | E00, E01 | `ProjectionScope`, `ScopeValidation`, `ScopeDiagnostics` | authority, planning, eligibility, execution |
| E03 | deterministic planning | E00–E02 and A05 closure facts | `ProjectionPlan`, `PlanValidation`, `PlanDiagnostics` | final eligibility, compatibility, execution |
| E04 | provisional temporal and knowledge eligibility | E00–E03 and A05 temporal facts | `ProjectionEligibility`, `EligibilityValidation`, `EligibilityDiagnostics` | compatibility, execution, closure |
| E05 | A05 and plan compatibility | E00–E04 and A05 closure/mapping/dependency/revision/replay facts | `ProjectionCompatibility`, `CompatibilityValidation`, `CompatibilityDiagnostics` | execution, audit, closure |
| E06 | immutable projection result | E00–E05 and A05 facts | `ProjectionResult`, `ProjectionResultValidation`, `ProjectionDiagnostics` | authority issuance, mutation, audit closure |
| E07 | deterministic replay | E00–E06 and A05 replay facts | `ProjectionReplay`, `ReplayValidation`, `ReplayDiagnostics` | mutable state, reinterpretation, closure |
| E08 | audit preparation | E00–E07 | `ProjectionAudit`, `AuditPreparation`, `AuditDiagnostics` | approval, result changes, closure |
| E09 | integrated closure | E00–E08 | `IntegratedProjectionClosure`, `ProjectionClosureDiagnostics`, `ProjectionClosureVerifier` | new decisions, mutation, lifecycle behaviour |

## 4. Contract invariants

Every contract SHALL preserve identity, authority context, temporal basis, lineage and all facts consumed by its validator. Equivalent unordered inputs SHALL produce identical ordering, equality, hashing and diagnostics. Caller summaries SHALL NOT override authoritative predecessor facts. Each diagnostic SHALL be attributable to exactly one evaluated immutable output. No package may mutate or duplicate predecessor semantics.

## 5. Public API

Each package exposes only the production types listed in the allocation table. Helpers, aliases, predecessor models and utility symbols are not public API.

## 6. Acceptance and traceability

A package is complete only when its declared responsibilities, contracts, diagnostics, immutable outputs, fail-closed rules, tests and quality gates pass. Each responsibility in the allocation table is owned exactly once. E09 closure requires complete E00–E08 outputs and independent reconstruction.

## 7. Authority precedence

Approved ADRs and architectural constraints supersede this specification; this specification supersedes the A06 Execution Plan; the Execution Plan supersedes closed predecessor contracts; implementations must conform to all of them.

## 8. E06 lineage and reconstruction clarification

Complete lineage is the canonical immutable preservation of the complete E00–E05 predecessor contract facts consumed by E06. The required set is exactly E00, E01, E02, E03, E04 and E05; unknown, missing, duplicate, forged or contradictory entries fail closed. Caller-supplied free-form labels are not authoritative.

The preservation model is physical embedding: every immutable fact required to reconstruct the E06 evaluation is stored in `ProjectionResult`. Reconstruction is offline and deterministic from `ProjectionResult` alone; no external mutable store, network lookup, digest algorithm or additional public lineage type is required. Equality and hashing include all preserved facts.

`ProjectionIdentity` is the canonical A06 identity carrier. E06 SHALL preserve its `identity`, `baseline_tag` and `authority_identity`, together with all consumed request, authority, scope, plan, eligibility, compatibility, temporal and replay facts required for reconstruction. A05 remains predecessor-owned and is never reinterpreted.

E07 consumes only the frozen public E06 result and its preserved facts plus explicitly authorized A05 replay contracts. E07 MUST NOT access private E06 state, invent lineage, repair missing facts or recompute predecessor semantics. E08 and E09 may use these facts for attribution and closure continuity without acquiring predecessor ownership.
