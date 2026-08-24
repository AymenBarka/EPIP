# A07 Execution Plan

Status: APPROVED FOR GOVERNANCE DELIVERY  
Baseline: A05-v1.0.0 / A06 v1.5.21  
Reserved release: v1.6.0  
Implementation authorization: E00 ready after this document is published

## 1. Mission and boundaries

A07 is the deterministic Strategy Engine. It consumes immutable analytical,
risk, temporal, and provenance facts and produces `BUY`, `SELL`, or `NO_TRADE`.

A07 does not acquire data, compute predecessor analytics, execute orders, access
MT5, backtest, optimize, walk forward, manage portfolios, or render dashboards.

## 2. Frozen contracts

- `StrategyDirection` is exactly `BUY`, `SELL`, `NO_TRADE`.
- `NO_TRADE` has `entry=None`, `stop=None`, `target=None`, and `rr=None`.
- Public outputs are immutable, deterministic, hashable, and reconstructable.
- Numeric domain is finite float with canonical decimal serialization and
  policy-defined precision; NaN and infinity fail closed.
- Hard-gate failures cannot be compensated by confidence.
- No wall-clock reads or broker precision lookup are permitted.

## 3. Package sequence and ownership

| Unit | Production file | Test file | Public outputs | Owns |
| --- | --- | --- | --- | --- |
| E00 | `epip/a07/foundation.py` | `tests/a07/test_foundation.py` | `StrategyIdentity`, `StrategyEvidenceIdentity`, `StrategyEvaluationRequest`, `StrategyDirection`, `StrategyFoundationDiagnostics` | identity and request foundation |
| E01 | `epip/a07/policy.py` | `tests/a07/test_policy.py` | `StrategyPolicyIdentity`, `StrategyPolicy`, `PolicyValidation`, `PolicyDiagnostics` | policy configuration and fingerprint |
| E02 | `epip/a07/evidence.py` | `tests/a07/test_evidence.py` | `StrategyEvidenceSnapshot`, `EvidenceBinding`, `EvidenceValidation`, `EvidenceDiagnostics` | immutable predecessor evidence binding |
| E03 | `epip/a07/direction.py` | `tests/a07/test_direction.py` | `DirectionalDecision`, `DirectionValidation`, `DirectionDiagnostics` | directional eligibility and NO_TRADE reasons |
| E04 | `epip/a07/entry.py` | `tests/a07/test_entry.py` | `EntryPrice`, `EntryValidation`, `EntryDiagnostics` | entry geometry only |
| E05 | `epip/a07/stop.py` | `tests/a07/test_stop.py` | `StopLoss`, `StopValidation`, `StopDiagnostics` | stop geometry only |
| E06 | `epip/a07/target.py` | `tests/a07/test_target.py` | `TakeProfit`, `TargetValidation`, `TargetDiagnostics` | target geometry only |
| E07 | `epip/a07/reward_risk.py` | `tests/a07/test_reward_risk.py` | `RewardRiskOutcome`, `RewardRiskValidation`, `RewardRiskDiagnostics` | RR and applicable risk acceptance |
| E08 | `epip/a07/confidence.py` | `tests/a07/test_confidence.py` | `StrategyConfidence`, `SignalExpiration`, `ConfidenceValidation`, `ConfidenceDiagnostics` | confidence, expiry, rationale inputs |
| E09 | `epip/a07/signal.py` | `tests/a07/test_signal.py` | `StrategySignal`, `SignalValidation`, `SignalDiagnostics` | integrated signal closure |

Only the listed files may be changed by each unit. No aliases, wildcard exports,
predecessor internals, or successor imports are allowed.

## 4. Dependency DAG

```text
E00 -> E01 -> E02 -> E03
                 |\
                 | +-> E04
                 | +-> E05
                 | +-> E06
E03 + E04 + E05 + E06 -> E07
E02 + E03 + E07 -> E08
E02 + E03 + E04 + E05 + E06 + E07 + E08 -> E09
```

E04, E05, and E06 are siblings and must not import one another.

## 5. Unit contracts

E00 validates identity, evidence identity, request shape, canonical timestamps,
baseline references, immutability, hashing, and reconstruction. It owns no strategy logic.

E01 validates policy identity, enabled directions, minimum RR/confidence, evidence
requirements, expiration, numeric policy, Elliott policy, and deterministic fingerprints.

E02 adapts only immutable predecessor snapshots. It preserves provenance, freshness,
temporal eligibility, mandatory/optional evidence, and A05/A06 continuity. It never recomputes analytics.

E03 resolves BUY/SELL/NO_TRADE from eligible Elliott, trend, structure, policy, and
MTF facts. Primary/alternate conflict is NO_TRADE. It owns no geometry.

E04 derives and validates supported entry geometry only.

E05 derives stops with precedence: Elliott invalidation, structure/swing, supported
volatility, explicit policy buffer. BUY stop is below entry; SELL stop is above entry.

E06 derives targets with precedence: Elliott projection, Fibonacci extension,
structure/liquidity, and policy-authorized RR fallback. It may not manufacture targets.

E07 validates finite positive risk/reward and `RR >= minimum_rr`, plus immutable risk acceptance.

E08 computes confidence in `[0,1]`, applies `confidence >= minimum_confidence`, derives
expiry from immutable evaluation time and policy, and never reads the wall clock.

E09 validates identity, policy, evidence, provenance, direction, geometry, RR, confidence,
expiry, and diagnostics without recomputation. BUY/SELL require complete geometry.

### 5.1 E01 normative policy contract

#### Purpose, ownership, files, and dependencies

E01 owns immutable strategy-policy configuration, its domain-qualified content fingerprint,
identity/reference validation, and policy diagnostics. Its only production and test files are
`epip/a07/policy.py` and `tests/a07/test_policy.py`. It may import the Python standard library,
`DataIntegrityError`, `MissingFieldError`, and `require_text` from `epip.core.integrity`, and
`StrategyDirection` and `StrategyIdentity` from E00. It must not import A05, A06, E02 or any later
A07 package. E00 remains frozen: E01 exposes a canonical string reference compatible with the
opaque `StrategyEvaluationRequest.policy_reference`; it does not change that field or retrofit an
E01 type into E00.

E01 exports exactly `StrategyPolicyIdentity`, `StrategyPolicy`, `PolicyValidation`, and
`PolicyDiagnostics`. Helpers and constants are private. All four objects are immutable, hashable,
compare by exact type and all declared fields, contain no mutable nested value, and are
reconstructable by passing their public fields to their documented constructor, except where the
constructor derives fields as specified below.

#### Common canonical rules

- Text inputs are required `str` values, stripped at both ends, and must remain non-empty.
  `policy_id` and `policy_version` additionally match ASCII
  `[A-Za-z0-9][A-Za-z0-9._-]*`; other text is preserved after stripping with no case folding.
- Tuple inputs must be actual tuples. Lists, sets, generators, mappings, and scalar substitutes are
  rejected. Every tuple member is validated before canonical ordering. Duplicate or conflicting
  members are rejected rather than collapsed.
- Numeric policy inputs must be actual `float` values; integers, booleans, `Decimal`, and strings
  are rejected. Values must be finite. Storage remains `float`, as required by the A07 frozen
  numeric domain. Canonical decimal text is obtained from `Decimal(str(value))`, with trailing
  fractional zeroes removed, no exponent, and negative zero represented as `0`. Thus `3.0`
  canonically fingerprints as `3`; integer `3` and string `"3.00"` are invalid inputs rather than
  alternative representations.
- Invalid construction raises the existing `MissingFieldError` for a missing/empty required value
  and `DataIntegrityError` for wrong type, malformed, duplicate, conflicting, non-finite,
  out-of-domain, or inconsistent content. No input is clamped, repaired, inferred, or defaulted.

#### `StrategyPolicyIdentity`

The exact fields, in constructor and equality order, are:

| Field | Type | Contract |
| --- | --- | --- |
| `policy_id` | `str` | Required canonical identifier text. |
| `policy_version` | `str` | Required canonical version label; it identifies declared policy evolution and is not parsed as SemVer. |
| `fingerprint` | `str` | Required lowercase 64-character hexadecimal SHA-256 content fingerprint. |

Its `reference` read-only property is exactly
`a07-policy:1:<policy_id>:<policy_version>:sha256:<fingerprint>`. Colons cannot occur in either
identifier because of the identifier grammar. Reconstruction from the three fields preserves
equality, hash, fingerprint, and reference. The identity alone validates fingerprint shape; binding
the fingerprint to content is enforced by `StrategyPolicy` construction. `StrategyPolicyIdentity`
does not duplicate or replace `StrategyIdentity`.

#### `StrategyPolicy`

The exact public fields, in canonical fingerprint and equality order, are:

| Field | Type | Required | Domain and canonical form |
| --- | --- | --- | --- |
| `identity` | `StrategyPolicyIdentity` | Derived | Constructed from caller `policy_id`, `policy_version`, and the content fingerprint below. A caller-supplied identity is not accepted. |
| `strategy_identity` | `StrategyIdentity` | Yes | Exact frozen E00 object; it binds the policy to one strategy identity and participates by `strategy_id`, then `strategy_version`. |
| `enabled_directions` | `tuple[StrategyDirection, ...]` | Yes | Non-empty subset of `BUY` and `SELL`; `NO_TRADE` is an outcome and is forbidden. Canonical order is E00 enum declaration order. Duplicates fail. |
| `minimum_rr` | `float` | Yes | Finite and strictly greater than zero; canonical decimal text participates in identity. |
| `minimum_confidence` | `float` | Yes | Finite inclusive range `0.0..1.0`; canonical decimal text participates in identity. |
| `required_evidence` | `tuple[str, ...]` | Yes | Opaque E02-owned evidence-kind identifiers; may be empty, canonical lexicographic order, unique. |
| `optional_evidence` | `tuple[str, ...]` | Yes | Opaque E02-owned evidence-kind identifiers; may be empty, canonical lexicographic order, unique and disjoint from `required_evidence`. |
| `expiration_seconds` | `int` | Yes | Positive integer seconds; booleans rejected. Expiration cannot be disabled. E01 stores duration only and never reads a clock or derives a timestamp. |
| `numeric_precision` | `int` | Yes | Non-negative integer number of decimal places used by later policy-authorized numeric serialization/rounding; booleans rejected. E01 performs no price geometry. |
| `elliott_policy` | `tuple[tuple[str, str], ...]` | Yes | Opaque caller-supplied Elliott configuration key/value text pairs; may be empty, ordered lexicographically by `(key, value)`, with unique keys. Duplicate keys, including equal pairs, fail. E01 assigns no analytical meaning or defaults. |

`policy_id` and `policy_version` are required constructor parameters used to derive `identity` but
are not duplicate `StrategyPolicy` fields. Changing either, the bound strategy identity, or any
configuration field changes the canonical fingerprint. Identical content under different declared
versions is therefore unequal and has a different reference. Any semantic policy change requires a
new `policy_version`; construction cannot detect dishonest reuse of a version label, but the changed
fingerprint prevents content identity reuse.

Evidence identifiers and Elliott keys/values use the common stripped non-empty text rule. E01
defines neither taxonomy nor interpretation for them. Empty evidence tuples mean that the policy
declares no requirements of that class. Empty `elliott_policy` means that it declares no additional
Elliott constraint. These empty states are explicit caller inputs, not defaults.

#### Fingerprint profile

The fingerprint owner is `StrategyPolicy`; its derived value is stored in
`StrategyPolicyIdentity.fingerprint`. The algorithm/profile is SHA-256/`sha256-v1`. Hash input is
UTF-8 encoding of canonical JSON produced with `ensure_ascii=True` and separators `(',', ':')`.
The JSON root is an array in exactly this order:

```text
[
  "a07-strategy-policy", "1", "epip-json-v1", "sha256-v1",
  policy_id, policy_version,
  [strategy_id, strategy_version],
  [enabled direction enum values],
  minimum_rr canonical decimal text,
  minimum_confidence canonical decimal text,
  [required evidence identifiers],
  [optional evidence identifiers],
  expiration_seconds,
  numeric_precision,
  [[Elliott key, Elliott value], ...]
]
```

All arrays use the canonical orders defined above. This schema has no optional fields and therefore
no null/absent encoding. Duplicate prevention occurs before hashing. Python `hash()` is used only
for in-process value-object hashing and never for the persistent fingerprint. A SHA-256 collision or
a supplied identity/content mismatch is a contract-integrity failure; E01 must not select a winner,
repair content, or issue an alternative reference.

#### `PolicyDiagnostics`

Its sole field is `diagnostics: tuple[str, ...]`. The tuple may be empty. Entries are stable code
strings, validated by the common text rule, canonically sorted lexicographically, and unique;
mutable containers, duplicates, malformed entries, and unknown codes fail closed. E01 defines
exactly one code: `POLICY_REFERENCE_MISMATCH`. Empty diagnostics means that the E01 identity check
found no mismatch; it is not evidence that later policy application accepted a trade.

#### `PolicyValidation`

`PolicyValidation` is an immutable validation-result value object, not a service and not policy
application. Its constructor accepts a `StrategyPolicy` and an opaque expected `policy_reference`
string. Its exact derived public fields, in equality order, are:

| Field | Type | Derivation |
| --- | --- | --- |
| `policy_reference` | `str` | Canonical `policy.identity.reference`. |
| `expected_policy_reference` | `str` | Required stripped caller reference, normally E00's opaque request field. |
| `valid` | `bool` | True exactly when the two reference strings are equal. |
| `diagnostics` | `PolicyDiagnostics` | Empty when valid; otherwise exactly `("POLICY_REFERENCE_MISMATCH",)`. |

Wrong object types or malformed expected references fail at construction. No caller may supply
`valid` or diagnostics, so an inconsistent result cannot be constructed through the public API.
Reconstruction repeats validation from a policy and `expected_policy_reference`; derived fields
must be identical. A false result diagnoses reference inconsistency only and does not evaluate
evidence, market state, eligibility, direction, geometry, RR, risk, confidence, or expiration.

#### Reconstruction, invariants, and forbidden state

`StrategyPolicy` reconstruction uses its identity's `policy_id` and `policy_version`, followed by
the remaining public configuration fields; it recomputes the fingerprint and must equal the
original identity or fail closed. Unknown keyword fields, missing fields, caller-supplied derived
fields, and malformed values fail. `PolicyDiagnostics` reconstructs from `diagnostics`.
`PolicyValidation` reconstructs from the original policy and `expected_policy_reference`. Every
round trip preserves equality and hash and, for policy objects, fingerprint and reference.

E01 invariants are valid non-empty identity text; exact E00 strategy binding; immutable values and
nested tuples; deterministic domain-separated fingerprinting; canonical decimal, direction,
evidence, Elliott, and diagnostic ordering; unique keys/items; disjoint required/optional evidence;
valid numeric domains; identity/content consistency; deterministic reconstruction; and complete
independence from wall clock, timezone, locale, random state, process state, filesystem, network,
environment variables, mutable registries, and caches.

E01 does not own runtime evidence binding, policy execution, strategy evaluation, direction or
signal-eligibility resolution, Elliott structure interpretation, Fibonacci geometry, liquidity
analysis, entry/stop/target geometry, risk or reward calculation, RR acceptance, confidence
calculation, live expiration calculation, signal construction or closure, execution, or broker/MT5
integration. Opaque configuration never authorizes E01 to import or reinterpret successor facts.

#### Required E01 tests and closure

The E01 test module must cover valid, invalid, canonical, equality, hashing, immutability, nested
immutability, and reconstruction behavior for every public object; identifier grammar; fingerprint
shape, exact canonical vector, content/version/strategy sensitivity, equivalent-float stability,
and external-state independence; all numeric boundaries plus NaN and infinities; direction
membership/order/empty/duplicate/`NO_TRADE` rejection; evidence ordering, emptiness, duplicates,
overlap, and wrong types; expiration and precision bounds with boolean rejection; Elliott ordering,
empty state, duplicate keys, and malformed pairs; deterministic diagnostics; reference match and
mismatch; missing, unknown, wrong-type, conflicting, and mutable inputs; E00 opaque-reference
compatibility; direct-import enforcement; and proof that no E02+ behavior exists. No exact test
count is prescribed.

E01 may close only after its authorized files alone are committed, all focused and predecessor/full
regressions pass, collection arithmetic reconciles, statement and branch coverage requirements
pass, Black/Ruff/MyPy and documentation checks pass, determinism/immutability/fail-closed and
successor-leakage audits pass, publication succeeds, and every applicable exact-SHA remote gate is
green. Closure authorizes no E02 work.

### 5.2 E02 normative evidence contract

#### Purpose, ownership, files, and dependencies

E02 is the deterministic adapter and binder of caller-supplied immutable evidence facts. It owns
canonical evidence-key binding, reconciliation of E01 required and optional keys, preservation of
E00 identity/provenance and supplied freshness/temporal facts, the immutable binding result,
validation result, and diagnostics. It never acquires evidence or computes predecessor facts.

Its only production and test files are `epip/a07/evidence.py` and
`tests/a07/test_evidence.py`. It exports exactly `StrategyEvidenceSnapshot`, `EvidenceBinding`,
`EvidenceValidation`, and `EvidenceDiagnostics`; helpers and constants remain private. Allowed
imports are the Python standard library; `StrategyIdentity` and `StrategyEvidenceIdentity` from
E00; `StrategyPolicy` from E01; and `DataIntegrityError`,
`MissingFieldError`, and `require_text` from `epip.core.integrity`. Direct A05/A06 imports are
forbidden: callers adapt their frozen facts into the E02 snapshot contract, and the opaque
`StrategyEvidenceIdentity.provenance` preserves their source continuity. E02 must not parse or
validate E01 policy references or recompute E01 fingerprints. These three types are the exact A07
predecessor objects E02 consumes; it does not consume `StrategyEvaluationRequest`,
`PolicyValidation`, or either predecessor diagnostics object. Policy-reference validation must
already have succeeded at the E01 boundary before E02 receives the policy.

E02 does not own market analysis, evidence acquisition, evidence taxonomy, strategy eligibility or
direction resolution, `NO_TRADE`, Elliott interpretation, Fibonacci or liquidity interpretation,
entry/stop/target geometry, risk or reward calculation, RR acceptance, confidence, live expiration
derivation, signal construction or closure, execution, or broker/MT5 behavior. It must not import
E03 or any later A07 package, analytical engines, providers, adapters, registries, or external-state
services.

#### Common value and error rules

All four public objects are immutable, hashable, use exact-type equality over every declared public
field in the documented order, contain only immutable nested state, and support deterministic
reconstruction. Runtime `hash()` is not persistent identity; E02 owns no persistent fingerprint or
digest.

Text uses E01 evidence-identifier semantics: an actual `str`, stripped at both ends, non-empty
after stripping, preserved without case folding or other normalization. This is the complete
evidence-key and provenance-text grammar; E02 does not narrow opaque E01 keys to a taxonomy.
Malformed type/shape/text, mutable containers, duplicate/conflicting evidence, or inconsistent
reconstruction are construction contract failures. Missing/empty required text raises
`MissingFieldError`; every other contract failure raises `DataIntegrityError`. Well-formed but
policy-unsatisfied evidence produces `EvidenceValidation(valid=False)` and diagnostics, not an
exception.

#### `StrategyEvidenceSnapshot`

The exact fields, constructor order, equality order, and reconstruction order are:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `strategy_identity` | `StrategyIdentity` | Yes | Exact frozen E00 type identifying the strategy to which this evidence fact is attributed. |
| `evidence_identity` | `StrategyEvidenceIdentity` | Yes | Exact frozen E00 identity; its `evidence_id` is the immutable evidence-instance identity and its `provenance` is the required opaque predecessor provenance reference. |
| `evidence_key` | `str` | Yes | Opaque canonical key matched exactly against E01 required/optional evidence identifiers. |
| `fresh` | `bool` | Yes | Actual bool supplied by the predecessor adapter; false means stale. |
| `temporally_eligible` | `bool` | Yes | Actual bool supplied by the predecessor adapter. |

No payload is stored: analytical content remains predecessor-owned and is neither required for
binding nor interpreted by E02. `strategy_identity` and `evidence_identity` must be exact types;
duck-typed replacements fail. Boolean fields reject integers and truthy coercion. Provenance is
preserved only through `evidence_identity.provenance`, whose frozen E00 construction already
requires canonical non-empty text; E02 neither duplicates nor recomputes it. Direct reconstruction
from the five public fields must preserve equality and hash.

#### Evidence key and available-evidence input

`EvidenceBinding` receives `available_evidence` as exactly
`tuple[StrategyEvidenceSnapshot, ...]`; an empty tuple is valid. Lists, mappings, sets, generators,
and wrong element types fail. Input permutations are canonicalized by ascending
`(evidence_key, evidence_identity.evidence_id, evidence_identity.provenance,
strategy_identity.strategy_id, strategy_identity.strategy_version)`. The additional values are
total-order safeguards only; duplicate/conflict checks occur first.

Within one binding input, each `evidence_key` and each complete `StrategyEvidenceIdentity` may occur
at most once. Repeating an equal snapshot is still a duplicate. Two snapshots sharing a key are a
key conflict regardless of their other fields. One evidence identity associated with two keys or
two semantic snapshots is an identity conflict. All such container-level duplicate/conflict states
raise `DataIntegrityError`; there is no first/last-wins rule and no diagnostic result is created.

#### Required, optional, and unexpected evidence

Keys match by exact canonical string equality. For every `StrategyPolicy.required_evidence` key,
exactly one matching snapshot is required. A required key is satisfied only when its snapshot is
present, has `strategy_identity == policy.strategy_identity`, `fresh is True`, and
`temporally_eligible is True`. Absence is well formed but unsatisfied and produces
`MISSING_REQUIRED_EVIDENCE`. A present stale required snapshot produces
`STALE_REQUIRED_EVIDENCE`; a present temporally ineligible required snapshot produces
`TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE`. A snapshot may produce both freshness and temporal
diagnostics. A well-formed strategy mismatch produces `STRATEGY_IDENTITY_MISMATCH`.

An optional key may be absent without diagnostic or validity impact. A present optional snapshot
is preserved and bound, but remains part of the validated contract: stale optional evidence
produces `STALE_OPTIONAL_EVIDENCE`, temporally ineligible optional evidence produces
`TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE`, and strategy mismatch produces
`STRATEGY_IDENTITY_MISMATCH`; each makes validation false. Malformed optional evidence is a
construction error, never silently ignored.

An unexpected snapshot has a key in neither policy tuple. It is preserved in the binding's
`unexpected_evidence`, produces `UNEXPECTED_EVIDENCE`, and makes validation false. E02 must not
silently discard, promote, reinterpret, or bind it. Because E01 guarantees disjoint required and
optional keys, a supplied nonconforming `StrategyPolicy` is impossible through the frozen public
E01 contract; E02 accepts only an exact `StrategyPolicy`.

#### `EvidenceBinding`

`EvidenceBinding` is the immutable canonical reconciliation result. Its public constructor accepts
exactly a `StrategyPolicy` and the available-evidence tuple. Its exact derived public fields, in
equality order, are:

| Field | Type | Derivation |
| --- | --- | --- |
| `policy` | `StrategyPolicy` | Exact frozen policy supplied to the constructor; it preserves policy identity, strategy identity, and authoritative required/optional configuration without duplication. |
| `available_evidence` | `tuple[StrategyEvidenceSnapshot, ...]` | Every supplied snapshot in canonical order. |
| `bound_required` | `tuple[StrategyEvidenceSnapshot, ...]` | Available snapshots whose keys occur in `policy.required_evidence`, ordered by evidence key. Presence does not imply freshness, temporal eligibility, or strategy compatibility. |
| `bound_optional` | `tuple[StrategyEvidenceSnapshot, ...]` | Available snapshots whose keys occur in `policy.optional_evidence`, ordered by evidence key. |
| `missing_required` | `tuple[str, ...]` | Required policy keys with no matching snapshot, in E01's canonical lexicographic order. |
| `unexpected_evidence` | `tuple[StrategyEvidenceSnapshot, ...]` | Available snapshots in neither policy collection, in canonical evidence order. |

Binding performs classification and preservation only; it does not decide validity or discard
invalid facts. Reconstruction uses a class method accepting all six public fields in their
documented order. It recomputes a binding from `policy` and `available_evidence`, requires every
supplied derived field to equal the recomputed field, and raises `DataIntegrityError` on
inconsistency. This preserves the complete frozen E01 policy as the authoritative source without
duplicating its configuration or trusting caller-supplied summaries.

#### `EvidenceDiagnostics`

Its sole field is `diagnostics: tuple[str, ...]`. The tuple may be empty, must be an actual tuple,
contains actual non-empty strings from exactly the frozen code set below, is lexicographically
sorted, and rejects duplicates and unknown codes:

- `MISSING_REQUIRED_EVIDENCE`: at least one required policy key has no snapshot.
- `STALE_REQUIRED_EVIDENCE`: at least one bound required snapshot has `fresh is False`.
- `STALE_OPTIONAL_EVIDENCE`: at least one bound optional snapshot has `fresh is False`.
- `TEMPORALLY_INELIGIBLE_REQUIRED_EVIDENCE`: at least one bound required snapshot has
  `temporally_eligible is False`.
- `TEMPORALLY_INELIGIBLE_OPTIONAL_EVIDENCE`: at least one bound optional snapshot has
  `temporally_eligible is False`.
- `STRATEGY_IDENTITY_MISMATCH`: at least one supplied snapshot's strategy identity differs from
  `binding.policy.strategy_identity`.
- `UNEXPECTED_EVIDENCE`: at least one unexpected snapshot is present.

Codes are aggregate deterministic conditions, not per-key messages; multiple distinct codes may
coexist, but each code occurs at most once. Duplicate/conflicting input is a construction error and
therefore has no diagnostic code. Empty diagnostics means all E02 binding conditions are satisfied;
it says nothing about E03+ eligibility or tradeability. Reconstruction directly from the tuple
revalidates and canonicalizes the codes.

#### `EvidenceValidation`

`EvidenceValidation` is an immutable derived result value object, not a service. Its constructor
accepts exactly one `EvidenceBinding`. Its public fields, in equality order, are:

| Field | Type | Derivation |
| --- | --- | --- |
| `binding` | `EvidenceBinding` | Exact validated binding, preserving complete E02 attribution. |
| `valid` | `bool` | True if and only if the derived diagnostics tuple is empty. |
| `diagnostics` | `EvidenceDiagnostics` | Canonical aggregate codes derived from the binding according to the rules above. |

Callers cannot supply `valid` or diagnostics to the public constructor. Validation inspects only
the binding's preserved identities and supplied boolean facts; it performs no lookup, policy
reference parsing, clock comparison, or analytics. Reconstruction accepts `binding`, `valid`, and
`diagnostics`, recomputes the latter two, and rejects any inconsistency with `DataIntegrityError`.

#### Canonicalization, reconstruction, and external state

Every E02 collection uses the canonical orders above. Equivalent permutations produce equal
bindings, hashes, validation results, and diagnostics. Snapshot reconstruction accepts its five
fields; binding and validation reconstruction recompute all derived facts; diagnostics
reconstruction accepts its sole tuple. Python signatures reject unknown or missing fields, and
wrong types fail through the declared integrity model. Every successful round trip preserves exact
value equality and runtime hash.

E02 behavior is independent of current time, `datetime.now()`, `time.time()`, timezone environment,
locale, filesystem, network, environment variables, randomness, process/hash iteration order,
mutable caches, and global registries. Freshness and temporal eligibility are supplied immutable
facts and never derived from timestamps. Evidence identity, provenance, policy identity, and
strategy identity are consumed and preserved without mutation or reinterpretation.

#### Required E02 tests and closure

The E02 test module must cover valid/invalid snapshot construction; exact predecessor types;
evidence-key and provenance preservation; strict booleans; equality, hash, immutability, nested
immutability, and reconstruction for all public objects; empty and permuted available tuples;
mutable/wrong containers and elements; canonical total ordering; duplicate equal snapshots, keys,
and identities; conflicts; fully satisfied and multiple-missing required keys; optional absence and
presence; required/optional separation; unexpected evidence; stale required and optional evidence;
temporally ineligible required and optional evidence; strategy mismatch; simultaneous diagnostic
conditions; known/unknown/duplicate diagnostics; derived-validity consistency; inconsistent
binding/validation reconstruction; unknown/missing/wrong reconstruction arguments; external-state
and repeated-construction determinism; E00/E01 compatibility; opaque A05/A06 continuity without
direct imports or recomputation; direct-import enforcement; and proof that no E03+ behavior exists.
No exact test count is prescribed.

E02 invariants are: consume and never recompute or mutate predecessor facts; opaque evidence keys;
tuple-only available evidence; no duplicate/conflicting evidence; deterministic required/optional
semantics; optional absence differs from required absence; malformed input is an exception while
well-formed policy dissatisfaction is a validation result; supplied freshness and temporal
eligibility; canonical ordering; frozen diagnostic codes; no silent precedence or last-write-wins;
no persistent E02 digest; and no successor semantics.

E02 may close only after its two authorized files alone are committed; focused, E00, E01, A05,
A06, and full regressions pass; collection arithmetic reconciles with no predecessor test removal;
coverage and static/documentation gates pass; determinism, immutability, fail-closed,
reconstruction, dependency, and successor-leakage audits pass; publication succeeds; and all
applicable exact-SHA remote gates are green. Closure authorizes no E03 work.

### 5.3 E03 normative direction contract

#### Purpose, ownership, files, and dependencies

E03 consumes frozen policy and evidence-validation results plus caller-supplied immutable
directional facts. It owns directional eligibility, deterministic `StrategyDirection` resolution,
`NO_TRADE` reasons, conflict handling, enabled-direction enforcement, validation, and E03
diagnostics. It does not bind evidence, recompute E02 validity or diagnostics, fingerprint or
reinterpret policy, or calculate any analytical fact.

Its only production and test files are `epip/a07/direction.py` and
`tests/a07/test_direction.py`. It exports exactly `DirectionalFacts`, `DirectionalDecision`,
`DirectionValidation`, and `DirectionDiagnostics`; helpers and constants remain private. Allowed
imports are the Python standard library; `StrategyDirection` from E00; `StrategyPolicy` from E01;
`EvidenceValidation` from E02; and `DataIntegrityError`, `MissingFieldError`, and `require_text`
from `epip.core.integrity`. E03 imports no A05, A06, E04+, analytical engine, market-data,
provider, filesystem, network, clock, environment, random, broker, or MT5 facility.

E03 does not detect or interpret Elliott waves; calculate trend, structure, or multi-timeframe
state; infer direction from evidence keys, provenance, policy names, or payloads; calculate
Fibonacci, liquidity, entry, stop, target, RR, confidence, or expiration; construct a final signal;
or execute a trade. E04 exclusively owns entry geometry. Later packages retain all other successor
responsibilities.

All four E03 objects are immutable and hashable, compare by exact type and every declared public
field in documented order, contain no mutable nested state, and own no persistent fingerprint or
digest. Malformed construction raises `MissingFieldError` for a missing required value where the
core primitive applies and `DataIntegrityError` for every other contract violation. Well-formed
negative domain conditions produce `NO_TRADE` and validation diagnostics, never an exception.

#### `DirectionalFacts`

`DirectionalFacts` is the sole normalized analytical input owned by E03. Every fact is supplied by
the caller; E03 never derives one. Its exact fields, constructor order, equality order, and
reconstruction order are:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `elliott_direction` | `StrategyDirection` | Yes | Direction already resolved by the authoritative Elliott producer. |
| `trend_direction` | `StrategyDirection` | Yes | Direction already resolved by the authoritative trend producer. |
| `structure_direction` | `StrategyDirection` | Yes | Direction already resolved by the authoritative structure producer. |
| `mtf_direction` | `StrategyDirection` | Yes | Direction already resolved by the authoritative multi-timeframe producer. |
| `primary_direction` | `StrategyDirection` | Yes | Direction of the caller-selected primary analytical hypothesis. |
| `alternate_direction` | `StrategyDirection` | Yes | Direction of the caller-supplied competing alternate hypothesis. |

Every value must be an exact frozen `StrategyDirection`; integers, strings, foreign enums, and
duck-typed values fail. All six fields are mandatory fixed named fields, so absence is malformed
construction rather than a domain result. `BUY` and `SELL` are affirmative facts.
`StrategyDirection.NO_TRADE` is the single neutral/unresolved analytical-fact representation; E03
defines no duplicate direction or neutral enum. A neutral fact is well formed but prevents
actionable consensus.

Primary means the direction of the analytical hypothesis selected by the caller as primary;
alternate means the direction of the competing hypothesis retained by the caller. E03 neither
selects nor ranks hypotheses. Both are required. They agree only when their exact enum values are
equal. Any difference, including directional versus neutral, is a primary/alternate conflict.

Direct reconstruction passes the six public fields to the constructor. Fixed fields require no
collection ordering. Reconstruction preserves equality and runtime hash.

#### Directional eligibility and resolution

E03 consumes exactly one `StrategyPolicy`, one `EvidenceValidation`, and one `DirectionalFacts`.
The evidence validation's `binding.policy` must equal the supplied policy. A mismatch is malformed
cross-predecessor state and raises `DataIntegrityError`; it is not `NO_TRADE`. E03 consumes
`EvidenceValidation.valid` as a frozen fact and never recomputes binding conditions or propagates
individual E02 diagnostic codes.

Define `facts` as the ordered six-tuple of `DirectionalFacts` values in documented field order.
Define actionable consensus for direction `D` exactly as:

```text
D is BUY or SELL
and every member of facts is D
```

There is no majority vote, weighting, advisory fact, analytical precedence, or pairwise override.
All six facts are mandatory confirmations. Structure does not override trend, Elliott does not
override MTF, and primary does not override alternate.

The exact BUY predicate is:

```text
evidence_validation.valid is True
and every member of facts is StrategyDirection.BUY
and StrategyDirection.BUY is in policy.enabled_directions
```

The exact SELL predicate is:

```text
evidence_validation.valid is True
and every member of facts is StrategyDirection.SELL
and StrategyDirection.SELL is in policy.enabled_directions
```

BUY and SELL are symmetrical independent predicates; SELL is not inferred from failure of BUY.
The result is `NO_TRADE` if and only if neither exact actionable predicate is true. Consequently,
the complete `NO_TRADE` trigger set is: invalid E02 evidence validation; at least one neutral fact;
any disagreement among the six facts; primary/alternate conflict; or unanimous BUY/SELL consensus
whose direction is disabled by policy. These triggers may coexist. Malformed structure is never a
`NO_TRADE` trigger.

Directional conflict is deterministic. `PRIMARY_ALTERNATE_CONFLICT` applies whenever the two
hypothesis fields differ. `DIRECTIONAL_CONFLICT` applies whenever both BUY and SELL occur anywhere
in the six facts. `NO_DIRECTIONAL_CONSENSUS` applies whenever the six facts are not unanimously
the same actionable direction, including all-neutral, mixed-neutral, and conflicting states.
Neutral versus directional state is lack of consensus rather than directional precedence.

#### `DirectionalDecision`

The exact fields, in equality order, are:

| Field | Type | Ownership |
| --- | --- | --- |
| `policy` | `StrategyPolicy` | Caller supplied; exact frozen E01 object. |
| `evidence_validation` | `EvidenceValidation` | Caller supplied; exact frozen E02 object. |
| `directional_facts` | `DirectionalFacts` | Caller supplied; exact E03 fact object. |
| `direction` | `StrategyDirection` | Derived by the exact predicates above. |

The public constructor accepts only the first three fields and derives `direction`. Exact runtime
types are required. Reconstruction accepts all four public fields, reconstructs from the three
caller fields, and rejects a supplied direction that differs from the recomputed direction with
`DataIntegrityError`. No decision diagnostics are stored; validation owns diagnostics.

#### `DirectionDiagnostics`

Its sole field is `diagnostics: tuple[str, ...]`. The tuple may be empty, must be an actual tuple,
contains exact non-empty strings, is lexicographically sorted, and rejects duplicates and unknown
codes. E03 defines exactly:

- `DIRECTIONAL_CONFLICT`: both BUY and SELL occur among the six directional facts.
- `DIRECTION_DISABLED_BY_POLICY`: the facts unanimously resolve BUY or SELL, but that direction is
  absent from `policy.enabled_directions`.
- `EVIDENCE_INVALID`: the frozen `EvidenceValidation.valid` value is false.
- `NO_DIRECTIONAL_CONSENSUS`: the facts are not unanimously one actionable direction.
- `PRIMARY_ALTERNATE_CONFLICT`: primary and alternate directions differ.

Codes are aggregate conditions and each occurs at most once. Every applicable code is emitted; no
short-circuit or diagnostic precedence suppresses another code. E03 summarizes invalid evidence
only as `EVIDENCE_INVALID` and never embeds or re-exports E02 diagnostic codes. Empty diagnostics
means the decision is an enabled BUY or SELL with valid evidence and complete consensus.
Reconstruction directly from the tuple revalidates and canonicalizes it.

#### `DirectionValidation`

Its exact derived public fields, in equality order, are:

| Field | Type | Derivation |
| --- | --- | --- |
| `decision` | `DirectionalDecision` | Exact caller-supplied E03 decision. |
| `valid` | `bool` | True exactly when derived E03 diagnostics are empty. |
| `diagnostics` | `DirectionDiagnostics` | All aggregate conditions derived from the decision. |

The public constructor accepts only `decision`. Here `valid` means directionally actionable: valid
evidence, unanimous non-neutral facts, policy-enabled resolution, and therefore direction BUY or
SELL. Every `NO_TRADE` decision is a well-formed domain outcome with `valid is False`; it is not
structural corruption. BUY and SELL decisions have `valid is True`. Reconstruction accepts all
three public fields, recomputes validity and diagnostics from the decision, and rejects any
contradiction with `DataIntegrityError`.

#### Error classification, reconstruction, and determinism

Wrong policy, evidence-validation, decision, fact, enum, tuple, or diagnostic types; missing or
unknown fields; unknown or duplicate diagnostics; predecessor policy mismatch; and contradictory
reconstruction are construction failures. They are never caught and converted to `NO_TRADE`.
Invalid predecessor evidence, neutral facts, disagreement, primary/alternate conflict, and a
policy-disabled consensus are well-formed negative domain outcomes.

Python signatures reject missing and unexpected reconstruction fields. Every derived field is
recomputed, every supplied derived field is verified, and every successful round trip preserves
exact equality, hash, canonical diagnostics, and direction. Diagnostics are the only collection
and use lexicographic order; input facts have fixed semantic field order. Equivalent reconstructed
predecessors and repeated construction produce identical results.

E03 behavior is independent of wall clock, timezone, locale, filesystem, network, environment,
randomness, process identity, unordered iteration, mutable registries, and caches. The same
semantic inputs always produce the same direction, validation, diagnostics, equality, hash, and
reconstruction result.

#### Required E03 tests and closure

The future E03 test module must cover every public field and exact type; valid BUY and SELL;
invalid E02 evidence; BUY and SELL disabled independently; each neutral fact position; all-neutral
facts; every BUY/SELL disagreement position; primary/alternate conflict including neutral versus
directional; simultaneous diagnostic reasons; the absence of majority voting and analytical
precedence; exact diagnostic triggers, ordering, duplicates, unknown codes, and empty state;
malformed input versus domain outcomes; policy/evidence cross-predecessor mismatch; equality,
exact-type inequality, hashing, immutability, nested immutability, reconstruction, contradictory
reconstruction, missing and unexpected arguments, repeated execution, external-state
independence, E00/E01/E02 compatibility, direct-import enforcement, and proof of no E04+ behavior.
No exact test count is prescribed.

E03 may close only after its two authorized files alone are committed; focused, E00, E01, E02,
A05, A06, collection, full-regression, coverage, static, determinism, immutability, fail-closed,
reconstruction, ownership, and successor-isolation gates pass; publication succeeds; and every
applicable exact-SHA remote gate is green. E03 closure authorizes no E04 implementation.

### 5.4 E04 normative entry contract

#### Purpose, ownership, files, and dependencies

E04 converts one caller-authorized immutable price zone into one canonical executable entry price.
It owns entry-fact validation, policy-precision normalization, direction-sensitive boundary
selection, entry integrity validation, and E04 diagnostics. It does not discover a zone, optimize
an entry, or inspect analytical payloads, current price, stop, target, risk, reward, RR,
`minimum_rr`, confidence, expiration, or execution state.

Its only production and test files are `epip/a07/entry.py` and `tests/a07/test_entry.py`. It exports
exactly `EntryFacts`, `EntryPrice`, `EntryValidation`, and `EntryDiagnostics`; helpers and constants
remain private. Allowed imports are Python standard-library decimal, finite-number, dataclass, and
typing facilities; `StrategyDirection` from E00; `DirectionValidation` from E03; and
`DataIntegrityError` from `epip.core.integrity`. E04 obtains the frozen `StrategyPolicy`, including
`numeric_precision`, through `direction_validation.decision.policy`; it neither accepts a second
policy argument nor directly imports E01. It does not import E02, A05, A06, E05+, analytical
engines, providers, market data, filesystem, network, clock, environment, random, broker, MT5, or
execution facilities.

All four public objects are immutable and hashable, compare by exact type and all declared public
fields in documented order, contain no mutable nested state, and own no persistent fingerprint or
digest. Wrong types, malformed prices, invalid predecessor state, impossible zones, precision
collapse, or contradictory reconstruction raise `DataIntegrityError`. E04 performs no exception
fallback and never represents an executable entry with a sentinel value.

#### Numeric model and normalization

Every caller price must have exact runtime type `float`; booleans, integers, `Decimal`, strings,
and foreign numeric types fail. Values must be finite and strictly greater than zero. `EntryFacts`
stores the validated caller floats unchanged; it has no policy or precision input.

Entry derivation converts each raw bound through `Decimal(str(value))`, then quantizes it to
`Decimal(1).scaleb(-numeric_precision)` with `ROUND_HALF_EVEN`. The quantized value is converted
back to built-in `float`. A zero result, including a negative zero, is canonicalized to positive
`0.0`; because executable prices must remain strictly positive, normalization to zero raises
`DataIntegrityError`. Normalization occurs before zone comparison, boundary selection, derived
price equality, and entry validation.

The raw and normalized bounds must both satisfy lower less than or equal to upper. If distinct raw
bounds normalize to the same value, construction raises `DataIntegrityError` for precision
collapse. Equal raw bounds are explicitly supported and produce one equal normalized boundary.
No tick size, broker precision, locale, or binary-float rounding operation participates.

#### `EntryFacts`

The exact fields, constructor order, equality order, and reconstruction order are:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `zone_lower` | `float` | Yes | Caller-supplied finite positive lower price bound. |
| `zone_upper` | `float` | Yes | Caller-supplied finite positive upper price bound. |

Both fields are caller supplied and stored without rounding. `zone_lower <= zone_upper` is required
at construction; reversed raw bounds are malformed rather than a domain-negative result. The zone
is already authorized by upstream analysis. E04 assigns no Elliott, Fibonacci, trend, structure,
MTF, liquidity, confidence, or RR meaning to it. Exactly one zone is accepted per evaluation; E04
has no candidate collection, ranking, selection, weighting, or permutation semantics.

Direct reconstruction passes both public fields to the constructor and preserves exact equality
and runtime hash. Missing and unexpected arguments fail through the Python signature.

#### `EntryPrice`

The exact fields, in constructor, equality, and public representation order, are:

| Field | Type | Ownership |
| --- | --- | --- |
| `direction_validation` | `DirectionValidation` | Caller supplied; exact frozen E03 object. |
| `entry_facts` | `EntryFacts` | Caller supplied; exact E04 raw fact object. |
| `price` | `float` | Derived canonical executable entry price. |

The public constructor accepts only `direction_validation` and `entry_facts`. Both must be exact
types. The predecessor must have `valid is True`, empty E03 diagnostics, and a decision direction
of exactly BUY or SELL. Any internally contradictory E03 object is impossible through its frozen
public contract; a well-formed invalid validation or `NO_TRADE` direction is rejected with
`DataIntegrityError` because `EntryPrice` represents executable geometry only.

After normalizing and validating both bounds with the predecessor policy's `numeric_precision`,
the exact formulas are:

```text
BUY  price = normalized zone_upper
SELL price = normalized zone_lower
```

This is the first executable boundary of the already-authorized zone in resolved trade direction.
E04 does not use current market price, optimize the entry, calculate Fibonacci, select by RR, or
inspect stop or target. No other BUY or SELL formula exists.

Reconstruction accepts `direction_validation`, `entry_facts`, and `price`. It requires exact float
type for the supplied price, reconstructs from the first two fields, and requires supplied price
to equal the recomputed canonical float exactly. Non-finite, non-positive, noncanonical, or
contradictory supplied prices raise `DataIntegrityError`.

#### `EntryDiagnostics` and `EntryValidation`

`EntryDiagnostics` has the sole field `diagnostics: tuple[str, ...]`. The E04 diagnostic code set
is intentionally empty because all E04-owned invalid states prevent construction of executable
entry geometry. Therefore only the empty tuple is valid. The input must be an actual tuple;
non-empty tuples, unknown strings, duplicates, malformed members, and mutable containers raise
`DataIntegrityError`. The stored tuple is immutable and already in its sole canonical order.
Direct reconstruction from the empty tuple preserves equality and hash.

`EntryValidation` is the immutable integrity validation of a successfully constructed canonical
entry, not final trade eligibility and not a domain-rejection service. Its exact derived public
fields, in equality order, are:

| Field | Type | Derivation |
| --- | --- | --- |
| `entry` | `EntryPrice` | Exact caller-supplied executable entry. |
| `valid` | `bool` | Always true for a successfully constructed exact `EntryPrice`. |
| `diagnostics` | `EntryDiagnostics` | Always the canonical empty diagnostics object. |

The public constructor accepts only `entry`; wrong types raise `DataIntegrityError`. It validates
that the entry equals a fresh canonical reconstruction from its predecessor and facts, without
recomputing E03 direction or upstream analytics. Reconstruction accepts all three public fields,
recomputes `valid` and diagnostics, and rejects wrong types or contradictions. A `NO_TRADE` or
invalid-E03 domain outcome has no `EntryPrice` and therefore no `EntryValidation`; callers retain
the predecessor result rather than manufacture empty or zero geometry.

#### Error classification, determinism, and successor isolation

Wrong public/predecessor types; missing or unexpected arguments; mutable diagnostic containers;
wrong price types; non-finite, non-positive, reversed, zero-normalized, or precision-collapsed
bounds; non-actionable E03 validation; unknown or duplicate diagnostics; and contradictory
reconstruction are structural contract failures raising `DataIntegrityError`. There are no
E04-owned well-formed negative entry states after an executable `EntryPrice` exists, so E04 has no
non-empty diagnostic result. Predecessor `NO_TRADE` remains a well-formed E03 result but is an
invalid input to the executable E04 object.

Same reconstructed predecessor, raw facts, and policy precision always produce exactly the same
normalized bounds, price, validation, diagnostics, equality, hash, and reconstruction. Behavior is
independent of clock, timezone, locale, environment, filesystem, network, market provider, broker,
MT5, randomness, process state, mutable registry, and cache.

Fibonacci, Elliott, trend, structure, MTF, liquidity, or other upstream analysis may produce the
authorized zone, but E04 receives only `EntryFacts` and performs none of those calculations. E05
owns stop geometry; E06 owns target geometry; E07 owns risk, reward, RR, and `minimum_rr`
acceptance; E08 owns confidence and expiration; E09 owns final signal assembly, validation, and
closure. E04 exposes none of their fields and imports none of their packages.

#### Required E04 tests and closure

The future E04 test module must cover exact public fields, runtime types, exports, BUY and SELL
boundary selection, equal bounds, reversed bounds, positive-price enforcement, booleans, integers,
strings, `Decimal`, NaN, both infinities, precision zero and positive precision, exact half-even
ties, normalization to positive zero and its rejection, raw-equal versus precision-collapsed
bounds, actionable and invalid E03 validations, `NO_TRADE`, wrong predecessor and fact types,
empty diagnostics, every forbidden non-empty diagnostic input, equality, exact-type inequality,
hashing, immutability, nested immutability, reconstruction, contradictory/noncanonical price and
validation reconstruction, missing and unexpected arguments, repeated execution, timezone,
locale, environment, filesystem, network and randomness independence, E00-E03 compatibility,
direct-import enforcement, one-zone-only behavior, and proof of no Fibonacci, stop, target, RR,
`minimum_rr`, confidence, expiration, signal, execution, E05+, broker, or MT5 behavior. No exact
test count is prescribed.

The canonical pre-E04 baseline is 2322. A future implementation reports its actual E04 collected
contribution and requires post-E04 collection to equal `2322 + contribution`, with no predecessor
node removal. E04 may close only after its authorized files alone are committed; focused,
predecessor, collection, full-regression, coverage, static, determinism, immutability, fail-closed,
reconstruction, ownership, and successor-isolation gates pass; publication succeeds; and every
applicable exact-SHA remote gate is green. E04 closure authorizes no E05 implementation.

### 5.5 E05 normative stop contract

#### Purpose, ownership, files, and dependencies

E05 converts one caller-authorized immutable invalidation price into one canonical executable stop
price and verifies its strict directional relationship to the frozen E04 entry. It owns stop-fact
validation, policy-precision normalization, stop-side validation, stop integrity validation, and
E05 diagnostics. It does not discover invalidation, choose among candidates, or calculate entry,
target, risk, reward, RR, `minimum_rr` acceptance, confidence, expiration, signals, or execution.

Its only production and test files are `epip/a07/stop.py` and `tests/a07/test_stop.py`. It exports
exactly `StopFacts`, `StopLoss`, `StopValidation`, and `StopDiagnostics`; helpers and constants
remain private. Allowed imports are Python standard-library decimal, finite-number, dataclass, and
typing facilities; `StrategyDirection` from E00; `EntryValidation` from E04; and
`DataIntegrityError` from `epip.core.integrity`. E05 reaches direction and
`policy.numeric_precision` only through the frozen entry-validation chain. It imports no E01-E03
type directly, no A05/A06, no E06+, and no analytical engine, market data, provider, filesystem,
network, clock, environment, random, broker, MT5, or execution facility.

All four public objects are immutable and hashable, compare by exact type and every declared
public field in documented order, contain no mutable nested state, and own no persistent
fingerprint or digest. Wrong types, malformed prices, non-actionable predecessors, invalid stop
geometry, or contradictory reconstruction raise `DataIntegrityError`; none becomes a sentinel or
diagnostic fallback.

#### Invalidation source and `StopFacts`

E05 accepts exactly one final invalidation price per evaluation. Upstream authority has already
selected it and incorporated any authorized Elliott invalidation, structure/swing invalidation,
supported volatility adjustment, or buffer. E05 does not receive those as alternatives, expose
their taxonomy, reproduce their precedence, or apply another offset. The broad precedence in the
unit summary describes upstream selection before this boundary, not E05 candidate selection.

`StopFacts` has exactly one caller-supplied public field:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `invalidation_price` | `float` | Yes | Final upstream-authorized raw stop/invalidation price, with every analytical adjustment already applied. |

The value must have exact runtime type `float`, be finite, and be strictly greater than zero.
Booleans, integers, strings, `Decimal`, foreign numeric wrappers, NaN, infinities, zero, and
negative values fail. It is stored unchanged; `StopFacts` has no policy or precision input.
Direct reconstruction passes the public field to the constructor and preserves equality and hash.

There is no candidate collection, precedence algorithm, tie, duplicate, missing-candidate, or
conflict state inside E05. A caller that has no authorized invalidation price cannot construct
`StopFacts`. Multiple-candidate ranking, nearest/widest stop selection, RR optimization, and market
optimization remain upstream or unsupported.

E01 contains no stop-buffer field and is not modified. Any fixed, volatility, ATR, spread, swing,
structure, Elliott, or policy-authorized buffer must already be reflected in
`invalidation_price`. E05 calculates no ATR, volatility, Fibonacci, wave rule, swing, structure,
spread, tick offset, or broker stop level.

#### Numeric normalization and directional geometry

E05 uses the exact E04 numeric profile. It converts the raw invalidation price through
`Decimal(str(value))`, quantizes to `Decimal(1).scaleb(-numeric_precision)` using
`ROUND_HALF_EVEN`, converts the result to built-in `float`, and canonicalizes negative zero to
positive `0.0`. The canonical stop must remain finite and strictly positive; normalization to zero
raises `DataIntegrityError`.

Normalization occurs before storage, comparison with the canonical entry, reconstruction
verification, equality of the derived stop, and validation. The canonical entry is already
normalized by E04 and is not renormalized or recomputed.

The exact stop formula for both actionable directions is:

```text
stop price = normalized StopFacts.invalidation_price
```

For BUY, the resulting stop must satisfy `stop price < entry price`. For SELL, it must satisfy
`stop price > entry price`. Equality and the wrong side raise `DataIntegrityError`. If raw entry
and stop are distinct but precision makes their canonical prices equal, this is precision collapse
and raises `DataIntegrityError`. There is no minimum distance beyond strict canonical separation.
E05 does not enforce pip, tick, ATR, spread, exchange, or broker minimums.

E05 may compare prices to establish the strict relationship but exposes no distance field and owns
no public risk semantic. E07 later derives risk from frozen geometry. E05 neither calculates nor
stores entry-minus-stop, stop-minus-entry, monetary risk, reward, or ratio.

#### Predecessor contract and `StopLoss`

E05 consumes exactly one `EntryValidation`, not a separate entry, direction, or policy. The exact
predecessor must have `valid is True`, empty E04 diagnostics, and a canonical `EntryPrice`. Its
direction, entry price, and precision are reached respectively through:

```text
entry_validation.entry.direction_validation.decision.direction
entry_validation.entry.price
entry_validation.entry.direction_validation.decision.policy.numeric_precision
```

Only BUY and SELL are actionable. Wrong predecessor types, invalid validations, or a `NO_TRADE`
chain raise `DataIntegrityError`. E05 never recomputes E03 direction or E04 entry.

`StopLoss` has the exact public fields, in equality order:

| Field | Type | Ownership |
| --- | --- | --- |
| `entry_validation` | `EntryValidation` | Caller supplied; exact frozen E04 object. |
| `stop_facts` | `StopFacts` | Caller supplied; exact E05 raw fact object. |
| `price` | `float` | Derived normalized stop price. |

The public constructor accepts only `entry_validation` and `stop_facts`, validates the predecessor,
normalizes the invalidation price, enforces the exact directional inequality, and stores the
canonical price. Reconstruction accepts all three public fields, requires exact float type for the
supplied price, recomputes from the first two, and requires exact equality with the canonical
derived price. Noncanonical or contradictory price raises `DataIntegrityError`.

#### `StopDiagnostics` and `StopValidation`

`StopDiagnostics` has the sole field `diagnostics: tuple[str, ...]`. Its closed E05 vocabulary is
intentionally empty because every E05-invalid state prevents construction of executable stop
geometry. Only the empty tuple is valid. The input must be an actual tuple; mutable containers,
non-empty tuples, unknown or malformed members, and duplicates raise `DataIntegrityError`. Direct
reconstruction from `()` preserves equality and hash.

`StopValidation` is immutable canonical-geometry integrity validation, not risk acceptance. Its
exact derived public fields, in equality order, are:

| Field | Type | Derivation |
| --- | --- | --- |
| `stop` | `StopLoss` | Exact caller-supplied canonical executable stop. |
| `valid` | `bool` | Always true for a successfully constructed canonical `StopLoss`. |
| `diagnostics` | `StopDiagnostics` | Always the canonical empty diagnostics object. |

The public constructor accepts only `stop`, requires its exact type, and verifies it equals a fresh
canonical reconstruction from its predecessor and facts. Reconstruction accepts all three public
fields, recomputes `valid` and diagnostics, and rejects wrong types or contradictions. Invalid
stop geometry has no `StopLoss` and therefore no `StopValidation`.

#### Error model, determinism, successor isolation, and future tests

Wrong predecessor/fact/public types; missing or unexpected arguments; wrong numeric types;
non-finite, zero, negative, equal-to-entry, wrong-side, or precision-collapsed stop prices;
non-actionable predecessors; absent/multiple/conflicting candidate representations; non-empty or
mutable diagnostics; and contradictory reconstruction are structural failures raising
`DataIntegrityError`. RR below policy minimum is not an E05 error or diagnostic; it is E07-owned.

The same reconstructed entry validation, raw stop fact, and frozen policy precision always produce
the same stop, validation, diagnostics, equality, hash, and reconstruction. Behavior is independent
of current price, clock, timezone, locale, environment, filesystem, network, provider, broker,
spread, MT5, randomness, process state, registry, and cache.

E06 owns target geometry. E07 owns risk, reward, RR, and `minimum_rr` acceptance. E08 owns
confidence and expiration. E09 owns signal assembly, validation, and closure. E05 calculates or
validates none of those and exposes no successor-derived field.

Future E05 tests must cover exact public fields, types, and exports; valid BUY and SELL stops;
strict side inequalities; equality and both wrong-side cases; exact float enforcement; zero,
negative, NaN, and both infinities; precision zero, positive precision, half-even ties, negative
zero/normalization-to-zero, and entry/stop precision collapse; valid and malformed/non-actionable
predecessors; wrong fact types; missing/unexpected arguments; empty diagnostics and every forbidden
non-empty/mutable input; equality, exact-type inequality, hashing, immutability, nested
immutability, reconstruction, contradictory/noncanonical reconstruction, repeated execution,
external-state independence, E04 compatibility, direct-import enforcement, one-fact-only behavior,
and proof of no ATR, buffer calculation, target, risk, reward, RR, `minimum_rr`, confidence,
expiration, signal, execution, E06+, broker, or MT5 behavior. No exact test count is prescribed.

The canonical pre-E05 baseline is 2368. A future implementation requires post-E05 collection to
equal `2368 + actual E05 contribution`, with no predecessor node removal. E05 may close only after
its authorized files alone are committed; focused, predecessor, collection, full-regression,
coverage, static, determinism, immutability, fail-closed, reconstruction, ownership, and successor-
isolation gates pass; publication succeeds; and every applicable exact-SHA remote gate is green.
E05 closure authorizes no E06 implementation.

## 6. Hard gates and diagnostics

Hard gates are: identity, provenance, policy, temporal eligibility, freshness, direction
permission, Elliott validity/tradeability, structure compatibility, MTF compatibility,
entry, stop, target, RR, risk acceptance, and confidence threshold.

Contract corruption is a contract failure. A valid but non-tradeable market setup is
`NO_TRADE`. Canonical reasons include missing evidence, stale evidence, temporal ineligibility,
identity mismatch, context conflict, invalid wave, trend/MTF conflict, invalid geometry,
low RR, risk rejection, insufficient confidence, and policy rejection.

## 7. Required tests and baselines

Each unit requires positive, negative, boundary, immutable, hash/equality, deterministic
reconstruction, permutation, provenance, and fail-closed tests. Required invariants include:

- BUY: `stop < entry < target`;
- SELL: `target < entry < stop`;
- positive risk and reward;
- NO_TRADE has no executable geometry;
- invalid evidence never produces BUY/SELL.

Baseline accounting is explicit: historical A06 evidence is 2075 tests; independent
reconstruction of the exact PRE-E00 commit `ec4054437bd21decdac341ad9ca65e49d1036c99`
establishes the current PRE-A07 full tracked baseline as 2075. Canonical collection uses
pytest `--import-mode=importlib`; no predecessor tests were lost. Every unit reports
pre-package baseline, package contribution,
post-package baseline, and current full baseline.

## 8. Quality and remote gates

Every unit requires Black, Ruff, MyPy strict, component tests, A05 regression, A06 regression,
full tracked regression, statement and branch coverage, `git diff --check`, and documentation
validation where applicable. Required remote workflows are Quality, CodeQL, and Documentation.

## 9. Git, publication, and freeze

Use one atomic commit per package with subjects:

```text
feat(a07): establish E00 strategy foundation
feat(a07): establish E01 strategy policy
feat(a07): bind E02 strategy evidence
feat(a07): establish E03 directional decision
feat(a07): derive E04 entry geometry
feat(a07): derive E05 stop geometry
feat(a07): derive E06 target geometry
feat(a07): establish E07 reward risk
feat(a07): establish E08 confidence and expiration
feat(a07): complete E09 strategy signal
```

After local validation, commit, push to `origin/develop`, verify exact-SHA remote gates,
then mark the unit CLOSED/FROZEN. Frozen predecessors cannot be silently modified.

## 10. Release model

`v1.6.0` remains RESERVED during implementation. No tag or release document is created now.
The release may be prepared only after E00–E09 are CLOSED/FROZEN, full regression, coverage,
Quality, CodeQL, Documentation, clean synchronization, and final closure review all pass.

## 11. Governance acceptance

```gherkin
Feature: package ownership
  Scenario: unauthorized file change
    Given a unit owns its declared production and test files
    When another file is modified
    Then delivery is blocked

Feature: predecessor freeze
  Scenario: successor attempts predecessor mutation
    Then delivery is blocked pending governance reconciliation

Feature: baseline accounting
  Scenario: package contribution
    Then pre-package, contribution, post-package, and full baselines are recorded

Feature: remote gate closure
  Scenario: pending workflow
    Then the unit is not CLOSED

Feature: release reservation
  Scenario: incomplete A07
    Then v1.6.0 remains RESERVED and untagged
```

## 12. Acceptance criteria

E00–E09 are COMPLETE only when their contracts, tests, quality gates, coverage, and boundaries
pass. They are CLOSED only after exact authorized-file commit, publication, remote verification,
and clean tracked-tree inspection. A07 is COMPLETE only after all units close and final release
verification succeeds.
