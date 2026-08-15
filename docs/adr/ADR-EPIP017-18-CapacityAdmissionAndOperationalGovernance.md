# ADR-EPIP017-18 — Capacity, Admission and Operational Governance

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-17 are approved, frozen, and normative. This ADR completes only
the capacity and operational-governance
responsibilities expressly deferred by ADR-01 through ADR-11. It creates no execution concept,
scheduling concept, identity domain, replay mode, authority type, lifecycle model, semantic model,
plan, producer category, or Decision concept.

**Deferred from:** ADR-01, `ADR Dependencies`; ADR-02 through ADR-11, `ADR Dependencies`.

**Completion rationale:** those sections require a mandatory future capacity and operational-
governance ADR before constitutional closure.

## Executive Summary

EPIP-017 already assigns operational readiness and capacity to the Operational Authority, resource
strategy to the Dispatch Plan, execution admission to frozen authorities, failure disposition to
ADR-13, parallel equivalence to ADR-14, and retention to ADR-10. This ADR completes the deferred
rules requiring all graph expansion, timeframe expansion, execution, lease, storage, cache,
archive, replay, certification, and benchmark activity to operate within explicit immutable bounds.

Capacity never changes semantic intent, trust, Evidence meaning, authority, or handoff eligibility.
Insufficient capacity causes an existing wait, rejection, expiration, cancellation, failure,
Retry, Recovery, or Replanning disposition under its competent frozen authority; it creates no new
disposition. Production, replay, migration, and certification retain their existing identities and
authority isolation.

**Deferred from:** ADR-02 through ADR-11, `ADR Dependencies`; ADR-03 `Operational Authority`;
ADR-06 `Operational Context` and `Scheduling Context`.

**Completion rationale:** this supplies only the bounds, admission, isolation, and operational
clock governance expressly deferred by those clauses.

## Purpose

The purpose is to close the mandatory capacity/operational-governance dependency for resource
profiles, admission budgets, graph limits, timeframe expansion, operational readiness, leases,
execution bounds, storage, cache, archive, replay isolation, and benchmark governance.

**Deferred from:** ADR-02 through ADR-11, `ADR Dependencies`.

**Completion rationale:** every listed responsibility appears verbatim or substantively in those
deferrals.

## Problem Statement

The frozen corpus requires finite graphs, bounded temporal expansion, deterministic admission,
isolated replay, governed leases, cache and storage limits, and operational readiness without
semantic privilege escalation. It intentionally leaves their common constitutional governance to
this ADR. Without completion, implementation would decide which existing authority facts and
failure dispositions apply under exhaustion.

**Deferred from:** ADR-02, ADR-03, ADR-04, ADR-05, ADR-06, ADR-07, ADR-08, ADR-10, and ADR-11
`ADR Dependencies`.

**Completion rationale:** the problem is exactly the deferred governance gap; no scheduler or
resource mechanism is introduced.

## Architectural Context

ADR-02 declares producer resource profiles. ADR-03 assigns operational readiness, capacity, and
availability to Operational Authority. ADR-04 requires finite bounded dependency graphs. ADR-05
governs timeframe expansion and historical retention obligations. ADR-06 places immutable
resource classes, plan limits, Dispatch admission, fairness, priority, and operational facts in
Dispatch, Operational, and Scheduling Context. ADR-07 governs leases, execution admission and
operational clock facts. ADR-08 governs environment profiles, operational clocks and benchmarks.
ADR-09 provides existing resource, environment, and operational-policy identity. ADR-10 governs
storage, cache, archive, legal hold and destruction. ADR-11 requires replay resource isolation and
bounded historical scope. ADR-13 and ADR-14 govern failure and concurrency consequences.

**Deferred from:** ADR-02 through ADR-11, `ADR Dependencies`.

**Completion rationale:** this section locates existing responsibility and does not move it.

## Definitions

The following terms retain or compose existing meanings:

- **Resource Profile** is the immutable producer, execution, storage, replay, or environment
  resource declaration already required by ADR-02, ADR-06, ADR-08, and ADR-09.
- **Admission Budget** is the explicit bound against which an existing admission authority
  evaluates work; it grants no authority by itself.
- **Graph Limit** is the finite node, edge, depth, fan-out, and resolution bound deferred by
  ADR-04 and ADR-06.
- **Timeframe Expansion Limit** is the bound on temporal dependency expansion deferred by ADR-05.
- **Operational Readiness** retains ADR-03 meaning and is distinct from registration, trust,
  certification, compatibility, and semantic eligibility.
- **Operational Clock** is the governed clock fact required by ADR-07 and ADR-08 for leases,
  windows, timeout policy, and operational validity; it is not ADR-05 semantic time.
- **Capacity Isolation** is application of existing authority and context isolation so one scope's
  resource use does not grant or alter another scope's authority.
- **Benchmark Observation** retains ADR-08 meaning as observational performance evidence that does
  not weaken semantic equivalence.

No term creates a new identity domain, authority, scheduling mechanism, or lifecycle.

**Deferred from:** ADR-02 through ADR-11, `ADR Dependencies`; ADR-03 `Operational Authority`;
ADR-06 `Execution Context`; ADR-08 `Benchmark Governance`.

**Completion rationale:** definitions name only the objects and bounds already deferred.

## Normative Rules

The following rules are the complete normative contribution of ADR-18:

- **CAP-01:** Every admitted producer, plan, graph, execution, storage, cache, replay, migration,
  certification, and benchmark scope MUST reference the applicable immutable resource,
  environment, and operational-policy identities already required by ADR-02, ADR-06, ADR-08, and
  ADR-09.
- **CAP-02:** Dependency resolution MUST enforce explicit finite node, edge, depth, fan-out, and
  resolution-budget limits before Semantic Plan acceptance.
- **CAP-03:** Cross-timeframe and historical expansion MUST enforce explicit bounded timeframe,
  interval, calendar, revision, and retained-history scope before Semantic Plan acceptance.
- **CAP-04:** Operational admission MUST verify applicable resource class, budget, readiness,
  authority, plan limits, execution scope, and isolation before authorizing existing Dispatch,
  Invocation, Attempt, replay, migration, or certification activity.
- **CAP-05:** Capacity, readiness, health, placement, queue, priority, fairness, circuit, or
  benchmark facts MUST NOT change Evidence semantics, producer selection semantics, temporal
  meaning, trust, certification, compatibility, Semantic Plan identity, Commit authority, or
  handoff eligibility.
- **CAP-06:** Capacity insufficiency or limit exhaustion MUST use an existing wait, rejection,
  expiration, cancellation, failure, Retry, Recovery, operational replan, or semantic Replanning
  path under ADR-06, ADR-07, and ADR-13 and MUST NOT create an implicit fallback or degraded
  semantic contract.
- **CAP-07:** Operational clocks used for leases, fences, execution validity, windows, timeout
  policy, and admission MUST be explicitly identified, governed by ADR-08 profiles, and kept
  distinct from ADR-05 Historical Time, Knowledge Time, and semantic temporal authority.
- **CAP-08:** Resource limits, fairness, priority, and backpressure constraints MUST be represented
  only through existing Dispatch Plan, Operational Context, Scheduling Context, lifecycle, and
  failure contracts and MUST NOT become producer analytical input.
- **CAP-09:** Parallel and speculative admission MUST remain within the immutable Execution Group,
  Window, isolation, authority, and equivalence bounds of ADR-14; capacity availability MUST NOT
  prove independence or select a Commit winner.
- **CAP-10:** Retry and Recovery resource admission MUST preserve ADR-13 eligibility, limits,
  lineage, new-Attempt authority, and deterministic disposition; additional capacity MUST NOT
  increase retry authority implicitly.
- **CAP-11:** Production, Replay Sessions, migration shadow execution, and certification campaigns
  MUST retain separate existing identity, authority, ledger, cache, result, and handoff scopes when
  sharing finite resources.
- **CAP-12:** Replay historical scope and archive use MUST be explicitly bounded and MUST NOT alter
  source retention, production availability, cache authority, original facts, or Replay Mode.
- **CAP-13:** Storage, cache, archive, legal-hold, and destruction capacity decisions MUST preserve
  ADR-10 durable authority, invalidation, retention, lineage, replay, audit, certification, and
  tombstone obligations; capacity pressure MUST NOT authorize deletion.
- **CAP-14:** Cache admission, eviction, warming, and replacement observations MUST remain
  operational and MUST NOT change Durable Result identity, semantic reuse eligibility, or
  historical interpretation.
- **CAP-15:** Benchmark resource and environment facts MUST remain observational under ADR-08 and
  MUST NOT weaken a determinism profile, equivalence relation, certification verdict, or
  production admission rule.
- **CAP-16:** Identical admitted plans, resource and environment profiles, operational policies,
  budgets, authority facts, and logical clock boundaries MUST produce the same admission,
  exhaustion, and disposition verdicts required by ADR-08.
- **CAP-17:** Capacity and admission decisions, limit exhaustion, isolation violation, clock
  mismatch, archive unavailability, and budget inconsistency MUST produce existing typed
  diagnostics and append-only audit facts under ADR-07, ADR-08, ADR-10, ADR-11, ADR-13, ADR-14,
  and ADR-17.
- **CAP-18:** Capacity, admission, operational-clock, resource-isolation, graph-bound,
  timeframe-bound, storage-bound, replay-bound, and benchmark conformance MUST be included in the
  existing institutional Certification Profile and verdict.
- **CAP-19:** No resource optimization or operational policy MAY weaken a frozen semantic,
  temporal, authority, lifecycle, identity, determinism, replay, migration, retention, or EPIP-016
  boundary.

### Normative Rule Traceability

| Rule | Originating ADR | Section | Deferred responsibility | Satisfied by |
| --- | --- | --- | --- | --- |
| CAP-01 | ADR-02, ADR-06, ADR-08, ADR-09 | `ADR Dependencies` | Resource, environment, and operational-policy profiles and identities | Required immutable profile references |
| CAP-02 | ADR-04, ADR-06 | `ADR Dependencies` | Finite graph, fan-out, depth, resolution budgets, plan limits | Pre-plan graph bounds |
| CAP-03 | ADR-05, ADR-06 | `ADR Dependencies` | Bounded timeframe expansion and graph expansion | Pre-plan temporal bounds |
| CAP-04 | ADR-02, ADR-03, ADR-06, ADR-07 | `ADR Dependencies`; `Operational Authority` | Admission budgets, readiness, Dispatch and execution admission | Existing-authority admission predicates |
| CAP-05 | ADR-03, ADR-06, ADR-08 | `Operational Authority`; `Execution Context`; `ADR Dependencies` | Readiness without semantic privilege escalation | Operational/semantic separation |
| CAP-06 | ADR-02, ADR-06, ADR-07 | `ADR Dependencies` | Operational availability, admission, resource bounds | Existing disposition only |
| CAP-07 | ADR-05, ADR-07, ADR-08 | `ADR Dependencies` | Authoritative operational clocks distinct from semantic time | Profile-bound clock rule |
| CAP-08 | ADR-06 | `Execution Context`; `ADR Dependencies` | Resource classes, fairness, backpressure, scheduling isolation | Existing context and plan representation |
| CAP-09 | ADR-06, ADR-14 | `ADR Dependencies`; `Parallel Execution Model` | Parallel safety, fairness, bounded execution | Existing concurrency bounds |
| CAP-10 | ADR-07, ADR-13 | `ADR Dependencies`; `Retry Model`; `Recovery Model` | Lease policy, execution admission, bounded Retry and Recovery | Existing eligibility and lineage preservation |
| CAP-11 | ADR-03, ADR-08, ADR-11, ADR-16 | `ADR Dependencies`; `Replay Isolation`; `Legacy Isolation` | Operational isolation among production, replay and migration | Existing scope isolation |
| CAP-12 | ADR-05, ADR-10, ADR-11 | `ADR Dependencies` | Bounded historical scope, archive availability, retention | Replay/archive boundary |
| CAP-13 | ADR-05, ADR-07, ADR-10, ADR-11 | `ADR Dependencies`; `Retention Model` | Storage capacity, archival service, legal hold, historical retention | Preservation precedence over capacity |
| CAP-14 | ADR-10 | `Cache Model`; `ADR Dependencies` | Cache budgets and admission behavior | Cache non-authority rule |
| CAP-15 | ADR-08 | `ADR Dependencies`; `Benchmark Governance` | Environment classes, resource profiles, benchmark governance | Observational benchmark boundary |
| CAP-16 | ADR-08, ADR-09 | `Determinism`; `ADR Dependencies` | Operational-policy identity and deterministic admission | Equivalent verdict requirement |
| CAP-17 | ADR-07, ADR-08, ADR-10, ADR-11 | `Diagnostics`; `Audit`; `ADR Dependencies` | Operational, storage, replay and clock audit evidence | Existing diagnostics and audit composition |
| CAP-18 | ADR-03, ADR-08 | `Certification Authority`; `Certification Profiles` | Operational readiness and profile certification | Existing institutional profile inclusion |
| CAP-19 | ADR-01; ADR-02 through ADR-11 | `System Invariants`; `ADR Dependencies` | Constitutional non-expansion | Preservation of frozen boundaries |

No normative rule is orphaned.

## Authorities

The existing Operational Authority from ADR-03 owns readiness, capacity, availability, and
incident-response facts. Existing Semantic Planning, Dispatch, Scheduler, Invocation, Lease,
Fence, Token, Commit, Cache, Retention, Replay, Migration, and Certification Authorities retain
their frozen scopes. Capacity facts constrain their existing admission predicates but do not
transfer authority.

No Capacity Authority, Admission Authority, Budget Authority, Resource Authority, Clock Authority,
or other new authority type is created.

**Deferred from:** ADR-03, ADR-06, ADR-07, ADR-08, ADR-10, and ADR-11 `ADR Dependencies`.

**Completion rationale:** the earlier ADRs assign authority and defer only its common capacity
constraints. Normative behavior is exhausted by CAP-04 through CAP-19.

## Responsibilities

Operational Authority supplies governed readiness and capacity facts. Planning authorities enforce
semantic graph and temporal bounds. Dispatch and scheduler authorities apply existing operational
constraints. Execution authorities enforce Attempt and lease admission. Cache and Retention
Authorities preserve storage boundaries. Replay, Migration, and Certification Authorities preserve
their existing isolation. No responsibility changes semantic intent.

**Deferred from:** ADR-03 through ADR-11 `ADR Dependencies`.

**Completion rationale:** the section maps existing authorities to CAP-01 through CAP-19 and adds
none.

## Lifecycle

ADR-18 creates no lifecycle. Capacity evaluation occurs within existing plan acceptance, Dispatch,
Invocation, Attempt, lease, Window, Replay Session, migration, retention, failure, Retry, Recovery,
and certification lifecycles. Exhaustion uses only the dispositions enumerated by those lifecycles.

**Deferred from:** ADR-06, ADR-07, ADR-10, and ADR-11 `ADR Dependencies`; ADR-13 `Failure
Disposition Model`; ADR-14 `Execution Windows`.

**Completion rationale:** the deferral requires operational governance, not a capacity state
machine. CAP-04, CAP-06 through CAP-10, and CAP-17 provide complete integration.

## Invariants

The constitutional invariants are consequences of CAP-02 through CAP-19: every expansion is
bounded; admission precedes authority; operational facts never change semantics; clock domains
remain distinct; capacity pressure never authorizes deletion, fallback, Commit, or handoff; and
identical governed facts produce equivalent verdicts.

**Deferred from:** ADR-02 through ADR-11 `ADR Dependencies`.

**Completion rationale:** these restate traced rules and introduce no invariant beyond the deferred
scope.

## Diagnostics

Existing diagnostics distinguish graph-limit, fan-out, depth, timeframe-expansion, admission,
readiness, budget, resource-profile, environment-profile, operational-clock, lease-policy,
isolation, storage-capacity, cache-budget, archive-availability, replay-scope, and benchmark-profile
violations. CAP-17 governs their attribution and audit; ADR-13 governs disposition.

**Deferred from:** ADR-02 through ADR-11 `ADR Dependencies` and their existing `Diagnostics`
sections.

**Completion rationale:** only diagnostic categories named by deferred responsibilities are
composed; no new disposition is added.

## Audit

Capacity and admission audit uses existing Execution Ledger, Replay Ledger, migration, storage,
retention, diagnostic, and governance records. CAP-01, CAP-04, CAP-07, CAP-11 through CAP-18 define
the required preserved facts. ADR-17 governs cross-domain retention and redaction.

**Deferred from:** ADR-07, ADR-08, ADR-10, and ADR-11 `ADR Dependencies`.

**Completion rationale:** this closes deferred operational audit evidence without introducing a
ledger.

## Determinism

CAP-07, CAP-15, and CAP-16 apply ADR-08 operational clock, environment, benchmark, and equivalence
profiles. Physical resource timing, queue order, worker discovery, and host placement remain
non-semantic under CAP-05 and CAP-19.

**Deferred from:** ADR-07 and ADR-08 `ADR Dependencies`.

**Completion rationale:** no new determinism profile or equivalence relation is created.

## Replay Compatibility

CAP-11 and CAP-12 preserve ADR-11 Replay Modes, Replay Authority, isolation, historical bounds,
archive use, and non-authoritative output. Capacity decisions are replayed as original operational
facts under CAP-16 and never recalculated from current resource availability.

**Deferred from:** ADR-08 and ADR-11 `ADR Dependencies`.

**Completion rationale:** this satisfies replay resource isolation and bounded historical scope
without defining a replay mode.

## Migration Considerations

Migration and shadow activity use ADR-16 epochs, identities, authority, isolation, rollback, and
retirement. CAP-01, CAP-04 through CAP-06, CAP-11, CAP-16, and CAP-17 make their capacity admission
explicit without changing the migration model.

**Deferred from:** ADR-03, ADR-08 through ADR-11 `Migration` and `ADR Dependencies`; ADR-16
`Migration Model`.

**Completion rationale:** the section applies existing isolation to deferred resource governance.

## Backward Compatibility

EPIP-016 and ADR-01 through ADR-17 remain unchanged. Legacy and target resource behavior remains
separate under ADR-16. Capacity policy cannot alter EPIP-016 Evidence, Decision behavior, public
APIs, or handoff membership.

**Deferred from:** ADR-02 through ADR-11 `Backward Compatibility` and `ADR Dependencies`.

**Completion rationale:** CAP-05, CAP-11, and CAP-19 preserve existing behavior.

## Alternatives Considered

Treating capacity as implementation detail was rejected because ADR-01 through ADR-11 explicitly
defer a mandatory operational-governance ADR. Creating schedulers, queues, algorithms, new
authorities, or new lifecycles was rejected by the completion mandate. A traced governance layer
over existing bounds, contexts, authorities, and dispositions was selected.

**Deferred from:** ADR-01 and ADR-02 through ADR-11 `ADR Dependencies`.

**Completion rationale:** alternatives concern only the form of constitutional closure.

## Decision

ADR-18 adopts CAP-01 through CAP-19 as the complete capacity, admission, and operational-governance
rules deferred by the frozen corpus. All source semantics, plans, execution, authority, identity,
replay, storage, migration, and EPIP-016 contracts remain unchanged.

**Deferred from:** ADR-01 and ADR-02 through ADR-11 `ADR Dependencies`.

**Completion rationale:** every adopted rule appears in the traceability table; no orphan rule is
accepted.

## Consequences

The deferred operational domains now have explicit boundedness, admission, isolation, clock,
storage, replay, and benchmark governance. The cost is stricter rejection and certification when
bounds or profiles are absent. No algorithm, deployment model, or performance target is selected.

**Deferred from:** ADR-02 through ADR-11 `ADR Dependencies`.

**Completion rationale:** consequences follow directly from CAP-01 through CAP-19.

## Future Evolution

Future change is limited by CAP-19 and ADR-16. This ADR introduces no future architectural work.
Operational implementations may vary only within existing profiles, authorities, and equivalence
rules and cannot create a new scheduler concept, authority, identity domain, or lifecycle without a
separate constitutional decision.

**Deferred from:** ADR-01 and ADR-16 `Future Evolution`.

**Completion rationale:** this rejects expansion and preserves existing evolution governance.

## Approval Gate

Approval closes only the mandatory capacity/operational-governance dependency. Together with
approved ADR-17 and the amended ADR-16 closure statement, it completes the eighteen-ADR corpus for
final independent review. It authorizes no implementation or Programme A.

**Deferred from:** ADR-01 `ADR Dependencies` and `Approval Gate`; ADR-16 `Approval Gate`.

**Completion rationale:** this applies the already-established constitutional gate and introduces
no new authorization standard.
