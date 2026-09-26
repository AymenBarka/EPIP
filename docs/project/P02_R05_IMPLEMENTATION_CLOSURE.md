# P02-R05 — Semantic Fact Identity and Multi-Input Request Implementation Closure

Status: **CLOSED / FROZEN**, subject to exact-final-commit publication gates

## Authority and preserved starting state

Implementation resumes the preserved R05 work on `develop` at
`9a1e8c79610b331ca64668b3ab75cc3f2168f2f2`, with refreshed origin parity.
The authorities are the
[R05 amendment](P02_R05_SEMANTIC_FACT_IDENTITY_AND_MULTI_INPUT_GEOMETRY_REQUEST_AMENDMENT.md)
and frozen
[A01 amendment](P02_R05_A01_COMPLIANCE_BASELINE_AND_RELATIONAL_VALIDATION_SCOPE_AMENDMENT.md).
The four existing production changes, three existing test-suite changes, and
new directional-set suite were audited and retained. No reset, restoration,
discard, or unrelated artifact inclusion was performed.

A01 governance remains unchanged. The implementation commit is the commit
introducing this closure artifact; its exact SHA and remote run IDs are
reported at publication. Remote success must refer to that final implementation
SHA, not to the earlier documentation-only A01 SHA.

## Exact additive contracts and compatibility

`SemanticFactIdentity(namespace, name, version)` is frozen, slotted, ordered,
hashable, and deterministic. All three fields use the existing exact text
validator; empty, whitespace-only, and non-string fields fail closed. No new
normalization policy, vocabulary, registry, metadata map, or validation
framework was introduced.

`SemanticCandidate.fact_identity: SemanticFactIdentity | None = None` is
appended after `role`. Both historical positional forms and keyword forms
remain valid. With `None`, the field is excluded from the candidate-ID and hash
projections, preserving the prior role-dependent exclusions. Historical
candidate equality, candidate IDs, hash projections, and ordering by candidate
ID remain unchanged. Golden IDs for all eight existing roles were measured
from an isolated archive of the unchanged A01 commit and asserted against the
resumed implementation.

A specified exact `SemanticFactIdentity` participates in candidate identity,
dataclass equality, and hash. Two otherwise identical values from the same
source and producer remain distinct when their facts differ. Tampering with a
fact while retaining the previous candidate ID fails closed.

`DirectionalCandidateSourceSetRequest` has exactly `context`, `candidates`,
`sources`, and `direction`, using the existing P02 and `StrategyDirection`
types. Both populations are exact non-empty tuples with exact immutable member
types. Duplicate candidate IDs and source binding IDs fail before sorting.

Every candidate and every source must match the context's instrument,
timeframe, source-binding membership, and provenance membership. Each candidate
must then resolve through its exact `source_binding_id` to one supplied source,
and its provenance must equal that precise source's provenance. Instrument and
timeframe equality with that source follow from their shared equality with the
context. Independent membership in context reference sets cannot admit a
candidate borrowing another source's provenance.

Construction validates exact types and non-empty populations, relies on the
existing immutable candidate/source identity construction boundaries, rejects
duplicates, validates context and precise-source relationships, and only then
sorts by `candidate_id` and `source_binding_id` and stores immutable tuples.
Tests replace the request module's sorting operation with a failure sentinel
to prove duplicate and invalid relationship paths reject before sorting.
Equivalent valid permutations produce equal requests and canonical JSON.

The producer identity remains distinct from the consuming invocation identity.
The request retains producer identities without inventing an allowlist or
requiring producer/consumer equality. Existing extraction authorization and
source/manifest validation remain at their frozen boundaries.

## Dispatch, serialization, and capability fit

The new request appears once in the existing closed request union and is
exported alongside the fact contract. Checked dispatch admits its exact type
only for `APPLICABILITY`, `BOUNDARY`, and `PRICE_TRANSFORMATION`. All ten other
invocation kinds reject it with zero implementation calls. Historical request
admissions and result checks retain their existing behavior.

The serializer framework is unchanged. Facts use tagged dataclass encoding;
historical candidate payloads missing the field reconstruct with `None`; new
default payloads emit explicit `null`. Fact-bearing candidates and canonical
directional requests round-trip through the existing serializer. Malformed
fact payloads and fact/ID tampering fail closed.

Generic fixtures demonstrate same-valued distinct facts, role-addressed start
and end anchors, multiple typed sources, and a typed Fibonacci snapshot
transported with both anchors. They introduce no P04 rule, Fibonacci
mathematics, W1 interpretation, trend/structure constants, or RR calculation.

## Compliance evolution authorized by A01

| State | Inventory | Canonical digest |
| --- | --- | --- |
| Pre-R05 | 610 | `522ea5bed864f02263ac38219ca3e8ff9bbd91f1905b842e42bb41c050c9e218` |
| Final R05 | 612 | `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1` |

Repeated authoritative scans reproduce the final digest. The only additions
are `epip.strategy_mapping.rule_values.SemanticFactIdentity` and
`epip.strategy_mapping.rule_requests.DirectionalCandidateSourceSetRequest`,
both in explicit-validation mode. Removing these two inventory entries
reproduces the previous count and digest.

`tests/core/test_integrity_compliance.py` changes only its `EXPECTED_DIGEST`
literal, exactly as A01 authorizes. Both tests and every assertion remain.
Scanner code, filtering, exclusions, ordering, and digest algorithm are
unchanged. The digest change is the authorized consequence of the two new
contracts, not a compliance exception.

## Exact 34-condition certification map

The following prefixes resolve to the four authorized suites under
`tests/strategy_mapping/`:

- `C`: `test_rule_execution_contracts.py`;
- `S`: `test_execution_serialization.py`;
- `D`: `test_directional_candidate_source_set.py`;
- `R`: `test_resolved_rules.py`.

Each row maps the original governed condition to an executed test. Parametrized
tests include every collected parameter node, not a selected example.

| Condition | Governed requirement | Executed test/node |
| --- | --- | --- |
| 01 | Historical candidate ID | `C::test_candidate_fact_identity_preserves_historical_semantics` (all eight roles and golden IDs) |
| 02 | Historical equality | `C::test_candidate_fact_identity_preserves_historical_semantics` |
| 03 | Historical hash | `C::test_candidate_fact_identity_preserves_historical_semantics` |
| 04 | Positional compatibility | `C::test_candidate_fact_identity_preserves_historical_semantics` (seven/eight historical arguments) |
| 05 | Keyword compatibility | `C::test_candidate_fact_identity_preserves_historical_semantics` |
| 06 | Omitted fact equals explicit None | `C::test_candidate_fact_identity_preserves_historical_semantics` |
| 07 | Default excluded from ID | `C::test_candidate_fact_identity_preserves_historical_semantics` (golden ID comparison) |
| 08 | Default excluded from hash | `C::test_candidate_fact_identity_preserves_historical_semantics` (historical tuple projection) |
| 09 | Specified fact changes ID | `C::test_candidate_fact_identity_separates_same_valued_facts` (default and two specified facts) |
| 10 | Specified fact changes equality | `C::test_candidate_fact_identity_separates_same_valued_facts` |
| 11 | Specified fact changes hash | `C::test_candidate_fact_identity_separates_same_valued_facts` |
| 12 | Same value/source/rule/role, different facts | `C::test_candidate_fact_identity_separates_same_valued_facts`; `D::test_same_value_different_fact_identities_are_distinct` |
| 13 | Duplicate complete fact-bearing candidate | `D::test_duplicate_candidate_and_source_identities_fail_closed` |
| 14 | Empty namespace rejected | `C::test_semantic_fact_identity_is_exact_immutable_and_validated` (empty, whitespace, wrong types) |
| 15 | Empty name rejected | `C::test_semantic_fact_identity_is_exact_immutable_and_validated` |
| 16 | Empty version rejected | `C::test_semantic_fact_identity_is_exact_immutable_and_validated` |
| 17 | Fact JSON round-trip | `S::test_fact_identity_and_candidates_use_canonical_tagged_serialization` |
| 18 | Historical payload without fact | `S::test_historical_candidate_payload_defaults_fact_without_identity_drift` |
| 19 | Default candidate round-trip and null | `S::test_fact_identity_and_candidates_use_canonical_tagged_serialization` |
| 20 | Fact-bearing candidate round-trip | `S::test_fact_identity_and_candidates_use_canonical_tagged_serialization` |
| 21 | Unknown/malformed fact rejected | `C::test_candidate_fact_identity_type_and_tampering_fail_closed`; `S::test_serialized_unknown_or_malformed_fact_fails_closed` |
| 22 | Fact-bearing ID tampering rejected | `C::test_candidate_fact_identity_type_and_tampering_fail_closed`; `S::test_serialized_fact_tampering_fails_closed` |
| 23 | One candidate and one source | `D::test_exact_shape_one_candidate_immutability_and_direction`; `D::test_populations_are_non_empty_exact_typed_tuples` |
| 24 | Two role-addressed anchors | `D::test_two_role_addressed_anchors_and_typed_fibonacci_source` |
| 25 | Canonical candidate permutations | `D::test_candidate_and_source_permutations_are_canonical` |
| 26 | Canonical source permutations | `D::test_candidate_and_source_permutations_are_canonical` |
| 27 | Duplicate candidate rejected before sorting | `D::test_duplicate_candidate_and_source_identities_fail_closed` (sorting sentinel) |
| 28 | Duplicate source rejected before sorting | `D::test_duplicate_candidate_and_source_identities_fail_closed` (sorting sentinel) |
| 29 | Distinct same-valued facts coexist | `D::test_same_value_different_fact_identities_are_distinct` |
| 30 | Missing precise source rejected | `D::test_candidate_must_reference_a_supplied_source` |
| 31 | Context/source/provenance continuity | `D::test_candidate_context_relationships_fail_closed`; `D::test_source_context_relationships_fail_closed`; `D::test_exact_source_provenance_is_validated_before_sorting`; `D::test_producer_identities_are_preserved_independently_of_consumer` |
| 32 | Canonical request round-trip | `D::test_exact_types_and_serialization_round_trip`; `D::test_candidate_and_source_permutations_are_canonical` |
| 33 | Three governed dispatch admissions | `R::test_directional_set_dispatch_is_admitted_for_exact_governed_kinds` (three nodes) |
| 34 | All other kinds rejected before invocation | `R::test_directional_set_dispatch_rejects_every_other_kind_before_invocation` (ten nodes, zero calls) |

Governed functional conditions: **34**. New pytest nodes: **53**. The four
focused suites collect and pass **85** nodes including predecessor regression.
The two unchanged-shape compliance tests are maintenance gates, not a 35th
functional condition.

## Executed regression and coverage evidence

The clean A01 archive collected 3074 nodes. Final R05 collection is 3127:
53 additions, zero removed predecessor nodes, verified by node-ID set comparison.

| Gate | Local result |
| --- | --- |
| Four focused R05 suites | 85 passed |
| Complete P02 strategy mapping | 325 passed |
| Complete P03 strategy runtime | 59 passed |
| Complete A07 | 571 passed |
| Frozen P04 profile/setup | 92 passed: 10 profile, 82 F01 setup |
| Relevant P02/P03 serialization | 22 passed: 11 execution, 9 source, 2 runtime |
| Resolved-rule suite | 18 passed |
| Structural applicability regressions | 39 passed: 8 singular, 31 set |
| Compliance suite | 2 passed |
| Combined P02/P03/A07/P04/compliance run | 1049 passed |
| Canonical full coverage run | 3127 collected, 3126 selected and passed, 1 deselected |
| Separate EventBus stress | 1 passed; 640,000 publications |
| Black | 694 files unchanged |
| Ruff | PASS |
| Strict MyPy | PASS; 694 source files |

The designated stress node is
`tests/core/test_eventbus_stress.py::test_640000_publications_are_lossless_unique_and_fifo`.
It is the sole deselection in the canonical coverage run and passes separately.
The full run uses `--cov=epip --cov-report=term-missing --cov-fail-under=95`;
the saved JSON report provides the precise figures below.

| Coverage scope | Covered statements | Coverage |
| --- | --- | --- |
| Aggregate | 25809 / 26512 | 97.3484% |
| `rule_values.py` | 129 / 133 | 96.9925% |
| `rule_requests.py` | 229 / 236 | 97.0339% |
| `resolved_rules.py` | 192 / 197 | 97.4619% |
| Package exports | 22 / 22 | 100% |

Intersecting changed production lines with the coverage report's missing lines
finds zero gaps. Remaining module gaps are unchanged predecessor paths. The
new fail-closed categories have directed tests: malformed fact/type, tampered
ID, empty/wrong population, duplicate identity, missing source, every context
dimension, precise-source provenance, and disallowed dispatch before invocation.
The canonical coverage gate measures statements, not a separate branch metric;
no claim of 100% repository branch coverage is made.

Local validation uses the existing Python 3.12.10 virtual environment with the
repository's Python 3.13 Black/MyPy targets. Black passes with its interpreter
version advisory. Exact-final-SHA remote Quality runs Python 3.13 and must pass
Black, Ruff, strict MyPy, coverage, and the separate stress gate before final
publication certification. No tooling configuration was weakened.

## Scope audit and closure gates

Production changes are limited to `epip/strategy_mapping/rule_values.py`,
`rule_requests.py`, `resolved_rules.py`, and `__init__.py`. Tests are limited to
the four mapped suites and the A01-authorized compliance literal update.
Documentation changes are limited to this artifact and `ROADMAP.md`.

The interrupted draft's precise-source provenance omission and premature sorts
are corrected. Strict typing of the conditional hash tuple and source lookup
is corrected without an `Any`, cast, or suppression in production. Existing
identity, dispatch, serializer, and predecessor request semantics are retained.

P03, A07, P04 production, all serializer frameworks, and the compliance scanner
have zero delta. Frozen F01 fingerprints, catalogs, five-rule executable closure,
32 future declarations, cardinalities, source requirements, and serialization
regressions pass unchanged. A07 E07 retains exclusive RR ownership.

Before publication, require `git diff --check`, Markdownlint on the tracked
publication files plus this artifact, and MkDocs strict. Unrelated untracked
historical documents and dependency caches remain preserved and excluded from
the commit and publication lint scope. Require selective staging of only the
authorized files, one atomic commit, normal push, refreshed HEAD/origin parity,
and exact-final-SHA Quality, CodeQL, and Documentation PASS. No release, tag,
version bump, force push, or successor implementation is authorized.

## Downstream program state

| Milestone | State |
| --- | --- |
| P02-R05-A01 | CLOSED / FROZEN |
| P02-R05 | CLOSED / FROZEN after exact-final-SHA gates |
| P04-F00 / P04-F01 | CLOSED / FROZEN |
| P03 / A07 | CLOSED / FROZEN |
| P04-F02 | READY FOR AUTHORIZATION REVIEW; implementation remains unauthorized |
| P04-F03 / P04-F04 | NOT AUTHORIZED |
| P05 | NOT AUTHORIZED |

R05 closes generic transport and semantic fact identity only. F02 still requires
its own governance and implementation authorization review, including remaining
business-policy decisions. No P04 or P05 rule is implemented by this closure.
