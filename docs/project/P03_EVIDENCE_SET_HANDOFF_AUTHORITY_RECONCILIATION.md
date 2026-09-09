# P03 Evidence-Set Handoff Authority Reconciliation

## Decision

The P03 evidence-set handoff authority is **NORMATIVELY RECONCILED** under **Model A — Handoff
Authority**. P02 is the sole authority that derives the ordered evidence-set identity. After an
accepted adaptation, P03 must preserve that identity and the ordered evidence tuple exactly when
constructing the A07 E00 request.

This is a governance-only clarification of ADR-0027 and ADR-0028. It changes no production
contract, serializer, identity algorithm, state, diagnostic, or A07 behavior.

## Blocker discovery

P03-F00 exposed an impossible negative-test requirement: compare an independently supplied
runtime-request evidence identity with `StrategyFactBundle.evidence_identity`. The frozen P01
`StrategyRuntimeRequest` has no evidence identity, and neither does `AnalyticalInputBundle`.
Requiring that comparison would force a frozen P01 schema change, a parallel binding contract, or
P03 recomputation of P02-owned identity. All three conflict with the existing architecture.

## Frozen request and pre-adaptation identity domains

`StrategyRuntimeRequest` contains the contract and request identities, `EvaluationContext`,
`AnalyticalInputBundle`, policy, profile identity, adapter identity, runtime contract version, and
options. Before adaptation the authoritative identity domains are:

- evaluation, run, instrument, and source-set identity in `EvaluationContext`;
- strategy and policy identity in the supplied policy;
- exact profile and adapter identity; and
- analytical input, MTF context, and provenance-manifest identity.

There is no expected evidence-set identity in the request or analytical input bundle.
`EvaluationContext.source_set_id` identifies the admitted source collection. It is not an evidence
set, must not be aliased to `StrategyFactBundle.evidence_identity`, and cannot be converted into
one by P03.

## P02 authority and first authoritative point

P02 owns semantic candidate selection, reduction, filtering, freshness and temporal outcomes,
ordered evidence membership, evidence-item identities, and the ordered evidence-set identity. Its
configured adapter derives item identities and then the set identity from the final semantic
entries. The evidence-set identity first becomes authoritative in an accepted
`FactAdapterResult` through its immutable `StrategyFactBundle`.

A caller cannot normatively know that final identity before adaptation because final membership,
order, eligibility, and provenance closure are P02 outputs. Requiring caller precommitment would
duplicate P02 authority and permit incoherent request/output pairs.

## Chosen authority model

Model A is frozen:

```text
StrategyRuntimeRequest (no evidence-set identity)
-> P02 FactAdapterProtocol
-> accepted StrategyFactBundle.evidence_identity = X
-> P03 constructs StrategyEvaluationRequest.evidence_identity = X
-> A07 consumes X and the exact ordered bundle.evidence tuple
```

Model B — caller precommitment — is rejected. Repository architecture does not require it, and it
would require a frozen P01 public-contract and serialization/versioning change without adding an
independent legitimate authority.

## Validation versus preservation

Validation compares independently authoritative values. Preservation carries one authoritative
value unchanged across a boundary. P03 evidence-set continuity is preservation.

The equality between `StrategyFactBundle.evidence_identity` and the constructed
`StrategyEvaluationRequest.evidence_identity` is therefore a construction/handoff invariant. It
is intentionally not an independent caller-input coherence check. Copying the value is no more a
defect than copying an authoritative provenance identity into an envelope; correctness is proven
by observing the downstream request.

## Exact P03 invariant

For an accepted bundle, P03 must:

1. construct the A07 E00 `StrategyEvaluationRequest` with the exact
   `bundle.evidence_identity` object/value;
2. pass the exact `bundle.evidence` tuple to E02 without sorting, rebuilding, or recomputing it;
3. never import or call P02 evidence identity derivation helpers; and
4. never substitute source-set, item, profile, adapter, or provenance identity for the set
   identity.

P03 owns the accepted bundle-to-A07 handoff. It does not derive or independently verify the
evidence-set digest. Construction defects are implementation defects, not caller-supplied
coherence outcomes and require no new runtime state or diagnostic.

## Reconciled test contract

The former mandatory public runtime request/bundle evidence mismatch test is removed because that
state is not representable by the frozen public contract. P03-F00 must instead prove:

- an adapter-produced set identity `X` is the exact identity observed in the A07 E00 request;
- multiple evidence members retain distinct item identities while the same set identity `X` is
  handed off;
- the exact semantic evidence tuple order is preserved;
- repeated equivalent evaluations perform the same identity handoff; and
- P03 neither imports nor calls P02 evidence identity helpers.

Malformed or missing accepted bundles and independently representable evaluation, strategy,
profile, adapter, policy, MTF, and provenance discontinuities remain valid negative coverage under
the existing runtime failure vocabulary.

## Layer impacts

- **P01:** no field, request, result, envelope, schema, version, or serializer change. Do not add
  `evidence_identity`, `ExpectedEvidenceIdentity`, `EvidenceBindingRequest`, or a wrapper request.
- **P02:** no change. It remains the sole item/set identity derivation authority.
- **A07:** no change. R01 remains frozen; A07 consumes the set identity and preserves ordered
  member/provenance continuity without deriving a P02 identity.
- **ADR-0027:** its orchestration decision now explicitly includes exact accepted-bundle-to-E00
  evidence preservation.
- **ADR-0028:** its bundle/request equality denotes the `StrategyFactBundle` to A07
  `StrategyEvaluationRequest` handoff, not a P01 `StrategyRuntimeRequest` field.
- **Serialization and compliance:** no impact. Inventory remains 606 and the governed digest
  remains `2b2aa94b9f3a8fb7ebe305be5dc3697f645197df82f3d12bee598d8f08c0930b`.

The model is identical in historical, backtest, paper, demo, and live runtime modes. No caller is
required to predict adapter-owned evidence membership or identity.

## P03-F00 unblock criteria

P03-F00 is ready to resume with the following frozen requirements:

- P02 is the sole evidence-set identity authority;
- P03 performs preservation, not independent request/bundle evidence validation;
- the P01 runtime request remains unchanged;
- P03 copies the exact bundle identity and ordered tuple into A07;
- positive observable handoff tests replace the impossible public mismatch test;
- no recomputation, P02 helper import, duplicate authority, or parallel contract is permitted; and
- P01, P02, A07, serialization, compliance, and shared-runtime semantics remain unchanged.

No new ADR is required because this document clarifies the already accepted ADR-0027/ADR-0028
layer boundary without making a new architectural decision.
