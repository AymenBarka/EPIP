# ADR-EPIP017-17 — Observability, Audit, Retention and Redaction Governance

## Status

Approved and frozen.

ADR-EPIP017-01 through ADR-EPIP017-16 are frozen and normative. This ADR completes only the
observability and audit responsibilities expressly deferred by ADR-01 through ADR-11. It creates
no execution concept, identity domain, replay mode, authority type, lifecycle model, semantic
model, plan, producer category, or Decision concept.

**Deferred from:** ADR-01, `ADR Dependencies`; ADR-02 through ADR-11, `ADR Dependencies`; ADR-02,
`Observability Rules`.

**Completion rationale:** those sections require a mandatory future observability and audit ADR
before constitutional closure. This document supplies that ADR without altering their contracts.

## Executive Summary

EPIP-017 already defines the facts that each domain records, the identities that bind them, and the
Audit, Retention, Certification, and domain authorities that govern them. This ADR completes the
deferred cross-domain rules for separating telemetry from authority, preserving causal audit
records, governing retention and redaction, and retaining evidence required by diagnostics,
replay, migration, and certification.

No observation becomes Evidence, execution input, lifecycle authority, or Decision input merely
because it is collected. Audit remains append-only. Redaction produces a governed projection and
never mutates the authoritative source. Retention honors the strongest applicable frozen
obligation. Existing identities and lifecycles remain controlling.

**Deferred from:** ADR-02 `Observability Rules`; ADR-03, ADR-07, ADR-08, ADR-09, ADR-10, and ADR-11
`ADR Dependencies`.

**Completion rationale:** the source ADRs define domain observations and audit facts but defer
their cross-domain separation, retention, redaction, attestation, and visibility governance.

## Purpose

The purpose is to close the mandatory observability/audit dependency by composing existing domain
rules into one constitutional contract. The scope is telemetry, trace, diagnostic, Audit Record,
retention, audience, exporter, redaction, attestation, chain of custody, and replay preservation.

**Deferred from:** ADR-02 through ADR-11, `ADR Dependencies`.

**Completion rationale:** every listed term appears in those deferrals; no additional purpose is
introduced.

## Problem Statement

The frozen ADRs prohibit telemetry from becoming semantic or operational authority, require
append-only audit, and require retained evidence for replay and certification. They intentionally
defer the common rules that prevent different domains from applying incompatible retention,
redaction, audience, causal-order, or projection behavior.

**Deferred from:** ADR-02 `Observability Rules`; ADR-03 `Audit`; ADR-07 `Audit`; ADR-08 `Audit`;
ADR-10 `Retention Model`; ADR-11 `Replay Audit`.

**Completion rationale:** this is the exact composition problem named by the deferred audit ADR;
it does not establish a new operational problem.

## Architectural Context

ADR-02 defines producer observations and prohibits hidden inputs. ADR-03 defines Audit Authority,
governance attestation, and separation of duties. ADR-04 and ADR-05 define semantic and temporal
diagnostics. ADR-06 separates Semantic, Dispatch, Execution, and Diagnostic Context. ADR-07 defines
the append-only Execution Ledger. ADR-08 separates permitted variability and authoritative facts.
ADR-09 defines Audit Record, telemetry projection, attestation, and Diagnostic Report identity
requirements. ADR-10 defines Retention Authority, archival, legal hold, destruction, cache
diagnostics, and quarantine. ADR-11 defines the Replay Ledger and replay isolation.

**Deferred from:** ADR-02 through ADR-11, `ADR Dependencies`.

**Completion rationale:** this section only locates existing ownership; it reallocates none.

## Definitions

The following terms retain their earlier meanings:

- **Telemetry** is an observational projection emitted under ADR-02, ADR-06, ADR-08, and ADR-09.
- **Execution Trace** is the causally attributable execution observation required by ADR-02,
  ADR-07, ADR-08, and ADR-11; it is not the Execution Ledger.
- **Diagnostic Report** is the existing ADR-09 identity domain for non-authoritative findings.
- **Audit Record** is the audit identity explicitly deferred by ADR-09 and composed from frozen
  domain audit facts.
- **Attestation** is an attributable assertion governed by ADR-03 and bound by ADR-09 identity and
  digest rules.
- **Chain of Custody** is the preserved identity, authority, lineage, integrity, access, and
  transformation history deferred by ADR-03.
- **Redaction** is a governed visibility projection that preserves source identity and lineage; it
  is not source mutation.
- **Retention** is preservation under ADR-10 authority and every domain-specific replay, audit,
  certification, legal-hold, and historical obligation.
- **Audience** and **Exporter** retain the meanings deferred by ADR-02: permitted consumers and
  governed projection boundaries.

No term creates a new identity domain or authority.

**Deferred from:** ADR-02 `Observability Rules`; ADR-03 `Audit`; ADR-09 `Identity Domains` and
`ADR Dependencies`; ADR-10 `Retention Model`; ADR-11 `Replay Audit`.

**Completion rationale:** only terms already defined or explicitly named for completion are used.

## Normative Rules

The following rules are the complete normative contribution of ADR-17:

- **OBS-01:** Telemetry, metrics, traces, statistics, diagnostics, Audit Records, Execution Ledger
  facts, and Replay Ledger facts MUST remain typed and distinguishable.
- **OBS-02:** Observational artifacts MUST NOT create Evidence, semantic input, plan state,
  execution authority, lifecycle authority, Commit authority, handoff eligibility, or Decision
  authority.
- **OBS-03:** Semantic, dispatch, execution, storage, replay, governance, and diagnostic
  observations MUST retain separate source identity, authority, context, and audience.
- **OBS-04:** Trace and audit composition MUST preserve originating identities, qualified digests,
  causal lineage, logical ordering, authority, and governing profiles.
- **OBS-05:** Audit facts MUST remain append-only, attributable, integrity-verifiable, and
  historically interpretable; correction MUST append lineage rather than mutate a prior fact.
- **OBS-06:** Chain of custody MUST preserve every governed acquisition, projection, export,
  redaction, archival, migration, and destruction fact affecting interpretation.
- **OBS-07:** Retention MUST satisfy the strongest applicable frozen obligation across source
  authority, audit, replay, certification, migration, legal hold, lineage, and historical
  interpretation.
- **OBS-08:** Redaction MUST create or select a governed projection, preserve its relationship to
  the unredacted source, declare exclusions, and MUST NOT change source identity, content,
  authority, or history.
- **OBS-09:** Audience and exporter use MUST be explicit, least-privilege, purpose-bound,
  attributable, and MUST NOT widen source visibility or authority.
- **OBS-10:** Diagnostic and telemetry collection MUST NOT expose undeclared producer inputs,
  secrets, credentials, mutable runtime state, or cross-attempt communication.
- **OBS-11:** Semantic graph, temporal, lifecycle, storage, cache, invalidation, quarantine, and
  governance diagnostics MUST be retained for the periods required by their frozen audit, replay,
  certification, and migration obligations.
- **OBS-12:** Replay observations and the Replay Ledger MUST remain isolated from production
  telemetry, ledgers, caches, results, handoff, and authority while retaining original-versus-
  replay attribution.
- **OBS-13:** Authoritative and observational projections MUST use the applicable ADR-08
  determinism profile and ADR-09 canonicalization, digest, identity, and lineage rules.
- **OBS-14:** Equivalent admitted source facts, projection contract, audience, redaction contract,
  profiles, and logical boundary MUST produce the required canonically equivalent projection and
  audit interpretation.
- **OBS-15:** Retention expiry, archival, retirement, redaction, and permitted destruction MUST use
  existing ADR-10 authority and MUST leave every tombstone or lineage fact required by the source
  ADRs.
- **OBS-16:** Audit completeness MUST cover every fact required by the applicable domain Audit and
  Certification Rules; missing, redacted, destroyed, inaccessible, or unverifiable facts MUST
  remain explicit.
- **OBS-17:** Observability, audit, retention, redaction, audience, exporter, and chain-of-custody
  conformance MUST be included in the existing institutional Certification Profile and verdict.
- **OBS-18:** No observability or audit convenience MAY weaken a frozen semantic, temporal,
  authority, identity, replay, retention, migration, or EPIP-016 boundary.

### Normative Rule Traceability

| Rule | Originating ADR | Section | Deferred responsibility | Satisfied by |
| --- | --- | --- | --- | --- |
| OBS-01 | ADR-06, ADR-08, ADR-09 | `ADR Dependencies` | Separated telemetry and authoritative/observational projections | Typed separation of all observation and authority records |
| OBS-02 | ADR-02, ADR-08 | `Observability Rules`; `ADR Dependencies` | Telemetry isolation from inputs and authority | Absolute non-authority rule |
| OBS-03 | ADR-06 | `ADR Dependencies` | Separated semantic, dispatch, execution, diagnostic telemetry | Source-domain isolation |
| OBS-04 | ADR-03, ADR-07, ADR-09 | `ADR Dependencies` | Chain of custody, causality, Audit Record identity | Identity and causal composition |
| OBS-05 | ADR-03, ADR-07 | `Audit`; `ADR Dependencies` | Attestation and ledger audit continuity | Append-only audit rule |
| OBS-06 | ADR-03, ADR-09 | `ADR Dependencies` | Chain of custody, redaction, attestation | Custody-event preservation |
| OBS-07 | ADR-03, ADR-05, ADR-07, ADR-10, ADR-11 | `ADR Dependencies` | Retention across governance, temporal, ledger, storage, replay | Strongest-obligation rule |
| OBS-08 | ADR-02, ADR-03, ADR-05, ADR-08, ADR-09, ADR-10, ADR-11 | `Observability Rules`; `ADR Dependencies` | Redaction governance and identity | Immutable governed projection |
| OBS-09 | ADR-02 | `Observability Rules` | Audience and exporter rules | Explicit least-privilege export |
| OBS-10 | ADR-02, ADR-06, ADR-07 | `Observability Rules`; `Execution Context`; `ADR Dependencies` | Telemetry separation and secret/runtime isolation | Collection boundary |
| OBS-11 | ADR-04, ADR-05, ADR-07, ADR-10 | `ADR Dependencies` | Diagnostic, temporal, ledger, invalidation and quarantine retention | Domain diagnostic preservation |
| OBS-12 | ADR-11 | `ADR Dependencies`; `Replay Isolation` | Replay Ledger retention and isolation | Replay observation separation |
| OBS-13 | ADR-08, ADR-09 | `ADR Dependencies` | Projection determinism and identity | Existing profile application |
| OBS-14 | ADR-08, ADR-09 | `Determinism`; `ADR Dependencies` | Deterministic comparison evidence | Equivalent projection requirement |
| OBS-15 | ADR-10 | `Retention Model`; `ADR Dependencies` | Retention classes, legal holds, destruction approval | Existing authority and lifecycle use |
| OBS-16 | ADR-03 through ADR-11 | `Audit`; `Certification Rules`; `ADR Dependencies` | Cross-domain audit completeness | Complete required-fact projection |
| OBS-17 | ADR-03, ADR-08 | `Certification Authority`; `Certification Profiles` | Institutional certification composition | Existing profile inclusion |
| OBS-18 | ADR-01; ADR-02 through ADR-11 | `System Invariants`; `ADR Dependencies` | Constitutional non-expansion | Preservation of all frozen boundaries |

No normative rule is orphaned.

## Authorities

The existing Audit Authority from ADR-03 verifies audit history and separation. Existing domain
authorities remain authoritative for source facts. The existing Retention Authority and Durable
Result Retention Authority from ADR-10 govern archival, legal hold, retirement, and permitted
destruction in their scopes. The existing Certification Authority from ADR-03 owns the verdict.
Authorities producing diagnostics or projections retain only the narrow authority already assigned
by their source ADR.

No Observability Authority, Redaction Authority, Export Authority, or new authority type is created.

**Deferred from:** ADR-03 and ADR-10 `ADR Dependencies`; ADR-02 `Observability Rules`.

**Completion rationale:** the deferral requests governance across existing authorities, not new
authority ownership. Normative behavior is exhausted by OBS-04 through OBS-09 and OBS-15 through
OBS-18.

## Responsibilities

Source authorities identify authoritative facts. Diagnostic producers identify observations.
Audit Authority verifies composition and history. Retention Authority applies existing retention
decisions. Certification Authority evaluates conformance. Replay Authority maintains replay
isolation. None acquires another domain's authority.

**Deferred from:** ADR-03, ADR-06, ADR-08, ADR-10, and ADR-11 `ADR Dependencies`.

**Completion rationale:** this section maps existing responsibilities to OBS-01 through OBS-18 and
adds none.

## Lifecycle

ADR-17 establishes no new lifecycle. Audit facts use the append-only correction and archival rules
already required by ADR-03 and ADR-07. Diagnostic Reports and telemetry projections retain their
ADR-09 identity lineage and the source artifact's availability interpretation. Retention,
archival, retirement, legal hold, and destruction use ADR-10 lifecycle and authority. Replay
records use ADR-11 Replay Session and Replay Ledger lifecycle.

**Deferred from:** ADR-03, ADR-07, ADR-09, ADR-10, and ADR-11 `ADR Dependencies`.

**Completion rationale:** the deferred ADR was required to compose lifecycle retention, not invent
another state machine. OBS-05, OBS-07, OBS-12, and OBS-15 provide the complete rules.

## Invariants

The constitutional invariants are the consequences of OBS-01, OBS-02, OBS-05, OBS-08, OBS-12,
OBS-16, and OBS-18: observations never become authority; source history is immutable; redaction is
a projection; replay remains isolated; and missing audit evidence stays visible.

**Deferred from:** ADR-02 `Observability Rules`; ADR-03, ADR-08, ADR-09, and ADR-11
`ADR Dependencies`.

**Completion rationale:** these are restatements of traced rules, not additional invariants.

## Diagnostics

Existing Diagnostic Report identity and domain diagnostics distinguish telemetry/authority
conflation, causal gap, identity or digest mismatch, custody gap, retention violation, unauthorized
audience or export, redaction lineage failure, source mutation, replay contamination, and audit
incompleteness. Their disposition remains non-authoritative under OBS-01, OBS-02, OBS-04, OBS-06,
OBS-08, OBS-09, OBS-12, and OBS-16.

**Deferred from:** ADR-02, ADR-04, ADR-05, ADR-09, ADR-10, and ADR-11 `ADR Dependencies`.

**Completion rationale:** only deferred diagnostic-governance categories are composed.

## Audit

The audit contract is fully expressed by OBS-04 through OBS-09, OBS-11, OBS-15, and OBS-16. It
preserves domain attribution and does not create a second ledger or audit authority.

**Deferred from:** ADR-03, ADR-07, ADR-09, ADR-10, and ADR-11 `ADR Dependencies`.

**Completion rationale:** the section closes chain of custody, causality, retention, redaction, and
attestation obligations using existing records.

## Determinism

Projection and audit determinism are governed by OBS-13 and OBS-14 and therefore reuse ADR-08 and
ADR-09 profiles. Physical collection order and exporter timing remain observational unless an
earlier ADR already declares the fact authoritative.

**Deferred from:** ADR-08 and ADR-09 `ADR Dependencies`.

**Completion rationale:** no new equivalence relation is introduced.

## Replay Compatibility

Replay behavior is governed by OBS-07, OBS-11 through OBS-14, and OBS-16. The eight ADR-11 Replay
Modes remain unchanged. Redacted or unavailable history remains explicit rather than being filled
from current observations.

**Deferred from:** ADR-05 and ADR-11 `ADR Dependencies`.

**Completion rationale:** this satisfies Replay Ledger retention, Diagnostic Report, redaction,
comparison evidence, and attestation without defining a replay mode.

## Migration Considerations

Migration uses ADR-16 epochs, compatibility, lineage, shadow isolation, rollback, and retirement.
OBS-04 through OBS-09 and OBS-15 through OBS-18 preserve audit interpretation across migration.
No migration-specific authority or lifecycle is introduced.

**Deferred from:** ADR-03 through ADR-11 `Migration` and `ADR Dependencies`; ADR-16 `Migration
Model`.

**Completion rationale:** the missing ADR was required to preserve deferred audit evidence during
the already-defined migration model.

## Backward Compatibility

EPIP-016 and ADR-01 through ADR-16 remain unchanged. Existing telemetry and audit representations
remain valid only within their original contracts; compatibility projections use ADR-09 and
ADR-16 lineage. No new field or exporter becomes required by EPIP-016.

**Deferred from:** ADR-02 through ADR-11 `Backward Compatibility` and `ADR Dependencies`.

**Completion rationale:** OBS-18 closes compatibility without expanding the boundary.

## Alternatives Considered

Treating distributed domain Audit sections as complete was rejected because ADR-01 through ADR-11
explicitly defer a mandatory cross-domain ADR. Creating new observation authorities, ledgers,
identities, or lifecycles was rejected because the completion mandate prohibits architectural
expansion. A traced composition of existing obligations was selected.

**Deferred from:** ADR-01 and ADR-02 through ADR-11 `ADR Dependencies`.

**Completion rationale:** the alternatives address only the legally required form of closure.

## Decision

ADR-17 adopts OBS-01 through OBS-18 as the complete cross-domain observability, audit, retention,
and redaction rules deferred by the frozen corpus. All source authority, identity, lifecycle,
semantic, execution, replay, migration, and EPIP-016 contracts remain unchanged.

**Deferred from:** ADR-01 and ADR-02 through ADR-11 `ADR Dependencies`.

**Completion rationale:** every adopted rule appears in the traceability table; no orphan rule is
accepted.

## Consequences

The deferred audit domains now compose consistently. The cost is stricter retention, custody,
projection, and certification evidence. No implementation, storage technology, telemetry system,
or exporter is selected.

**Deferred from:** ADR-03, ADR-07 through ADR-11 `ADR Dependencies`.

**Completion rationale:** these are consequences of OBS-04 through OBS-17, not new obligations.

## Future Evolution

Future change is limited by OBS-18 and ADR-16. This ADR introduces no future architectural work.
Any later representation or tool remains subordinate to the traced rules and cannot create a new
authority, identity domain, replay mode, or lifecycle without a separate constitutional decision.

**Deferred from:** ADR-16 `Future Evolution`; ADR-01 `Future Evolution`.

**Completion rationale:** the section rejects expansion and preserves existing evolution governance.

## Approval Gate

Approval closes only the mandatory observability/audit dependency. It authorizes no implementation
and does not by itself close the separate capacity/operational-governance dependency.

**Deferred from:** ADR-01 `ADR Dependencies` and `Approval Gate`.

**Completion rationale:** this preserves the original two-part closure condition.
