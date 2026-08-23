# A06 Execution Plan

Status: APPROVED
Role: NORMATIVE EXECUTION PLAN
Programme: A06
Derived from: A06 Functional Architecture Specification
Predecessor baseline: A05-v1.0.0

## 1. Sequence and ownership

Execution is strictly sequential: E00 → E01 → E02 → E03 → E04 → E05 → E06 → E07 → E08 → E09. Each unit owns only its production and test files below and may consume only declared immutable predecessor contracts.

| Unit | Production file | Test file | Public outputs |
| --- | --- | --- | --- |
| E00 | `epip/a06/foundation.py` | `tests/a06/test_foundation.py` | `ProjectionRequest`, `ProjectionIdentity`, `ProjectionFoundationDiagnostics` |
| E01 | `epip/a06/authority.py` | `tests/a06/test_authority.py` | `ProjectionAuthority`, `AuthorityValidation`, `AuthorityDiagnostics` |
| E02 | `epip/a06/scope.py` | `tests/a06/test_scope.py` | `ProjectionScope`, `ScopeValidation`, `ScopeDiagnostics` |
| E03 | `epip/a06/planning.py` | `tests/a06/test_planning.py` | `ProjectionPlan`, `PlanValidation`, `PlanDiagnostics` |
| E04 | `epip/a06/eligibility.py` | `tests/a06/test_eligibility.py` | `ProjectionEligibility`, `EligibilityValidation`, `EligibilityDiagnostics` |
| E05 | `epip/a06/compatibility.py` | `tests/a06/test_compatibility.py` | `ProjectionCompatibility`, `CompatibilityValidation`, `CompatibilityDiagnostics` |
| E06 | `epip/a06/projection.py` | `tests/a06/test_projection.py` | `ProjectionResult`, `ProjectionResultValidation`, `ProjectionDiagnostics` |
| E07 | `epip/a06/replay.py` | `tests/a06/test_replay.py` | `ProjectionReplay`, `ReplayValidation`, `ReplayDiagnostics` |
| E08 | `epip/a06/audit.py` | `tests/a06/test_audit.py` | `ProjectionAudit`, `AuditPreparation`, `AuditDiagnostics` |
| E09 | `epip/a06/closure.py` | `tests/a06/test_closure.py` | `IntegratedProjectionClosure`, `ProjectionClosureDiagnostics`, `ProjectionClosureVerifier` |

## 2. Unit contracts

E00 consumes A05 baseline identity and produces the foundation contracts. E01 consumes E00 and A05 authority facts. E02 consumes E00–E01. E03 consumes E00–E02 and A05 closure facts. E04 consumes E00–E03 and A05 temporal/knowledge facts. E05 consumes E00–E04 and A05 closure, mapping, dependency, revision and replay facts. E06 consumes E00–E05 and A05 facts. E07 consumes E00–E06 and A05 replay facts. E08 consumes E00–E07. E09 consumes E00–E08 and produces the sole integrated closure.

Every unit SHALL validate concrete contract shape, identity, authority, temporal compatibility, uniqueness, continuity and immutability as applicable. Missing, malformed, unauthorized, inconsistent, duplicate or ambiguous inputs fail closed. Outputs preserve every consumed immutable fact required for independent reconstruction.

## 3. Forbidden changes

No unit may modify A05, ADRs, this Execution Plan, the Functional Architecture Specification, predecessor packages, successor packages, unrelated files, or another unit's public API. No circular dependency, mutable semantic state, public alias, or responsibility duplication is permitted.

## 4. Quality gates

Each unit requires Black, Ruff, MyPy `--strict`, component tests, full regression, `git diff --check`, 100% statement coverage and 100% branch coverage for owned production code. Quality and CodeQL workflows must pass before closure.

## 5. Review and closure

Implementation review, corrective review, delivery review and post-publication verification are mandatory. A unit is COMPLETE only when all functional and quality gates pass. It is CLOSED only after an atomic commit containing exactly its authorized files is pushed to `origin/develop`, workflows pass, and the working tree is verified.

## 6. Git and release strategy

A06 starts from frozen tag `A05-v1.0.0` on `develop`. Use one atomic commit per unit and explicit package-scoped messages. Do not rewrite history or force-push. Create an A06 release tag only after E00–E09 are CLOSED and final repository verification passes.

## 7. Deliverables and acceptance

Deliverables are the two normative documents, E00–E09 production and tests, review and corrective evidence, delivery commits, workflow evidence, coverage evidence, closure report and final release tag. A06 is COMPLETE only when every unit is CLOSED, all contracts and boundaries are satisfied, the repository is clean and synchronized, and final Quality and CodeQL workflows pass.

## 8. Traceability

## 9. E06 corrective contract

E06 owns immutable projection-result composition and complete predecessor lineage preservation. It consumes the public immutable contracts from E00–E05 and produces only `ProjectionResult`, `ProjectionResultValidation` and `ProjectionDiagnostics` in `epip/a06/projection.py`, with tests in `tests/a06/test_projection.py`.

Complete lineage is the exact authoritative E00–E05 predecessor fact set, physically embedded in `ProjectionResult`. The set is complete, unique, canonical, immutable, hashable and independently reconstructable from `ProjectionResult` alone. Caller-provided labels are not authoritative. E06 SHALL preserve `ProjectionIdentity.identity`, `baseline_tag`, `authority_identity`, all consumed request/authority/scope/plan/eligibility/compatibility facts, and required temporal/replay references.

E06 fails closed on missing, incomplete, malformed, duplicate, unknown, forged, inconsistent or contradictory predecessor facts, including identity, baseline, temporal-basis, scope, plan, eligibility and compatibility mismatches. E07 consumes only the frozen public E06 result and explicitly authorized A05 replay contracts; it may not access private E06 state or recompute E00–E06 semantics.

Foundation→E00; authority→E01; scope→E02; planning→E03; eligibility→E04; compatibility→E05; projection→E06; replay→E07; audit→E08; integrated closure→E09. Each responsibility appears exactly once.
