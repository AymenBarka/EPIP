# A03 Execution Plan Version 2

| Governance field | Value |
| --- | --- |
| Status | APPROVED |
| Version | 2.0 |
| Approval date | 2026-08-15 |
| Git baseline | `2040e3e` |
| Approved governance amendment | Completion and acceptance governance correction, 2026-08-15 |

## Document Authority

This document is the authoritative implementation roadmap for the remaining A03 work. It is a new
execution plan derived from the frozen architecture and current repository state. It is not a
reconstruction of the unavailable historical A03 Implementation Master Plan.

Architectural authority remains exclusively with ADR-EPIP017-01 through ADR-EPIP017-18 and the
consolidated A03 Architecture Amendment. This plan allocates implementation work without changing
architecture.

## Approved Governance Amendment

The completion and acceptance governance correction approved on 2026-08-15 is normative for this
plan. It changes only completion governance, acceptance governance, and dependency-governance
wording. It does not change architecture, execution-package definitions, component ownership,
execution order, repository allocation, or the public API.

The correction establishes two independent gates:

- a Component Completion Gate for execution-package-local completion;
- an Integrated Acceptance Gate for repository-wide behavioral acceptance.

A package may be component-complete without being accepted. Only an Integrated Acceptance Gate may
authorize a repository baseline, release tag, acceptance declaration, or architectural freeze
point for packages governed by a combined gate.

## Purpose

The plan transforms the implementation at baseline commit `2040e3e` into complete, objectively
demonstrable conformance with the consolidated A03 Architecture Amendment. It provides:

- unique ownership of every remaining implementation obligation;
- deterministic package ordering;
- independently reviewable repository changes;
- one incremental commit boundary per package;
- explicit tests and completion gates;
- final conformance and compatibility evidence.

## Frozen Baseline

The following are frozen inputs:

- ADR-EPIP017-01 through ADR-EPIP017-18;
- A01-F;
- A02;
- A03 Increment 1 through Increment 7;
- the consolidated A03 Architecture Amendment;
- Alternative D;
- the `GovernanceRegistry.apply(action, manifest, epoch)` public operation;
- accepted A03-MP-01 at commit `2040e3e`.

A03-MP-01 established the complete immutable `GovernanceManifest` schema and
`GovernanceFactReference`. No execution package may weaken, reinterpret, or bypass that accepted
boundary.

## Scope

The plan covers only the remaining A03 alignment work in:

- `epip/governance/`;
- `tests/governance/`;
- A03-specific conformance and traceability documentation created by this plan.

It does not authorize changes to ADRs, A01-F, A02, the consolidated A03 Architecture Amendment, or
unrelated repository modules.

## Execution Package Inventory

| Identifier | Name | Status | Primary ownership |
| --- | --- | --- | --- |
| A03-V2-E00 | Frozen model baseline | Complete | Accepted MP-01 model and exports |
| A03-V2-E01 | Governance-semantic validation integration | Pending | Validation layer |
| A03-V2-E02 | Manifest-aware immutable reduction | Pending | Reducer |
| A03-V2-E03 | Candidate snapshot construction and identity | Pending | Snapshot builder |
| A03-V2-E04 | Authoritative snapshot publication | Pending | Store |
| A03-V2-E05 | Ordered governance transition orchestration | Pending | Coordinator |
| A03-V2-E06 | Public registry façade integration | Pending | Registry façade |
| A03-V2-E07 | Complete governance lifecycle verification | Pending | End-to-end integration evidence |
| A03-V2-E08 | Architectural conformance and compatibility closure | Pending | Final evidence and acceptance |

## A03-V2-E00 — Frozen Model Baseline

### Objective

Record the accepted MP-01 implementation as the immutable input boundary for every remaining
execution package. This package is already complete and authorizes no further implementation.

### Repository Components

- `epip/governance/model.py`
- `epip/governance/__init__.py`
- `tests/governance/test_model.py`
- `tests/governance/__init__.py`
- the A03 contribution to `tests/core/test_integrity_compliance.py`

### Architectural Traceability

- Consolidated amendment: `GovernanceManifest`
- Consolidated amendment: `GovernanceFactReference`
- Consolidated amendment: intrinsic manifest validation
- ADR-EPIP017-03
- ADR-EPIP017-09

### Dependencies

None within this plan. The package is the accepted foundation.

### Required Tests

The accepted MP-01 model and integrity tests remain unchanged and passing.

### Completion Criteria

- MP-01 remains accepted.
- Complete manifest and reference schemas remain unchanged.
- All model and integrity tests pass.

### Repository Impact

None. This is a frozen completed package.

## A03-V2-E01 — Governance-Semantic Validation Integration

### Objective

Align the governance validation layer with the complete manifest so it exclusively validates
governance semantics against the exact starting snapshot, selected action, manifest facts, and
epoch. It must return explicit deterministic acceptance or one immutable rejection.

### Repository Components

- `epip/governance/validation.py`
- `tests/governance/test_validation.py`

No other production component may be modified by this package.

### Architectural Traceability

- Consolidated amendment: Validation Architecture
- Consolidated amendment: Governance Validation Layer
- Consolidated amendment: Validation Responsibility Matrix
- Consolidated amendment: Lifecycle-Wide Validation Invariants
- ADR-EPIP017-03
- ADR-EPIP017-08

### Dependencies

- A03-V2-E00

### Required Tests

- admission eligibility and declaration completeness;
- authoritative ownership uniqueness;
- authority authorization, scope, and separation;
- certification profile, scope, version, state, suspension, and revocation;
- compatibility direction, endpoints, approval, and revocation;
- lifecycle and trust transitions;
- revocation authority, scope, duplication, and prior state;
- action-to-fact semantic correspondence;
- current-snapshot and policy consistency;
- explicit acceptance from each applicable validator;
- deterministic rejections for missing, unrelated, or ambiguous facts;
- proof that validators remain stateless, pure, and mutation-free.

### Completion Criteria

- Every semantic validation activity has exactly one validation-layer owner.
- The validation layer performs no supported-action selection, reduction, construction,
  coordination, or publication.
- Identical immutable inputs produce identical validation outcomes.
- All validation tests and the full regression suite pass.

### Repository Impact

Modify the validation module and its existing tests only. Commit independently after acceptance.

## A03-V2-E02 — Manifest-Aware Immutable Reduction

### Objective

Align `_GovernanceReducer` with the frozen validation-to-reduction contract. The reducer must own
supported-action validation, deterministic validator-set selection, validator-completion
confirmation, and exactly one immutable reduction using selected manifest facts.

### Repository Components

- `epip/governance/reduction.py`
- `tests/governance/test_reduction.py`

### Architectural Traceability

- Consolidated amendment: GovernanceReducer
- Consolidated amendment: Validation Responsibility Matrix
- Consolidated amendment: Reduction Semantics
- Consolidated amendment: Authority, History, Validation, and Reduction Invariants
- ADR-EPIP017-03
- ADR-EPIP017-09

### Dependencies

- A03-V2-E00
- A03-V2-E01

### Required Tests

- complete immutable reducer input binding;
- supported-action rejection;
- deterministic complete validator-set selection;
- explicit validator-acceptance completion;
- admission state creation from selected immutable facts;
- certification issuance, suspension, and revocation;
- compatibility approval and revocation;
- lifecycle and trust state transformations;
- preservation of every unaffected entry by canonical value;
- append-only governance history;
- exactly-once selected-fact application;
- no processing of unrelated facts;
- no invented authority, identifiers, facts, or decisions;
- deterministic reduction and fail-closed rejection;
- rejected operations produce no reduction result.

### Completion Criteria

- All frozen supported actions follow one validation and reduction path.
- Reduction begins only after complete explicit acceptance.
- A successful call produces one complete immutable reduction result.
- Input state and unaffected governed state remain unchanged.
- No builder, store, coordinator, registry, persistence, or external behavior is introduced.
- Reducer unit and component tests, local quality gates, package coverage, and repository ownership
  checks pass.
- The resulting status is `COMPONENT COMPLETE — INTEGRATED ACCEPTANCE PENDING`.

### Repository Impact

Modify the reducer and reducer tests only. Commit after Component Completion without declaring the
package accepted or establishing a repository baseline, release tag, or architectural freeze point.

## A03-V2-E03 — Candidate Snapshot Construction and Identity

### Objective

Align `_SnapshotBuilder` with the complete post-reduction input, frozen snapshot schema,
canonicalization rules, and identity participation contract.

### Repository Components

- `epip/governance/snapshot.py`
- `tests/governance/test_snapshot.py`

### Architectural Traceability

- Consolidated amendment: SnapshotBuilder
- Consolidated amendment: Snapshot Construction Semantics
- Consolidated amendment: Identity and Determinism Invariants
- ADR-EPIP017-03
- ADR-EPIP017-08
- ADR-EPIP017-09

### Dependencies

- A03-V2-E00
- A03-V2-E02

### Required Tests

- complete post-reduction entries and history preservation;
- exact frozen snapshot field inventory;
- canonical entry, action-reference, policy, and authority-fact participation;
- deterministic profile-bound identity derivation;
- reproducibility under equivalent input orderings;
- identity changes for identity-participating content changes;
- mismatch and unsupported-profile rejection;
- complete deep immutability;
- no lazy, deferred, or partial candidate;
- absence of governance validation, reduction, or publication.

### Completion Criteria

- One successful reduction admits exactly one complete candidate construction.
- Candidate content preserves the exact post-reduction governance meaning.
- Canonically identical inputs produce identical candidate snapshots and identities.
- No hidden environment state participates.
- Snapshot unit and component tests, local quality gates, package coverage, and repository ownership
  checks pass.
- The resulting status is `COMPONENT COMPLETE — INTEGRATED ACCEPTANCE PENDING`.

### Repository Impact

Modify the snapshot builder and its tests only. Commit after Component Completion without declaring
the package accepted or establishing a repository baseline, release tag, or architectural freeze
point.

## A03-V2-E04 — Authoritative Snapshot Publication

### Objective

Align `GovernanceStore` with the frozen single-authoritative-snapshot and atomic replacement
contract.

### Repository Components

- `epip/governance/store.py`
- `tests/governance/test_store.py`

### Architectural Traceability

- Consolidated amendment: GovernanceStore
- Consolidated amendment: Authoritative Publication Semantics
- Consolidated amendment: Publication Invariants
- ADR-EPIP017-03
- ADR-EPIP017-09

### Dependencies

- A03-V2-E03

### Required Tests

- exactly one authoritative snapshot after initialization;
- atomic candidate replacement;
- previous snapshot visibility before successful replacement;
- candidate visibility only after successful replacement;
- failed replacement preserves the previous authoritative snapshot;
- no transient zero, dual, mixed, mutable, or partial authoritative state;
- exact unchanged candidate publication;
- concurrent read consistency at the replacement boundary;
- absence of validation, reduction, construction, inference, or persistence.

### Completion Criteria

- Every observable read returns exactly one complete immutable authoritative snapshot.
- Replacement is atomic and deterministic.
- Failure produces no authoritative transition and requires no rollback mutation.
- Store unit and component tests, local quality gates, package coverage, and repository ownership
  checks pass.
- The resulting status is `COMPONENT COMPLETE — INTEGRATED ACCEPTANCE PENDING`.

### Repository Impact

Modify the store and store tests only. Commit after Component Completion without declaring the
package accepted or establishing a repository baseline, release tag, or architectural freeze point.

## A03-V2-E05 — Ordered Governance Transition Orchestration

### Objective

Align `_GovernanceCoordinator` with the single frozen sequence from current-state read through
reduction, construction, and one replacement request.

### Repository Components

- `epip/governance/coordinator.py`
- `tests/governance/test_coordinator.py`

### Architectural Traceability

- Consolidated amendment: GovernanceCoordinator
- Consolidated amendment: Complete Governance Lifecycle
- Consolidated amendment: Lifecycle Sequencing and Failure Invariants
- ADR-EPIP017-03
- ADR-EPIP017-09

### Dependencies

- A03-V2-E01
- A03-V2-E02
- A03-V2-E03
- A03-V2-E04

### Required Tests

- exact transfer of starting snapshot, action, manifest, and epoch;
- exactly one reducer invocation;
- no construction after reduction rejection;
- exactly one builder invocation after successful reduction;
- no replacement after construction rejection;
- exactly one replacement request after successful construction;
- immediate unchanged rejection propagation;
- previous authoritative state after every failure boundary;
- identical transition traces for identical inputs and starting state;
- no validation, reduction, construction, identity, retry, or recovery logic in the coordinator.

### Completion Criteria

- The coordinator exposes one and only one architectural transition path.
- No phase is skipped, repeated, reordered, retried, or speculatively executed.
- Failed operations have no partial observable state.
- Coordinator unit and component tests, local quality gates, package coverage, and repository
  ownership checks pass.
- Completion of E05 admits the combined E02–E05 Integrated Acceptance Gate.

### Repository Impact

Modify the coordinator and coordinator tests only. Commit after Component Completion; acceptance,
baselining, tagging, and architectural freeze remain subject to the combined E02–E05 Integrated
Acceptance Gate.

## A03-V2-E06 — Public Registry Façade Integration

### Objective

Align `GovernanceRegistry` with the completed internal workflow while preserving the frozen public
API and façade-only responsibility.

### Repository Components

- `epip/governance/registry.py`
- `tests/governance/test_registry.py`

### Architectural Traceability

- Consolidated amendment: GovernanceRegistry
- Consolidated amendment: Component Responsibility Matrix
- Consolidated amendment: Responsibility Separation Invariants
- ADR-EPIP017-03
- ADR-EPIP017-09

### Dependencies

- A03-V2-E05

### Required Tests

- unchanged `apply(action, manifest, epoch)` signature;
- exactly one coordinator delegation;
- immutable input and output boundaries;
- unchanged immutable rejection propagation;
- read-only authoritative snapshot access;
- deterministic public outcomes from identical state and inputs;
- no alternate governance path;
- absence of validation, reduction, construction, publication transformation, retry, recovery,
  persistence, scheduling, and producer execution.

### Completion Criteria

- Public API compatibility is demonstrated.
- Registry behavior is delegation and read-only observation only.
- No internal responsibility is duplicated or bypassed.
- Registry tests and the full regression suite pass.

### Repository Impact

Modify the registry façade and its tests only. Commit independently after acceptance.

## A03-V2-E07 — Complete Governance Lifecycle Verification

### Objective

Demonstrate the complete public lifecycle for every frozen governance operation without adding
production responsibilities.

### Repository Components

- create `tests/governance/test_lifecycle.py`

Existing production components may not be modified in this package. A defect discovered here must
be returned to the package that uniquely owns the failed responsibility.

### Architectural Traceability

- Consolidated amendment: Complete Governance Lifecycle
- Consolidated amendment: Reduction Semantics
- Consolidated amendment: Authoritative Publication Semantics
- Consolidated amendment: Lifecycle-Wide Architectural Invariants
- ADR-EPIP017-03
- ADR-EPIP017-08
- ADR-EPIP017-09

### Dependencies

- A03-V2-E01 through A03-V2-E06

### Required Tests

- admission creates the authoritative registry entry;
- certification issuance reaches authoritative state;
- certification suspension and revocation preserve history;
- compatibility approval and revocation preserve direction and history;
- lifecycle and trust transitions preserve authority separation;
- successful operations append selected facts exactly once;
- rejected operations append nothing and preserve the authoritative snapshot;
- identical starting state and inputs produce identical terminal state and identity;
- no intermediate reduction or candidate becomes authoritative;
- public workflow uses the single frozen sequence.

### Completion Criteria

- Every frozen operation has one successful and required fail-closed lifecycle scenario.
- All lifecycle-wide invariants have direct integration evidence.
- No production file changes are included.
- Lifecycle tests and the full regression suite pass.

### Repository Impact

Create one integration-test module only. Commit independently after acceptance.

## A03-V2-E08 — Architectural Conformance and Compatibility Closure

### Objective

Produce complete deterministic evidence that the final implementation satisfies every frozen A03
obligation and preserves the compatibility contract.

### Repository Components

- create `tests/governance/test_conformance.py`;
- create `docs/project/A03_CONFORMANCE_MATRIX.md`;
- create `docs/project/A03_COMPATIBILITY_EVIDENCE.md`.

No production component may be modified in this package. Any detected defect returns to its unique
owning execution package.

### Architectural Traceability

- Consolidated amendment: Lifecycle-Wide Architectural Invariants
- Consolidated amendment: Conformance Model
- Consolidated amendment: Compatibility and Evolution Contract
- Consolidated amendment: Repository Traceability
- ADR-EPIP017-03
- ADR-EPIP017-08
- ADR-EPIP017-09
- ADR-EPIP017-16

### Dependencies

- A03-V2-E00 through A03-V2-E07

### Required Tests

- one machine-verifiable obligation inventory;
- exactly one result for every frozen obligation;
- exclusive component responsibility ownership;
- complete lifecycle ordering;
- negative responsibility boundaries;
- immutable representation and state preservation;
- deterministic equivalence and identity reproducibility;
- append-only history and fail-closed behavior;
- frozen public API and representation compatibility;
- deterministic rejection of unsupported future versions;
- unchanged A01-F and A02 boundaries.

### Completion Criteria

- Every frozen obligation is `PASS`; `FAIL` and `NOT DEMONSTRATED` are absent.
- Every compatibility claim has objective evidence.
- Conformance evaluation is deterministic for the same evaluated configuration.
- Documentation traceability matches the implementation and tests.
- All repository quality and documentation gates pass.

### Repository Impact

Create conformance tests and two evidence documents only. Commit independently after acceptance.

## Unique Repository Ownership Matrix

| Repository component | Unique execution owner |
| --- | --- |
| `epip/governance/model.py` | A03-V2-E00 |
| `epip/governance/__init__.py` | A03-V2-E00 |
| `epip/governance/validation.py` | A03-V2-E01 |
| `epip/governance/reduction.py` | A03-V2-E02 |
| `epip/governance/snapshot.py` | A03-V2-E03 |
| `epip/governance/store.py` | A03-V2-E04 |
| `epip/governance/coordinator.py` | A03-V2-E05 |
| `epip/governance/registry.py` | A03-V2-E06 |
| `tests/governance/__init__.py` | A03-V2-E00 |
| `tests/governance/test_model.py` | A03-V2-E00 |
| `tests/governance/test_validation.py` | A03-V2-E01 |
| `tests/governance/test_reduction.py` | A03-V2-E02 |
| `tests/governance/test_snapshot.py` | A03-V2-E03 |
| `tests/governance/test_store.py` | A03-V2-E04 |
| `tests/governance/test_coordinator.py` | A03-V2-E05 |
| `tests/governance/test_registry.py` | A03-V2-E06 |
| `tests/governance/test_lifecycle.py` | A03-V2-E07 |
| `tests/governance/test_conformance.py` | A03-V2-E08 |
| `docs/project/A03_CONFORMANCE_MATRIX.md` | A03-V2-E08 |
| `docs/project/A03_COMPATIBILITY_EVIDENCE.md` | A03-V2-E08 |

The consolidated A03 Architecture Amendment is an immutable input and is not owned for modification
by any package.

## Dependency Graph

```text
A03-V2-E00
    -> A03-V2-E01
        -> A03-V2-E02
            -> Component Completion Gate — E02
                -> A03-V2-E03
                    -> Component Completion Gate — E03
                        -> A03-V2-E04
                            -> Component Completion Gate — E04
                                -> A03-V2-E05
                                    -> Integrated Acceptance Gate — E02 through E05
                                        -> A03-V2-E06
                                            -> A03-V2-E07
                                                -> A03-V2-E08
```

This implementation order is mandatory and unchanged. E03 may begin after E02 Component Completion;
E04 may begin after E03 Component Completion; and E05 may begin after E04 Component Completion. E06
may begin only after successful combined E02–E05 Integrated Acceptance. Component Completion is not
package acceptance and creates no reverse dependency or dependency cycle.

## Commit and Review Policy

Each execution package must produce exactly one independently reviewable commit after its applicable
completion gate. The next package must not begin while the current package has uncommitted or
unpushed changes. An E02–E05 component-completion commit is an implementation checkpoint only; it is
not an accepted repository baseline, release tag, or architectural freeze point.

Recommended commit subjects are:

- `feat(a03): complete V2-E01 governance validation integration`
- `feat(a03): complete V2-E02 immutable reduction integration`
- `feat(a03): complete V2-E03 snapshot construction integration`
- `feat(a03): complete V2-E04 authoritative publication integration`
- `feat(a03): complete V2-E05 governance transition orchestration`
- `feat(a03): complete V2-E06 registry facade integration`
- `test(a03): complete V2-E07 lifecycle verification`
- `test(a03): complete V2-E08 conformance and compatibility closure`

## Component Completion Gate

The Component Completion Gate certifies execution-package-local completion only. It requires:

- execution-package implementation complete;
- execution-package unit and component tests passing;
- execution-package local integration tests passing when allocated;
- Black passing for the allocated scope;
- Ruff passing for the allocated scope;
- MyPy strict passing for the allocated scope;
- package coverage requirements satisfied;
- repository ownership compliance demonstrated.

It does not require repository-wide regression, repository-wide integration, downstream
execution-package integration, or repository-wide acceptance.

Successful E02, E03, and E04 Component Completion produces the status:

```text
COMPONENT COMPLETE — INTEGRATED ACCEPTANCE PENDING
```

A package with this status shall not become a repository baseline, receive a release tag, be
declared accepted, or be used as an architectural freeze point. Only successful Integrated
Acceptance may authorize those repository states.

## Integrated Acceptance Gate

The combined E02–E05 Integrated Acceptance Gate runs only after E02, E03, E04, and E05 have
completed their allocated implementation. It requires:

- all dependent execution packages implemented;
- the complete integration path established;
- repository-wide regression passing;
- repository-wide integration tests passing;
- Black passing;
- Ruff passing;
- MyPy strict passing;
- coverage maintained or improved;
- `git diff --check` passing;
- deterministic lifecycle demonstration;
- no compatibility shim;
- no alternate execution path;
- no responsibility leakage.

Successful completion authorizes acceptance, repository baselining, release tagging, and use as an
architectural freeze point for E02–E05. E06 may begin only after this gate succeeds.

No TODO, placeholder, compatibility shim, speculative API, hidden authority, hidden state, external
lookup, or future-package implementation is permitted.

## Final Repository Acceptance Criteria

A03 execution is complete only when:

- A03-V2-E00 through A03-V2-E08 are accepted;
- every frozen architectural obligation has objective `PASS` evidence;
- every existing and planned A03 repository component has exactly one owner;
- validation, reduction, construction, publication, coordination, and façade responsibilities are
  neither duplicated nor bypassed;
- every frozen governance operation succeeds through the single public workflow;
- every failure preserves the previously authoritative snapshot;
- canonical identity and deterministic outcomes are reproducible;
- compatibility evidence preserves frozen representations, meaning, authority, lifecycle,
  responsibility allocation, sequencing, and failure behavior;
- A01-F and A02 remain unchanged;
- the full repository and documentation quality gates pass;
- the final working tree is clean and all accepted package commits are published.

## Allocation Verification

Every remaining architectural obligation is allocated:

- semantic validation: A03-V2-E01;
- reducer validation ownership and immutable reduction: A03-V2-E02;
- candidate construction and identity: A03-V2-E03;
- authoritative publication: A03-V2-E04;
- transition orchestration: A03-V2-E05;
- public façade: A03-V2-E06;
- lifecycle-wide integration: A03-V2-E07;
- conformance and compatibility closure: A03-V2-E08.

Every existing A03 production module belongs to exactly one package. Cross-package dependencies are
explicit, the execution order is complete, and no remaining implementation surface is unallocated.
