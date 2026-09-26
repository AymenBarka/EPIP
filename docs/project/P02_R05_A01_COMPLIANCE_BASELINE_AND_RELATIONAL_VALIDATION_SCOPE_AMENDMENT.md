# P02-R05-A01 — Compliance Baseline and Relational Validation Scope Amendment

Status: **CLOSED / FROZEN at governance level**, subject to exact-commit publication gates

P02-R05: **AUTHORIZED / IMPLEMENTATION IN PROGRESS**

## Authority and boundary

This governance-only amendment supplements the
[P02-R05 authority](P02_R05_SEMANTIC_FACT_IDENTITY_AND_MULTI_INPUT_GEOMETRY_REQUEST_AMENDMENT.md).
It authorizes the narrowly specified compliance-reference maintenance below and
freezes relational validation requirements for resumed R05 implementation. It
does not implement, certify, or close R05.

The starting branch is `develop` at
`7fb3eec063ea2452e90277384ce12ac621930e97`, with refreshed `origin/develop`
parity. Authorized R05 production and test changes already exist unstaged.
They must remain preserved and excluded from this documentation-only commit.
The last clean authoritative collection is 3074; A01 adds zero test nodes.
No current dirty-worktree collection or clean local regression is asserted.

## Independently measured compliance baseline

The unchanged authoritative scanner is
`epip/core/integrity_compliance.py::scan_immutable_dataclasses`; its
`compliance_digest` hashes the sorted qualified-name/mode inventory material.
Repeated scans of the current R05 working tree produce the same result:

| State | Inventory | Canonical SHA-256 digest |
| --- | --- | --- |
| Pre-R05 | 610 | `522ea5bed864f02263ac38219ca3e8ff9bbd91f1905b842e42bb41c050c9e218` |
| Authorized R05 working tree | 612 | `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1` |

Exactly two new entries explain the entire delta, both in `explicit` mode:

- `epip.strategy_mapping.rule_values.SemanticFactIdentity`;
- `epip.strategy_mapping.rule_requests.DirectionalCandidateSourceSetRequest`.

Removing exactly these entries from the measured inventory reproduces both
the previous count and its frozen digest. No other inventory additions or
historical entry changes are authorized. The scanner and its test currently
have no changes relative to the starting commit.

The previous expectation that adding two inventoried frozen public dataclasses
could preserve the compliance digest was incorrect. These additions necessarily
change its canonical material. This is authorized baseline evolution, not a
regression or an exception to integrity enforcement.

## Exact additional test-file authorization

Resumed R05 implementation may additionally modify only
`tests/core/test_integrity_compliance.py`, solely to replace `EXPECTED_DIGEST`
with `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1`.
The current test has no expected-count constant: do not invent a new baseline
framework or add a functional condition. Independently verify inventory 612
and the exact two additions as part of implementation closure evidence.

Keep both existing tests and all assertions. Scanner production code, algorithm,
exclusions, filtering, ordering, digest algorithm, inventory semantics, and
historical contracts remain frozen. Do not suppress either new contract from
the inventory or introduce special cases. A different inventory delta or a
non-reproducible digest requires reconciliation before closure.

This baseline update is authorized for resumed R05 implementation only. A01
does not edit the test or any implementation file.

## Exact candidate, source, and context relationships

The authority is the existing `SemanticCandidate`,
`SemanticRuleInvocationContext`, and `AnalyticalSourceBinding` contracts,
the [P02 execution contract](P02_F02_SEMANTIC_RULE_EXECUTION_CONTRACT.md), and
the frozen adapter's extraction and transformation lineage checks. The new
request transports already typed, identity-valid inputs; it introduces no
domain interpretation or new producer registry.

For every candidate `c`, exactly one supplied source `s` must satisfy
`c.source_binding_id == s.source_binding_id`. Duplicate source IDs are invalid,
so lookup is unambiguous. A missing source fails with `DataIntegrityError`.
An equal value, instrument, timeframe, source kind, source object label, or
tuple position cannot substitute for this canonical binding identity.

The following equalities and membership checks are mandatory:

| Relationship | Required invariant |
| --- | --- |
| Candidate to exact source | `c.source_binding_id == s.source_binding_id` |
| Candidate provenance to exact source | `c.provenance_ref == s.provenance_ref` |
| Candidate instrument to exact source | `c.instrument_binding_id == s.instrument.binding_id` |
| Candidate timeframe to exact source | `c.timeframe == s.timeframe` |
| Source and candidate instrument to context | Both equal `context.instrument_binding_id` |
| Source and candidate timeframe to context | Both equal `context.timeframe` |
| Source and candidate binding membership | Both IDs belong to `context.source_binding_ids` |
| Source and candidate provenance membership | Both references belong to `context.provenance_refs` |

Apply the source/context checks to every supplied source, including additional
sources that no candidate references. Context tuples are independently
canonicalized sets of references, not positionally paired lists. Membership in
each context tuple alone is insufficient: a candidate cannot borrow another
supplied source's provenance, even if both references appear in the context.
Each failed relationship is a structural `DataIntegrityError`, before sorting
and before rule invocation.

`source_binding_id` is the existing digest of the complete source-binding
contract excluding its ID. It preserves exact payload, source object, revision,
instrument, timeframe, and provenance attribution. Do not replace it with
`canonical_key()`, a reduced key, or a newly invented identity.

### Producer and manifest authority remain distinct

`candidate.source_rule_identity` is the exact typed producer `RuleIdentity`
and participates in candidate identity. `context.rule_identity` identifies the
consuming invocation. They need not be equal: an extraction producer may supply
a subsequent applicability, boundary, or transformation rule. Candidates from
different valid producers retain their respective identities and are not merged.

The source binding has no producer-rule field, and the invocation context has
no producer allowlist. Therefore the request must not invent a producer-to-source
registry, require all producers to be identical, parse rule names, or require
producer equality with the consuming rule. Existing extraction validation
checks producer equality with the actual selector rule at its own boundary;
this authority remains unchanged. Producer authorization is not newly inferred
from request membership.

Likewise, `AnalyticalSourceBinding.validate_for` retains evaluation/manifest
validation, including source-object attribution, metadata, availability, and
revision checks. The new request has neither `EvaluationContext` nor
`ProvenanceManifest`; it must not manufacture them or claim to independently
certify their upstream checks. Its exact candidate/source/context continuity
checks complement those existing boundaries without weakening or relocating
them. No P03, adapter, source-binding, or A07 change is required.

## Validation before canonicalization

The resumed new-request implementation must follow this order:

1. Validate exact context and direction types and exact tuple/member types.
2. Require both candidate and source tuples to be non-empty.
3. Require candidate identity integrity under existing candidate construction
   and reconstruction validation, including the R05 fact/default projection.
4. Require source identity integrity under existing source construction and
   reconstruction validation. Reuse existing contracts, not a second digest
   framework. These immutable members normally satisfy steps 3 and 4 before
   entering request construction; no bypass of their validators is authorized.
5. Detect duplicate `candidate_id` values and fail closed.
6. Detect duplicate `source_binding_id` values and fail closed.
7. Validate every candidate and source against the invocation context.
8. Validate each candidate against its exact supplied source, including the
   provenance equality above.
9. Only after successful validation, sort candidates by `candidate_id`.
10. Sort sources by `source_binding_id`.
11. Store the canonical tuples on the frozen request.

Exact tuple and non-empty checks may share the existing typed-tuple helper.
Identity validation remains at the existing immutable construction boundaries;
this sequence does not authorize mutation of nested inputs or a new validator
framework. Duplicate checks must precede both sorting operations. Do not use
set conversion to silently deduplicate either population. Canonicalization must
not mask invalid relationships or duplicates. Equivalent valid permutations
produce equal canonical requests; input order carries no business meaning.

The current unfinished draft checks context membership without the required
exact-source provenance equality and sorts before all relationships have been
validated. These are required resumed R05 corrections, not A01 code changes.

## Unchanged implementation scope and functional conditions

The only authorized R05 production files remain:

- `epip/strategy_mapping/rule_values.py`;
- `epip/strategy_mapping/rule_requests.py`;
- `epip/strategy_mapping/resolved_rules.py`;
- `epip/strategy_mapping/__init__.py`.

The four existing R05 functional suites remain:

- `tests/strategy_mapping/test_rule_execution_contracts.py`;
- `tests/strategy_mapping/test_execution_serialization.py`;
- `tests/strategy_mapping/test_resolved_rules.py`;
- `tests/strategy_mapping/test_directional_candidate_source_set.py`.

Only the compliance test file specified above is additionally authorized, with
its exact maintenance restriction. Exactly 34 governed generic functional
conditions remain required. Source membership and relational/provenance cases
belong within conditions 30 and 31; duplicate ordering belongs within 27 and 28;
permutation equivalence belongs within 25 and 26. Additional parametrized nodes
must be reported separately from the 34 conditions. Compliance-reference
maintenance does not create a 35th functional condition.

R05 fact semantics remain unchanged: `None` preserves historical candidate
identity and hash projections; a specified fact participates in identity;
same-valued candidates with different facts remain distinct. Serialization,
dispatch admissions, old request behavior, and all other R05 requirements
remain governed by the original amendment.

## Resumption, publication, and downstream state

This milestone stages and commits only this artifact and `ROADMAP.md`, after
explicit staged-diff verification. Preserve all unfinished implementation and
unrelated untracked artifacts. Run `git diff --check`, Markdownlint, and
`mkdocs build --strict`. Push normally and verify refreshed HEAD/origin parity
and exact-SHA Quality, CodeQL, and Documentation success.

Remote CI validates the documentation commit containing the frozen predecessor
implementation, not local unfinished R05 code. Its results cannot certify R05.
The dirty-worktree compliance scan above proves the prospective inventory only;
it does not replace implementation regression or coverage evidence.

On resumption, update the authorized compliance reference, complete exact
relationships, move sorting after validation, certify all 34 conditions, run
the complete R05 regression/coverage/stress and documentation gates, and obtain
exact-final-SHA remote passes before closing R05. No implementation closure is
granted by this amendment.

| Milestone | State after successful A01 publication |
| --- | --- |
| P02-R05-A01 | CLOSED / FROZEN at governance level |
| P02-R05 | AUTHORIZED / IMPLEMENTATION IN PROGRESS; A01 SCOPE AMENDMENT AUTHORIZED |
| P04-F00 / P04-F01 | CLOSED / FROZEN; fingerprints and cardinality unchanged |
| P03 | CLOSED / FROZEN; zero production changes |
| A07 | CLOSED / FROZEN; zero production changes; E07 exclusively owns RR |
| P04-F02 | NOT AUTHORIZED / PREDECESSOR AMENDMENT REQUIRED |
| P04-F03 / P04-F04 | NOT AUTHORIZED |
| P05 | NOT AUTHORIZED |

Only successful R05 implementation closure can make F02 ready for a fresh
authorization review. A01 authorizes no F02 implementation, P04 semantics,
P05 behavior, release, tag, or version change.
