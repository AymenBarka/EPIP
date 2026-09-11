# P02-R03 — Additive Semantic Declaration and Candidate Role Amendment

Status: COMPLETE / CLOSED / FROZEN

Authority class: predecessor contract reconciliation

Affected program: P02 only

## 1. Decision

The missing predecessor capability can be added strictly additively. Existing
P02 objects, callers, serialized inputs, canonical identities, equality
relations, and public behavior need not change unless a caller explicitly uses
the new capability.

This document defines the complete amendment but does not authorize its
implementation. P04-F01 remains governance-blocked until this amendment is
separately authorized, implemented, validated on an exact SHA, and frozen.

## 2. Authority and purpose

This proposal reconciles the frozen P02 execution contract with the proposed
P04-F00-R03 requirement for:

- a complete future rule catalog distinct from an executable manifest;
- typed semantic-candidate roles;
- direction-neutral structural applicability; and
- historical serialization and canonical-identity continuity.

The governing P02 authorities are the P02-F00, P02-F02, P02-F04, P02-F06,
P02-F08, P02-F10, P02-F12, P02-F14 and P02-F16 contracts, P02-R02 and
P02-R02-I00, P02 final closure, ADR-0029, and the frozen implementation.

P02-R02-I00 establishes the applicable additive-evolution precedent: a final
defaulted field may be emitted by the existing tagged serializer, historical
missing-field payloads reconstruct through the default, and byte-identical
serialization is not required. Canonical identities must nevertheless follow
the explicit rules below.

## 3. Exact scope

The amendment adds:

1. `SemanticRuleCatalogState`;
2. `SemanticRuleCatalogEntry`;
3. `SemanticRuleCatalog`;
4. `SemanticCandidateRole`;
5. a final `role` field on `SemanticCandidate`;
6. `SemanticInvocationKind.STRUCTURAL_APPLICABILITY`;
7. `StructuralApplicabilityRequest`; and
8. an additive, checked `ResolvedSemanticRuleSet.invoke()` entry point.

It does not alter the fields or semantics of `SemanticRuleDeclaration`,
`ResolvedRuleManifest`, `ApplicabilityRequest`, `BoundarySelectionRequest`,
`CandidateRuleResult`, or `StrategySemanticMappingProfile`.

## 4. Rule catalog contract

### 4.1 State

`SemanticRuleCatalogState` is a closed public enum owned by
`epip.strategy_mapping.resolved_rules`:

- `EXECUTABLE`
- `DECLARATION_ONLY`

The enum has no implicit default because it is used only by a new contract.
Unknown values fail closed under the existing enum-deserialization behavior.

### 4.2 Entry

`SemanticRuleCatalogEntry` is a new frozen, slotted, ordered public dataclass
with these fields in this order:

1. `identity: RuleIdentity`
2. `family: SemanticRuleFamily`
3. `invocation_kind: SemanticInvocationKind`
4. `result_kind: SemanticResultKind`
5. `state: SemanticRuleCatalogState`
6. `implementation_id: str | None = None`

All type checks are exact. Family/invocation/result compatibility uses the same
closed compatibility authority as executable declarations.

- `EXECUTABLE` requires a non-empty `implementation_id`.
- `DECLARATION_ONLY` requires `implementation_id is None`.
- A placeholder, empty string, future module path, or prospective implementation
  name is not a valid implementation ID.

State and implementation ID participate in ordering, equality, hashing,
serialization, and catalog identity. No historical object uses this new type.

### 4.3 Catalog

`SemanticRuleCatalog` is a new frozen, slotted public dataclass:

1. `schema_version: str`
2. `catalog_id: str`
3. `entries: tuple[SemanticRuleCatalogEntry, ...]`

The schema version is the existing P02 execution schema version. Entries are a
non-empty tuple, canonically sorted by `identity.reference`, with unique
identities. `catalog_id` is the existing canonical SHA-256 digest of schema
version and ordered entries, excluding only `catalog_id`.

The catalog exposes a pure `executable_manifest()` operation. It:

1. selects exactly entries whose state is `EXECUTABLE`;
2. constructs exact `SemanticRuleDeclaration` objects from those entries;
3. rejects an empty executable selection;
4. returns `ResolvedRuleManifest.create(...)`; and
5. performs no discovery, import, implementation lookup, or mutation.

## 5. Executable closure invariant

The frozen meanings remain distinct:

```text
catalog identities
    = executable identities union declaration-only identities

executable identities intersect declaration-only identities
    = empty set

executable manifest identities
    = semantic profile rule closure
    = resolved implementation identities
```

`ResolvedRuleManifest` remains an exact executable manifest. Its fields,
identity derivation, historical payloads, and closure validation do not change.

A declaration-only entry:

- may occur in `SemanticRuleCatalog`;
- may not occur in the catalog-derived executable manifest;
- may not be bound to an implementation;
- may not occur in executable semantic-profile closure; and
- may not be resolved or invoked.

An executable entry must appear exactly once in the executable manifest, exact
profile closure, and resolved implementation tuple before adapter execution.
Missing, extra, duplicate, or state-contradictory entries raise
`DataIntegrityError` before downstream invocation.

This design deliberately does not add state to `SemanticRuleDeclaration`.
Doing so would change every historical manifest's canonical field graph and
would overload a type whose frozen meaning is already “executable declaration.”

## 6. Semantic candidate role

### 6.1 Enum

`SemanticCandidateRole` is a closed public enum owned by
`epip.strategy_mapping.rule_values` with reusable, strategy-neutral values:

- `UNSPECIFIED`
- `QUALIFICATION`
- `ANCHOR_START`
- `ANCHOR_END`
- `ZONE`
- `ENTRY`
- `STOP`
- `TARGET`

Source-rule identity and provenance distinguish which producer supplied an
anchor or zone. P02 does not encode Elliott, Fibonacci, Wave-3, or P04 feature
names in this enum.

### 6.2 Candidate field

Append this final field to `SemanticCandidate`:

```python
role: SemanticCandidateRole = SemanticCandidateRole.UNSPECIFIED
```

The field is last. Existing seven-argument positional construction and all
existing keyword construction remain valid. `SemanticCandidate.create()` adds
the final keyword-only argument with the same default.

The role is exact typed input. Arbitrary strings, integer coercion, role lookup
from rule-ID text, value-shape inference, and positional tuple semantics are
prohibited.

### 6.3 Equality and hashing

Role participates in equality. Two otherwise identical candidates with
different roles are unequal.

To preserve the effective legacy hash contract:

- `UNSPECIFIED` hashes the exact historical seven-field tuple;
- a non-legacy role hashes that historical tuple plus the role.

This requires an explicit `__hash__`; it does not change equality between any
two legacy candidates. Equal objects always have equal hashes.

### 6.4 Candidate identity

Candidate ID derivation is version-compatible without changing the digest
framework:

- for `UNSPECIFIED`, exclude both `candidate_id` and `role` from the canonical
  digest, reproducing the historical candidate ID exactly;
- for every other role, exclude only `candidate_id`, so role is identity-bearing.

Construction and `__post_init__` use the same branch. An ID copied from one role
to another fails with `DataIntegrityError`. No role normalization occurs.

## 7. Legacy UNSPECIFIED truth table

The existing serializer emits every dataclass field. New output therefore
includes an explicit role even when it is `UNSPECIFIED`; this is governed
schema evolution, not byte-preserving output.

| Input | Reconstructed role | New serialized output | Legacy equality | Hash | Candidate ID |
| --- | --- | --- | --- | --- | --- |
| Historical payload, role missing | `UNSPECIFIED` | Explicit enum field | Preserved | Historical projection | Preserved |
| New payload, explicit `UNSPECIFIED` | `UNSPECIFIED` | Explicit enum field | Preserved | Historical projection | Preserved |
| New object, role omitted | `UNSPECIFIED` | Explicit enum field | Preserved | Historical projection | Preserved |
| New payload, non-legacy role | Exact supplied role | Explicit enum field | Not legacy-equal | Role-bearing | Role-bearing |
| New payload, unknown role | No object | No output | N/A | N/A | N/A |

Missing role and explicit `UNSPECIFIED` are semantically and canonically
equivalent. New writers may not suppress the field because the existing generic
serializer emits all declared fields.

## 8. Structural applicability

### 8.1 Rejected alternatives

- Making `ApplicabilityRequest.direction` optional weakens a frozen request and
  permits misuse unless every implementation repeats capability checks.
- An applicability-mode field on the existing request changes every historical
  request's serialization and hash surface.
- Rule-name parsing, signature inspection, `isinstance` guessing, or direction
  inference is prohibited.

### 8.2 Chosen contract

Add `SemanticInvocationKind.STRUCTURAL_APPLICABILITY` and allow the
`APPLICABILITY` family these two exact compatible pairs:

- `APPLICABILITY` invocation + `APPLICABILITY` result: directional;
- `STRUCTURAL_APPLICABILITY` invocation + `APPLICABILITY` result: structural.

Add `StructuralApplicabilityRequest`, a frozen, slotted public dataclass with:

1. `context: SemanticRuleInvocationContext`
2. `candidate: SemanticCandidate`

Both fields are exact typed. It has no direction field.

`ApplicabilityRequest` remains unchanged and continues to require exact
`StrategyDirection`. Thus:

- structural rule + structural request: allowed;
- structural rule + directional request: `DataIntegrityError` before invoke;
- directional rule + directional request: unchanged;
- directional rule + structural request: `DataIntegrityError` before invoke;
- directional rule with missing direction: construction fails before invoke;
- structural-with-direction is prohibited, not ignored.

The invocation kind is the explicit capability declaration. No additional mode
metadata is needed.

## 9. Checked invocation entry point

Add `ResolvedSemanticRuleSet.invoke(identity, request)` without changing
`resolve()` or existing callers. The new operation:

1. resolves the exact identity;
2. locates its exact executable declaration;
3. requires the exact request type governed by its invocation kind;
4. invokes the implementation once;
5. requires the exact result type governed by its result kind; and
6. returns the typed result or raises `DataIntegrityError`.

This is the opt-in execution boundary for structural rules. It is additive;
existing adapter dispatch remains observationally unchanged. A later separately
authorized integration may migrate existing adapter calls to this checked
operation, but this amendment does not require that migration.

## 10. Serialization compatibility

The serializer framework is unchanged.

| Flow | Result |
| --- | --- |
| Old writer -> new reader | Accepted; missing candidate role defaults to `UNSPECIFIED` |
| New writer -> new reader | Accepted; all new enums/types/fields round-trip canonically |
| New writer -> old reader | Not guaranteed; old code rejects unknown fields/types fail-closed |
| Historical fixture -> new reader -> new writer | Semantic equality, legacy hash projection, and candidate ID preserved; bytes gain explicit role |

Unknown dataclass fields continue to fail reconstruction through the existing
`DataIntegrityError` wrapper. Unknown enum values continue to fail closed under
the serializer's existing enum-construction behavior. No tag, qualified-name,
key-order, import, or serializer-dispatch rule changes.

Catalogs, catalog entries, structural requests, and role-bearing candidates use
the existing tagged dataclass/enum encoding and deterministic JSON key sorting.

## 11. Identity, equality and fingerprint matrix

| Semantic item | Equality/hash | Serialization | Canonical identity/fingerprint |
| --- | --- | --- | --- |
| Catalog state | Yes | Yes | Yes, in new `catalog_id` |
| Catalog implementation ID | Yes | Yes | Yes, in new `catalog_id` |
| Candidate `UNSPECIFIED` | Legacy projection | Explicitly emitted | Excluded to preserve legacy candidate ID |
| Candidate non-legacy role | Yes | Yes | Included in candidate ID |
| Structural request type | Yes | Yes | No derived request ID exists |
| Structural invocation kind | Yes | Yes | Included in new declarations/manifests |
| Existing rule declaration | Unchanged | Unchanged | Existing manifest IDs unchanged |
| Existing directional request | Unchanged | Unchanged | No derived request ID exists |

Rule fingerprints in `RuleIdentity` do not change merely because the
infrastructure gains a new invocation kind. A rule changing from directional to
structural invocation requires a new executable manifest identity, as it should;
its independently governed semantic fingerprint changes only if its declared
semantics change.

## 12. Positional and keyword compatibility

The following remain valid and unchanged:

```python
SemanticCandidate(candidate_id, source_id, provenance, instrument, timeframe, rule, value)
SemanticCandidate.create(
    source_binding_id=source_id,
    provenance_ref=provenance,
    instrument_binding_id=instrument,
    timeframe=timeframe,
    source_rule_identity=rule,
    value=value,
)
ApplicabilityRequest(context, candidate, direction)
SemanticRuleDeclaration(identity, family, invocation, result, implementation_id)
```

New capability is explicit:

```python
SemanticCandidate.create(..., role=SemanticCandidateRole.ANCHOR_START)
StructuralApplicabilityRequest(context, candidate)
SemanticRuleCatalogEntry(..., SemanticRuleCatalogState.DECLARATION_ONLY)
```

No required field is inserted before a historical field.

## 13. Failure behavior

| Defect | Failure phase | Outcome |
| --- | --- | --- |
| Declaration-only entry has implementation ID | catalog-entry construction | `DataIntegrityError` |
| Executable entry lacks implementation ID | catalog-entry construction | `DataIntegrityError` |
| Duplicate catalog identity | catalog construction | `DataIntegrityError` |
| Declaration-only rule enters executable manifest | manifest derivation/binding | `DataIntegrityError` |
| Executable/profile closure differs | existing closure validation | `DataIntegrityError` |
| Unknown catalog state or candidate role | enum decode/construction | fail closed; no object |
| Candidate role/ID tampering | candidate construction | `DataIntegrityError` |
| Structural rule receives directional request | checked dispatch | `DataIntegrityError`; no invoke |
| Directional rule receives structural request | checked dispatch | `DataIntegrityError`; no invoke |
| Directional direction absent | request construction | `DataIntegrityError`/`TypeError`; no invoke |
| Wrong result type | checked dispatch | `DataIntegrityError` |
| Duplicate role where a consuming rule requires uniqueness | consuming rule input validation | `DataIntegrityError`; no downstream invoke |

Domain non-match remains a typed rule result. Structural contract violations are
not normalized into domain non-match.

## 14. Determinism

All new enums are closed. Catalog and candidate identity use existing canonical
JSON and SHA-256. Catalog entries sort by exact rule reference. No time,
randomness, environment, filesystem, network, mutable registry, dynamic import,
reflection, discovery, fallback, tolerance, or unordered canonicalization is
introduced.

## 15. Public API

The new enums and contracts are public because separately owned strategy-profile
packages must declare catalogs, create typed candidates, implement structural
rules, and invoke them without importing P02 internals. They are exported from
their owning modules and `epip.strategy_mapping`.

The compatibility/request/result dispatch maps remain private implementation
details. No P04-specific symbol is public or private in P02.

## 16. P02, P03 and A07 impact

P02 production changes are limited to the new contracts, candidate legacy
projection, compatibility map, checked invocation method, and exports.

P03 production changes: none. Existing P03 requests, results, serialized graphs,
and adapter handoff remain unchanged.

A07 production changes: none. Existing policy/profile identities and adapter
output shapes remain unchanged. No role is added to A07 evidence or signal
contracts.

P04-F00 must later replace its misuse of a 37-entry `ResolvedRuleManifest` with
a 37-entry `SemanticRuleCatalog`, marking future entries declaration-only. Any
actual executable manifest remains exact profile closure. That P04 re-freeze is
outside this amendment.

P04-F01 may use generic roles, structural requests, and a checked feature rule
set only after both amendments are closed. This amendment does not authorize
P04-F01 or final adapter integration.

## 17. Compliance impact

The amendment introduces three frozen dataclasses:

- `SemanticRuleCatalogEntry`
- `SemanticRuleCatalog`
- `StructuralApplicabilityRequest`

Under the current compliance scanner, the expected inventory is therefore 609,
subject to governed implementation-time verification. Enum additions and a new
field on an existing dataclass do not add inventory entries.

The digest necessarily changes because the qualified-name/mode inventory gains
three entries. No proposed digest is normative until generated by the governed
implementation and independently verified. Automatic or silent baseline
rewriting is prohibited.

## 18. Migration

No historical P02 payload migration is required. The new reader accepts legacy
candidates and manifests directly. Existing manifests remain executable
manifests with their existing IDs.

P04-F00 requires an explicit, separately reviewed migration from its proposed
all-rule executable-manifest usage to the new catalog. The migration retains all
37 `RuleIdentity` values and classifies each state; it does not delete future
rules to force profile equality.

## 19. Test obligations

Implementation authorization must require at least these 48 test conditions.

### A. Catalog and declaration state — 8

1. explicit executable entry;
2. explicit declaration-only entry;
3. executable missing implementation ID rejection;
4. declaration-only implementation ID rejection;
5. deterministic ordering;
6. duplicate identity rejection;
7. executable-manifest derivation; and
8. exact executable/profile closure with declaration-only exclusion.

### B. Candidate roles — 12

1. historical missing-role payload;
2. omitted-role constructor;
3. explicit `UNSPECIFIED`;
4. each of the seven non-legacy roles;
5. role equality difference;
6. role hash behavior;
7. unknown role rejection;
8. wrong-type role rejection;
9. role/ID tamper rejection;
10. legacy ID fixture stability;
11. non-legacy ID separation; and
12. deterministic role-bearing round trip.

The parameterized seven-role condition counts as one governed condition and
must exercise every enum member.

### C. Structural applicability — 8

1. historical directional request unchanged;
2. directional rule plus direction;
3. directional missing direction rejection;
4. structural request without direction;
5. structural rule plus directional request rejection;
6. directional rule plus structural request rejection;
7. structural request wrong candidate/context rejection; and
8. wrong structural result type rejection.

### D. Compatibility and serialization — 8

1. old positional candidate construction;
2. old keyword candidate construction;
3. old declaration construction;
4. old applicability construction;
5. old writer/new reader candidate fixture;
6. historical fixture/new writer semantic round trip;
7. catalog tagged round trip; and
8. structural-request tagged round trip.

### E. Identity and negative closure — 5

1. historical candidate hash projection;
2. historical manifest ID fixture;
3. catalog state changes catalog ID;
4. structural invocation changes new manifest ID; and
5. declaration-only binding rejected before invocation.

### F. Regression and quality — 7

1. P02 suite;
2. P03 suite;
3. A07 suite;
4. P04-F00 regression;
5. full collection with aggregate coverage at least 95%;
6. Black, Ruff, MyPy and `git diff --check`; and
7. compliance inventory/digest plus exact-SHA remote Quality and CodeQL.

## 20. Expected implementation file scope

### Expected P02 production files

- `epip/strategy_mapping/rule_execution.py`
- `epip/strategy_mapping/rule_values.py`
- `epip/strategy_mapping/rule_requests.py`
- `epip/strategy_mapping/resolved_rules.py`
- `epip/strategy_mapping/__init__.py`

No serializer file is expected to change.

### Expected P02 test files

- `tests/strategy_mapping/test_rule_execution_contracts.py`
- `tests/strategy_mapping/test_resolved_rules.py`
- `tests/strategy_mapping/test_execution_serialization.py`
- `tests/strategy_mapping/test_rule_catalog.py`
- `tests/strategy_mapping/test_structural_applicability.py`

### Expected documentation files

- this amendment, updated from proposed to implemented evidence only after
  authorization and validation;
- `docs/project/ROADMAP.md` only in a separately authorized status-recording
  step; and
- P04-F00-R03 only after the P02 amendment is frozen.

Any required production file outside the five-file boundary requires renewed
governance review before editing.

## 21. Explicit non-goals

This amendment does not:

- implement P04 rules or P04-specific semantics;
- change existing adapter behavior or output;
- add final profile integration;
- change P03 or A07;
- make direction optional on directional applicability;
- serialize executable Python code;
- introduce arbitrary candidate tags;
- infer roles or capabilities;
- mutate historical manifests or IDs;
- regenerate compliance baselines;
- authorize P04-F01, P04-F02, P04-F03, P04-F04, or P05; or
- tag, release, publish, or bump a version.

## 22. Governance gap disposition

- **G0:** existing executable-manifest closure, directional applicability,
  serializer framework, determinism, and failure boundary remain exact.
- **G1:** catalog-versus-manifest terminology is resolved by distinct types.
- **G2:** P02-R02-I00 supplies the additive missing-field serialization
  precedent.
- **G3:** candidate default, legacy identity projection, structural-with-direction
  behavior, catalog state, and forward-reader behavior are fixed above.
- **G4:** none remains inside this amendment.
- **G5:** none remains; no frozen type must be removed, reordered, or weakened.

## 23. Implementation authorization

P02-R03 implementation was separately authorized with the five-production-file
boundary, five focused test files, 48 governed test conditions, compliance
inventory review, and exact-SHA closure gates defined here.

Final implementation disposition:

- P02-R03 is **COMPLETE / CLOSED / FROZEN**;
- P04-F00-R03 is **PROPOSED / NOT FROZEN**; and
- P04-F01 is **NOT AUTHORIZED / GOVERNANCE BLOCKED**.

## 24. Implementation evidence

The authorized implementation preserves the five-file P02 production boundary
and adds no P03, A07, or P04 production change.

Local evidence on the implementation worktree:

- focused P02-R03 contract selection: 45 passed before final incremental
  closure additions;
- P02 strategy-mapping regression: 240 passed before final incremental closure
  additions;
- P03 regression: 59 passed;
- A07 regression: 571 passed;
- frozen P04-F00 profile regression: 7 passed;
- final collection: 2,958 nodes, an increase of 26 with zero predecessor-node
  removals;
- selected full regression: 2,957 passed and one designated EventBus stress
  node deselected;
- aggregate coverage: 97.34%;
- changed P02 production files: 97% combined statement coverage;
- EventBus stress: 1 passed;
- Ruff: passed repository-wide;
- strict MyPy: passed across 690 source files;
- compliance inventory: 609;
- compliance digest:
  `86f80e197821dae4c010a55fc8e3fbde25dfd43871d00841d17b7e68dcb4d977`;
  and
- `git diff --check`: passed.

The compliance delta is exactly three new explicit frozen dataclasses:
`SemanticRuleCatalog`, `SemanticRuleCatalogEntry`, and
`StructuralApplicabilityRequest`.

The implementation commit is
`83ef3e79d3b6e3cc6fa7e7e5ee25c935d7b45860`. It was pushed normally with
HEAD/origin parity. Exact-SHA remote closure evidence:

- Quality run `34626519988`: PASS, including Black, Ruff, MyPy, pytest,
  coverage, and EventBus stress;
- CodeQL run `34626519932`: PASS; and
- Documentation run `34626519958`: PASS, including Markdown style, links,
  Mermaid syntax, and documentation build.

P02-R03 is therefore complete, closed, and frozen. P04-F00-R03 remains proposed
and not frozen. P04-F01 and all later P04/P05 features remain not authorized.
