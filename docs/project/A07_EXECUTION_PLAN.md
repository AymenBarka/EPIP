# A07 Execution Plan

Status: COMPLETE / CLOSED / FROZEN

Baseline: A05-v1.0.0 / A06 v1.5.21 / A07 final collection 2643

Release state: v1.6.0 PREPARED / AWAITING RELEASE AUTHORIZATION / NOT RELEASED
Implementation state: E00-E09 CLOSED / FROZEN

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
E00 -> E01 -> E02 -> E03 -> E04
                              |\
                              | +-> E05
                              | +-> E06
E03 + E04 + E05 + E06 -> E07
E00 + E02 + E03 + E07 -> E08
E08 -> E09
```

E05 and E06 are independent siblings that both consume E04 `EntryValidation`; they must not
import one another. E07 consumes their resulting canonical geometry.

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

E06 normalizes and validates exactly one final upstream-authorized target price. Upstream resolves
all Elliott, Fibonacci, structure, liquidity, or other analytical candidates before E06. E06 has
no candidate precedence, target selection, or RR-derived fallback.

E07 validates finite positive risk/reward and `RR >= minimum_rr`, plus immutable risk acceptance.

E08 canonicalizes one caller-supplied confidence fact in `[0,1]`, applies
`confidence >= minimum_confidence`, derives expiry from the immutable E00 evaluation request and
policy, and never reads the wall clock.

E09 consumes one accepted E08 `ConfidenceValidation`, assembles the final immutable BUY/SELL
signal, and closes the deterministic strategy-evaluation pipeline without predecessor
recomputation or execution behavior. Rejected and `NO_TRADE` chains produce no E09 signal.

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

### 5.6 E06 normative target contract

#### Purpose, ownership, files, and dependency topology

E06 converts exactly one final upstream-authorized target price into one canonical executable
take-profit price and verifies its strict directional relationship to the frozen E04 entry. It is
a geometry-normalization stage only. It owns target-fact validation, policy-precision
normalization, target-side validation, target integrity validation, and E06 diagnostics. It does
not calculate analytical targets or own risk, reward, RR, `minimum_rr` acceptance, confidence,
expiration, signal closure, or execution.

The future implementation scope is exactly `epip/a07/target.py` and
`tests/a07/test_target.py`; neither file is part of this governance reconciliation. E06 exports
exactly `TargetFacts`, `TakeProfit`, `TargetValidation`, and `TargetDiagnostics`; helpers and
constants remain private.

E06 consumes exactly E04 `EntryValidation`. E05 and E06 are independent siblings: both consume
E04, E06 never consumes or imports E05, and E05 never consumes or imports E06. Their canonical
outputs converge in E07. The frozen topology is:

```text
E03 -> E04 entry
       |-> E05 stop
       `-> E06 target

E05 + E06 -> E07
```

Allowed production imports are narrow Python standard-library numeric, immutable-value, and
typing facilities; `StrategyDirection` from E00; `EntryValidation` from E04; and
`DataIntegrityError` from `epip.core.integrity`. E06 must not directly import E01, E02, E03, E05,
A05, A06, E07 or any later unit, analytics, providers, market data, execution, broker, or MT5.
Direction, canonical entry price, and policy precision are reached only through:

```text
entry_validation.entry.direction_validation.decision.direction
entry_validation.entry.price
entry_validation.entry.direction_validation.decision.policy.numeric_precision
```

E06 may read only `policy.numeric_precision`, solely for canonical target-price normalization. It
must not read `minimum_rr` or evaluate risk, reward, RR, or RR acceptance.

#### Final target source and single-target model

E06 accepts exactly one opaque final target price. Upstream analytical authority resolves every
candidate, precedence, tie, absence, or conflict before E06. There is no TP1/TP2/TP3 model, target
list, candidate collection, ranking, voting, best-target selection, or fallback within E06. If no
upstream-authorized final target exists, the caller cannot construct `TargetFacts` or
`TakeProfit`; E06 creates no `None`, zero, NaN, or sentinel target.

E06 performs no Elliott-wave analysis, wave detection or projection, Fibonacci analysis or
extension calculation, structure or liquidity analysis, swing detection, support/resistance
analysis, or market-data analysis. Those sources may contribute upstream, but E06 sees their
resolved result only as `TargetFacts.target_price` and stores no analytical provenance.

There is no policy-authorized RR fallback. E06 does not use `minimum_rr` to derive, select, move,
validate, or reject a target. E07 exclusively owns risk, reward, RR, and `minimum_rr` acceptance.

#### Numeric normalization and directional geometry

Every caller-supplied price must have exact runtime type `float`; booleans, integers, `Decimal`,
strings, `None`, and foreign numeric wrappers fail. It must be finite and strictly positive, so
NaN, both infinities, positive or negative zero, and negative values fail.

Normalization converts the raw value through `Decimal(str(value))`, quantizes it to
`Decimal(1).scaleb(-numeric_precision)` using `ROUND_HALF_EVEN`, and converts the result back to
exact built-in `float`. A zero result, including negative zero, is canonicalized to positive
`0.0`; because an executable target must remain strictly positive, normalization to zero raises
`DataIntegrityError`. Comparison occurs after normalization against E04's already canonical entry,
which E06 neither renormalizes nor recomputes.

The exact target formula for both actionable directions is:

```text
target price = normalized TargetFacts.target_price
```

For BUY, canonical `target price > entry price` is required; equality and a target below entry
raise `DataIntegrityError`. For SELL, canonical `target price < entry price` is required; equality
and a target above entry raise `DataIntegrityError`. If distinct raw target and entry values become
equal at policy precision, the precision collapse raises `DataIntegrityError`. There is no minimum
distance beyond strict canonical separation.

E06 defines no target-to-stop invariant and does not inspect a stop. It may compare target with
entry only to establish geometric side. It neither calculates nor exposes target-stop distance,
risk, reward, reward distance, target distance, profit distance, or RR.

#### Public object matrix

All E06 public objects are immutable and runtime-hashable, compare by exact type and every public
field in documented order, contain no mutable nested state, and own no persistent fingerprint or
digest.

| Object | Purpose and owner | Public fields and exact runtime types | Caller supplied / derived | Validation and canonicalization | Equality, hashing, immutability, reconstruction |
| --- | --- | --- | --- | --- | --- |
| `TargetFacts` | E06-owned final upstream-authorized raw target geometry. | `target_price: float` | Caller supplies `target_price`; no derived field. | Exact built-in finite, strictly positive float; stored unchanged and given no analytical meaning. | Exact-type equality and hash use the field; immutable; direct reconstruction from `target_price`. |
| `TakeProfit` | E06-owned canonical executable target geometry. | `entry_validation: EntryValidation`; `target_facts: TargetFacts`; `price: float` | Caller supplies exact predecessor and facts; `price` is derived and is never caller-authoritative. | Requires an actionable canonical E04 predecessor; normalizes the fact at predecessor policy precision with half-even rounding and enforces the strict BUY/SELL entry relation. | Exact-type equality and hash use all fields; immutable; reconstruction from predecessor and facts recomputes price, and any optionally supplied price must be an exact float equal to the recomputation. |
| `TargetValidation` | E06-owned integrity validation of an executable target. | `target: TakeProfit`; `valid: bool`; `diagnostics: TargetDiagnostics` | Caller supplies exact `target`; `valid=True` and `diagnostics=TargetDiagnostics(())` are derived. | A successfully constructed canonical `TakeProfit` is integrity-valid; RR semantics do not participate. | Exact-type equality and hash use all fields; immutable; reconstruction recomputes derived fields and rejects contradictions. |
| `TargetDiagnostics` | E06-owned closed diagnostic value. | `diagnostics: tuple[str, ...]` | Caller supplies the tuple; only `()` is canonical. | Exact tuple required; the vocabulary is empty, so non-empty values, unknown or malformed codes, duplicates, and mutable containers fail. | Exact-type equality and hash use the tuple; immutable; only `()` reconstructs successfully. |

#### Predecessor actionability and `TakeProfit`

`TakeProfit` requires the exact `EntryValidation` type and exact `TargetFacts` type. The predecessor
must have `valid is True`, canonical empty E04 diagnostics, a canonical executable `EntryPrice`,
and direction exactly `StrategyDirection.BUY` or `StrategyDirection.SELL`. A wrong, malformed,
invalid, non-actionable, or `NO_TRADE` predecessor raises `DataIntegrityError`; E06 never
recomputes E03 direction or E04 entry.

The exact public fields, constructor/equality order, and ownership are:

| Field | Type | Ownership |
| --- | --- | --- |
| `entry_validation` | `EntryValidation` | Caller supplied; exact frozen E04 object. |
| `target_facts` | `TargetFacts` | Caller supplied; exact E06 raw fact object. |
| `price` | `float` | Derived normalized target price. |

The ordinary construction API accepts only `entry_validation` and `target_facts` and recomputes
`price`. A reconstruction API may accept all public fields, but supplied `price` must have exact
float type and exactly equal the recomputed canonical price. A noncanonical or contradictory
derived price raises `DataIntegrityError`.

#### `TargetValidation` and `TargetDiagnostics`

`TargetValidation` is canonical-geometry integrity validation, not trade, reward, or RR
acceptance. Its public constructor accepts only an exact `TakeProfit`. A successfully constructed
target always derives `valid=True` and canonical empty diagnostics. Reconstruction from all public
fields recomputes those values and rejects wrong types or any contradiction with
`DataIntegrityError`.

`TargetDiagnostics` has the sole field `diagnostics: tuple[str, ...]`. Its closed vocabulary is
empty and its sole canonical value is `()`. The input must be an actual tuple. Every non-empty
tuple, unknown or malformed code, duplicate code, and mutable diagnostic container raises
`DataIntegrityError`. Direct reconstruction from `()` preserves exact equality and hash. All
E06-invalid states are construction-time structural/integrity failures rather than diagnostic
outcomes.

#### Error model, equality, reconstruction, and determinism

Wrong `TargetFacts`, `EntryValidation`, or other public types; invalid or non-actionable
predecessors; `NO_TRADE`; wrong numeric runtime types; NaN; infinities; zero or negative values;
BUY equality or wrong-side values; SELL equality or wrong-side values; precision collapse;
non-empty or mutable diagnostics; and contradictory reconstruction all raise
`DataIntegrityError`. A missing required target fact follows normal Python missing-argument
behavior. RR below policy minimum and `minimum_rr` failure are not E06 states; E07 owns them.

Every object uses exact-type value equality with all public fields participating, and all public
fields participate in runtime hashing. Round-trip reconstruction preserves exact equality, hash,
canonical price, and predecessor identity. `TargetFacts` reconstructs directly from its public
field; `TakeProfit` recomputes price; `TargetValidation` recomputes true validity and empty
diagnostics; and only empty `TargetDiagnostics` reconstructs.

Output depends only on immutable input. Repeated equivalent construction produces identical
values and is independent of clock, timezone, locale, environment variables, filesystem, network,
provider, market feed, broker, MT5, randomness, process-global mutable state, registry, and cache.

#### Successor isolation and future test contract

Risk, reward, RR, and `minimum_rr` acceptance belong to E07. Confidence and expiration belong to
E08. Signal assembly, validation, and closure belong to E09. Execution is outside E06. E06 exposes,
calculates, validates, or imports none of this successor behavior.

Future E06 tests must cover exact public API and runtime types; `TargetFacts` validation; valid BUY
and SELL targets; BUY equality and wrong-side rejection; SELL equality and wrong-side rejection;
numeric precision and `ROUND_HALF_EVEN`; precision collapse; zero, negative zero, negative values,
NaN, positive infinity, negative infinity, bool, int, `Decimal`, string, and `None`; invalid and
`NO_TRADE` predecessors; precision access through the predecessor policy chain;
`TargetValidation` semantics; empty diagnostics and diagnostic rejection; equality, exact-type
inequality, hashing, immutability, nested immutability, reconstruction and contradictory
reconstruction; determinism and external-state independence; E04 compatibility; absence of an E05
dependency, RR calculation, `minimum_rr` access, Fibonacci calculation, Elliott calculation, and
analytical candidate selection; E07+ isolation; and the direct dependency/import boundary. No
arbitrary exact E06 test count is prescribed.

The canonical pre-E06 baseline is 2405. This governance reconciliation adds no tests, so its
required collection is `2405 + 0 = 2405`, with no predecessor node removal. A future E06
implementation reports its actual collected contribution and requires post-E06 collection to
equal `2405 + actual E06 contribution`. E06 may close only after its two authorized implementation
files alone are committed; focused, predecessor, collection, full-regression, coverage, static,
determinism, immutability, fail-closed, reconstruction, ownership, and successor-isolation gates
pass; publication succeeds; and every applicable exact-SHA remote gate is green. E06 closure
authorizes no E07 implementation.

### 5.7 E07 normative reward-risk contract

#### Purpose, ownership, files, and dependencies

E07 deterministically derives reward-risk values and applies the policy minimum-RR threshold over
already canonical executable E04, E05, and E06 geometry. It owns exactly risk, reward, RR, and
`minimum_rr` acceptance. It does not own entry, stop, or target construction; direction
resolution; evidence; analytical, Elliott, Fibonacci, or trend calculations; confidence;
expiration; signal closure; execution; broker behavior; or MT5 behavior.

The future implementation scope is exactly `epip/a07/reward_risk.py` and
`tests/a07/test_reward_risk.py`. E07 exports exactly `RewardRiskOutcome`,
`RewardRiskValidation`, and `RewardRiskDiagnostics`; helpers and constants remain private. No
production or test implementation is authorized by this governance contract.

Authorized direct dependencies are narrow Python standard-library numeric, immutable-value, and
typing facilities; E04 `EntryValidation`; E05 `StopValidation`; E06 `TargetValidation`; and core
`DataIntegrityError`. E00 `StrategyDirection` may be imported only when required for exact BUY/SELL
branching. E07 must not directly import E01, E02, E03, A05, A06, analytics, providers, market data,
Fibonacci or Elliott computation, confidence, expiration, signals, execution, broker, MT5, E08 or
later packages, or external-state services.

#### Public object matrix

All E07 public objects are immutable and runtime-hashable, compare by exact type and every public
field in documented order, contain no mutable nested state, and own no persistent fingerprint,
UUID, reference, or digest.

| Object | Purpose | Public fields and exact runtime types | Caller supplied / derived | Validation and canonicalization | Equality, hashing, reconstruction |
| --- | --- | --- | --- | --- | --- |
| `RewardRiskOutcome` | Canonical E07 arithmetic result over converged geometry. | `entry_validation: EntryValidation`; `stop_validation: StopValidation`; `target_validation: TargetValidation`; `risk: float`; `reward: float`; `rr: float` | Caller supplies the three exact predecessor validations; risk, reward, and RR are derived. | Requires actionable, value-consistent predecessors; derives positive distances through decimal subtraction and canonical RR through the E07 12-decimal profile. | All six fields participate; reconstruction recomputes all derived values and rejects contradictions. |
| `RewardRiskValidation` | E07-only minimum-RR acceptance result. | `outcome: RewardRiskOutcome`; `valid: bool`; `diagnostics: RewardRiskDiagnostics` | Caller supplies exact outcome; validity and diagnostics are derived. | Valid exactly when canonical RR is at least authoritative policy `minimum_rr`. | All three fields participate; reconstruction recomputes validity and diagnostics and rejects contradictions. |
| `RewardRiskDiagnostics` | Closed immutable E07 domain-negative diagnostic value. | `diagnostics: tuple[str, ...]` | Caller supplies exact tuple representation. | Accepts only `()` or `("RR_BELOW_MINIMUM",)`; tuple must already be canonical. | Tuple participates; direct reconstruction accepts only either canonical state. |

#### Predecessor convergence, actionability, and policy continuity

`RewardRiskOutcome` directly consumes exact `EntryValidation`, `StopValidation`, and
`TargetValidation` runtime types. The directly supplied entry validation is the canonical reference
entry. The following value-equality invariants are mandatory:

```text
stop_validation.stop.entry_validation == entry_validation
target_validation.target.entry_validation == entry_validation
```

Python object identity is not required. Independently reconstructed but value-equal frozen
predecessors are accepted. A stop or target referencing a value-unequal entry raises
`DataIntegrityError`; this is structural corruption, not an RR rejection.

All three validations must have `valid is True` and their frozen canonical validation state. The
entry direction must resolve to exactly `StrategyDirection.BUY` or `StrategyDirection.SELL`.
Wrong types, invalid validations, malformed validation state, continuity mismatch, or `NO_TRADE`
raise `DataIntegrityError`; no `RewardRiskOutcome` is created.

E07 accepts no separate policy or `minimum_rr` parameter. Its authoritative policy and threshold
are reached only through:

```text
entry_validation.entry.direction_validation.decision.policy
entry_validation.entry.direction_validation.decision.policy.minimum_rr
```

Stop and target policy continuity follows from their required entry-validation value equality.
E07 neither selects nor recomputes policy and does not duplicate policy state.

#### Canonical prices and directional distance formulas

E07 reads the already canonical predecessor prices exactly as:

```text
entry  = entry_validation.entry.price
stop   = stop_validation.stop.price
target = target_validation.target.price
```

It must not re-round, quantize, mutate, correct, or otherwise recreate E04, E05, or E06 price
normalization. It converts each canonical float operand with `Decimal(str(value))` for E07-owned
distance arithmetic. Raw binary-float subtraction is not the normative operation.

For BUY, the exact formulas are:

```text
risk_decimal   = Decimal(str(entry)) - Decimal(str(stop))
reward_decimal = Decimal(str(target)) - Decimal(str(entry))
```

For SELL, the exact formulas are:

```text
risk_decimal   = Decimal(str(stop)) - Decimal(str(entry))
reward_decimal = Decimal(str(entry)) - Decimal(str(target))
```

Both derived decimals must be finite and strictly positive. Zero, negative, or non-finite risk or
reward raises `DataIntegrityError`. No absolute-value fallback, epsilon, tolerance, correction, or
distance minimum exists. E07 may enforce positive arithmetic integrity but must not recreate stop
or target selection and normalization.

Risk and reward are not re-quantized to `policy.numeric_precision`. After decimal validation,
their canonical public values are exactly `float(risk_decimal)` and `float(reward_decimal)`, both
exact built-in floats that must remain finite and strictly positive.

#### RR calculation and canonical profile

RR means reward divided by risk, exactly:

```text
rr_decimal = reward_decimal / risk_decimal
```

Reward is the numerator and risk is the denominator. Risk must already be strictly positive; a
zero denominator is structural corruption raising `DataIntegrityError`. There is no inverse,
absolute, alternative, or binary-float division formula.

RR is not a price, so E01 `numeric_precision` must not quantize it. E07 owns this dedicated RR
canonical profile:

```text
rr_canonical_decimal = rr_decimal.quantize(
    Decimal("0.000000000001"),
    rounding=ROUND_HALF_EVEN,
)
rr = float(rr_canonical_decimal)
```

The public RR therefore has 12-decimal canonical precision and exact built-in `float` runtime
type. It must be finite and strictly positive. A negative-zero result is canonicalized to positive
`0.0` and then rejected. Instrument price precision cannot alter RR precision or acceptance.

#### Minimum-RR comparison and domain result

The authoritative threshold is the frozen E01 float reached through the reference entry's policy.
E07 converts it for comparison as:

```text
minimum_rr_decimal = Decimal(str(policy.minimum_rr))
accepted = rr_canonical_decimal >= minimum_rr_decimal
```

Comparison occurs after RR canonicalization and in the Decimal domain. It uses no epsilon,
tolerance, `math.isclose`, binary-float comparison, or additional threshold rounding. Exact
equality is accepted. A canonical RR above the threshold is accepted; one below it is a
well-formed E07 domain-negative result.

Below-threshold geometry still produces `RewardRiskOutcome`: entry, stop, target, risk, reward,
and RR remain valid. E07 must not raise solely for a low RR, change direction, move geometry, or
create fallback geometry.

#### `RewardRiskOutcome`

The exact fields, constructor/equality order, and ownership are:

| Field | Type | Ownership |
| --- | --- | --- |
| `entry_validation` | `EntryValidation` | Caller supplied; canonical reference entry. |
| `stop_validation` | `StopValidation` | Caller supplied; must reference a value-equal entry. |
| `target_validation` | `TargetValidation` | Caller supplied; must reference a value-equal entry. |
| `risk` | `float` | Derived canonical directional risk distance. |
| `reward` | `float` | Derived canonical directional reward distance. |
| `rr` | `float` | Derived canonical 12-decimal reward/risk ratio. |

The ordinary constructor accepts only the three predecessor validations. Callers cannot choose
authoritative risk, reward, or RR. Reconstruction accepts the three predecessors plus serialized
public `risk`, `reward`, and `rr`; each supplied derived value must have exact built-in float type
and exactly equal the independently recomputed canonical public value. Any mismatch, non-finite or
non-positive supplied value, or other contradiction raises `DataIntegrityError`. Round trips
preserve exact equality, runtime hash, all three numeric values, and predecessor value continuity.

#### `RewardRiskValidation` and `RewardRiskDiagnostics`

`RewardRiskValidation` means only E07 reward-risk acceptance. Its ordinary constructor accepts one
exact `RewardRiskOutcome` and derives:

```text
accepted: valid=True,  diagnostics=RewardRiskDiagnostics(())
rejected: valid=False, diagnostics=RewardRiskDiagnostics(("RR_BELOW_MINIMUM",))
```

It does not mean that confidence, expiration, final signal, order, or execution is approved.
Reconstruction accepts `outcome`, `valid`, and `diagnostics`, requires exact bool and diagnostics
types, recomputes both derived fields from the outcome and authoritative threshold, and raises
`DataIntegrityError` for any contradiction.

`RewardRiskDiagnostics` has the sole field `diagnostics: tuple[str, ...]`. Its complete known code
vocabulary is `RR_BELOW_MINIMUM`. Input must be an exact immutable tuple already in canonical
lexicographic order. The only valid states are `()` and `("RR_BELOW_MINIMUM",)`. Mutable
containers, unknown or malformed codes, duplicates, and non-canonical states raise
`DataIntegrityError`. No predecessor diagnostic is propagated. Structural failures raise rather
than becoming E07 diagnostics.

#### Malformed and domain-negative classification

| Condition | Classification and exact behavior |
| --- | --- |
| Wrong `EntryValidation`, `StopValidation`, or `TargetValidation` type | Structural `DataIntegrityError`. |
| Invalid or malformed predecessor validation | Structural `DataIntegrityError`. |
| `NO_TRADE` predecessor | Structural `DataIntegrityError`; no outcome. |
| Stop-entry or target-entry value mismatch | Structural `DataIntegrityError`. |
| Non-positive or non-finite risk | Structural `DataIntegrityError`. |
| Non-positive or non-finite reward | Structural `DataIntegrityError`. |
| Zero denominator or non-positive/non-finite canonical RR | Structural `DataIntegrityError`. |
| Contradictory reconstructed derived state | Structural `DataIntegrityError`. |
| Canonical RR below `minimum_rr` | Well-formed domain-negative validation: `valid=False`, diagnostics exactly `("RR_BELOW_MINIMUM",)`. |
| Canonical RR equal to or above `minimum_rr` | Accepted validation: `valid=True`, diagnostics exactly `()`. |

#### Trust boundary, determinism, and successor isolation

E07 verifies exact predecessor types, validation actionability, and reference-entry value
continuity; reads canonical entry, stop, and target; derives its own distances and ratio; and
derives its own threshold acceptance. It must not recompute E01 identity/fingerprint or policy
validity, E02 evidence validity, E03 consensus, E04 entry normalization, E05 stop selection or
normalization, or E06 target selection or normalization.

Equivalent immutable predecessor geometry produces identical risk, reward, RR, validity,
diagnostics, equality, hash, and reconstruction. Behavior is independent of clock, timezone,
locale, environment, filesystem, network, market data, provider, broker, MT5, randomness, process
state, mutable global state, registry, and cache.

E08 exclusively owns confidence and expiration. E07 must not calculate confidence, read confidence
thresholds, apply time decay, derive expiration, read clocks, or modify acceptance using confidence
or expiration. E09 owns final signal assembly, validation, and closure. Execution is outside E07.
An accepted `RewardRiskValidation` is only an E07 result and is not final-signal or execution
authorization.

#### Normative numeric examples

For BUY with entry `100.0`, stop `95.0`, and target `115.0`, risk is `5.0`, reward is
`15.0`, and canonical RR is `3.0`. For SELL with entry `100.0`, stop `105.0`, and target `85.0`,
risk is `5.0`, reward is `15.0`, and canonical RR is `3.0`. With `minimum_rr=3.0`, both are
accepted because equality satisfies `RR >= minimum_rr`.

With risk `5`, reward `14`, and `minimum_rr=3.0`, raw and canonical RR are `2.8`; validation is
`valid=False` with diagnostics exactly `("RR_BELOW_MINIMUM",)`.

Threshold comparison uses canonical 12-decimal RR. A raw decimal RR of `2.9999999999996`
half-even quantizes to `3.000000000000` and is accepted against `3.0`; a raw decimal RR of
`2.9999999999994` quantizes to `2.999999999999` and is rejected. Implementations derive these
values through Decimal arithmetic, never binary-float approximation.

#### Future test contract and closure

Future E07 tests must cover exact public fields and runtime types; wrong predecessor types; BUY and
SELL risk, reward, and RR formulas; `Decimal(str(...))` arithmetic; 12-decimal RR half-even
canonicalization and public float conversion; authoritative `minimum_rr` access and comparison
after RR canonicalization; below, exact-equality, and above-threshold results; zero/non-positive
risk and reward and non-finite derived-state rejection; stop-entry and target-entry mismatch;
independently reconstructed value-equal predecessors; `NO_TRADE`; validation semantics;
`RR_BELOW_MINIMUM`; unknown, duplicate, malformed, mutable, and non-canonical diagnostics;
immutability and nested immutability; exact-type equality; hashing; reconstruction and every
contradictory reconstruction; determinism and external-state independence; E04/E05/E06
compatibility; absence of direct E01-E03, A05/A06, and E08+ imports; and confidence, expiration,
signal, and execution isolation. No arbitrary exact E07 test count is prescribed.

The canonical pre-E07 baseline is 2448. This governance reconciliation adds no tests, so required
collection remains `2448 + 0 = 2448`, with no predecessor node removal. A future E07
implementation reports its actual contribution and requires post-E07 collection to equal
`2448 + actual E07 contribution`. E07 may close only after its two authorized implementation files
alone are committed; focused, predecessor, collection, full-regression, coverage, static,
determinism, immutability, fail-closed, reconstruction, ownership, and successor-isolation gates
pass; publication succeeds; and every applicable exact-SHA remote gate is green. E07 closure
authorizes no E08 implementation.

### 5.8 E08 normative confidence and expiration contract

#### Purpose, ownership, files, and dependencies

E08 binds one caller-supplied immutable confidence fact to already accepted E02, E03, and E07
results, applies the policy minimum-confidence threshold, and derives deterministic expiration
metadata from the immutable E00 evaluation request and E01 policy duration. It owns confidence
canonicalization, `minimum_confidence` acceptance, expiration derivation, validation, and E08
diagnostics. The predecessor references are its complete rationale inputs; E08 defines no separate
scoring explanation or analytical-rationale taxonomy.

The future implementation scope is exactly `epip/a07/confidence.py` and
`tests/a07/test_confidence.py`. E08 exports exactly `StrategyConfidence`, `SignalExpiration`,
`ConfidenceValidation`, and `ConfidenceDiagnostics`; helpers and constants remain private. This
governance contract authorizes no implementation.

E08 directly consumes exact E00 `StrategyEvaluationRequest`, E02 `EvidenceValidation`, E03
`DirectionValidation`, and E07 `RewardRiskValidation` objects. The direct E00 dependency is the
authoritative immutable path to `evaluation_timestamp`; no frozen predecessor is changed to
duplicate it. E01 policy is reached indirectly through E03 and E07 continuity.

Allowed direct imports are deterministic Python standard-library immutable-value, numeric, typing,
and datetime facilities; the four predecessor types just named; and core `DataIntegrityError`.
Direct E01, E04, E05, and E06 imports are forbidden. Their values remain reachable only through
the frozen chain. A05, A06, E09+, analytics, providers, market data, replay clocks, filesystem,
network, execution, broker, and MT5 imports are forbidden.

#### Common object rules

All four public objects are immutable and runtime-hashable, compare by exact type and every public
field in documented order, and contain only immutable nested values. Every field participates in
equality and `hash()`. E08 owns no persistent fingerprint, UUID, reference, or digest.

Ordinary constructors accept only fields identified below as caller supplied and derive every
other field. Each class provides `reconstruct`, accepting all public fields in documented order.
Reconstruction independently recomputes derived state and requires exact equality with supplied
derived values. Wrong types, non-canonical values, and contradictions raise `DataIntegrityError`.
Round trips preserve equality, runtime hash, canonical confidence, canonical timestamps, and
predecessor value continuity.

#### Exact predecessor topology and hard gates

`StrategyConfidence` consumes exact runtime types `EvidenceValidation`, `DirectionValidation`, and
`RewardRiskValidation`. The directly supplied E02 value is the canonical evidence reference. The
mandatory value-equality invariants are:

```text
direction_validation.decision.evidence_validation == evidence_validation
reward_risk_validation.outcome.entry_validation.entry.direction_validation
    == direction_validation
```

Object identity is not required; independently reconstructed value-equal predecessors are valid.
All three validations must have `valid is True` and frozen canonical state, and direction must be
exactly `StrategyDirection.BUY` or `StrategyDirection.SELL`. Wrong types, malformed or invalid
evidence, non-actionable direction, `NO_TRADE`, failed RR acceptance, or continuity mismatch raises
`DataIntegrityError`; no confidence object is created. Confidence never compensates for a failed
hard gate. Predecessor diagnostic strings are not copied or reinterpreted.

The authoritative policy is exactly
`direction_validation.decision.policy`. E07 policy continuity follows through the required
direction-validation equality. E08 accepts no separate policy, threshold, or duration argument.

#### Caller-supplied confidence fact and numeric model

E08 adopts one model: the caller supplies one immutable normalized strategy-assessment fact after
upstream analysis produced the E02/E03/E07 results. The caller owns the semantic calculation that
produced this fact. E08 does not derive, weight, average, boost, penalize, or infer confidence from
evidence counts, freshness, direction votes, RR magnitude, Elliott facts, trend, or structure. Its
predecessors are hard gates and immutable rationale references only and contribute no numeric
weight. There is no hidden heuristic or E08 derivation formula.

Confidence must have exact built-in `float` type. Integers, booleans, `Decimal`, strings, and float
subclasses are rejected. It must be finite and within inclusive `0.0..1.0`. NaN, either infinity,
and values outside the range raise `DataIntegrityError`. Negative zero canonicalizes to positive
`0.0`; every other value is stored as the exact supplied float. E08 applies no quantization or
rounding and never uses `policy.numeric_precision`. Its comparison representation is exactly
`Decimal(str(confidence))`.

#### `StrategyConfidence`

Its exact fields, constructor/equality order, and ownership are:

| Field | Exact runtime type | Source and contract |
| --- | --- | --- |
| `evidence_validation` | `EvidenceValidation` | Caller-supplied exact E02 hard-gate result. |
| `direction_validation` | `DirectionValidation` | Caller-supplied exact E03 result; converges with E02. |
| `reward_risk_validation` | `RewardRiskValidation` | Caller-supplied exact E07 result; converges with E03. |
| `confidence` | `float` | Caller-supplied fact, validated and canonicalized by E08. |

The constructor accepts those four fields only and derives no score. Reconstruction accepts the
same predecessors and serialized confidence, repeats validation and canonicalization, and requires
exact equality with canonical confidence.

#### Minimum-confidence threshold

The threshold is reached only through
`strategy_confidence.direction_validation.decision.policy.minimum_confidence`. After confidence
canonicalization, E08 computes:

```text
accepted = (
    Decimal(str(strategy_confidence.confidence))
    >= Decimal(str(policy.minimum_confidence))
)
```

There is no epsilon, tolerance, `math.isclose`, binary-float threshold decision, or threshold
rounding. Equality and values above the threshold are accepted. A value below the threshold is a
well-formed domain-negative result and does not alter confidence, RR, direction, or geometry.

#### Deterministic expiration and request continuity

`SignalExpiration` consumes exact `StrategyEvaluationRequest` and `StrategyConfidence` values.
Policy is reached through `strategy_confidence.direction_validation.decision.policy`. The request
must satisfy:

```text
request.strategy_identity == policy.strategy_identity
request.policy_reference == policy.identity.reference
all(
    snapshot.evidence_identity == request.evidence_identity
    for snapshot in strategy_confidence.evidence_validation.binding.available_evidence
)
```

The last invariant is vacuously true for an empty policy-valid binding. Any mismatch raises
`DataIntegrityError`. The base timestamp is exactly `request.evaluation_timestamp`; duration is
exactly `policy.expiration_seconds`, already validated by E01 as a positive non-boolean integer in
seconds. No separate timestamp or duration is accepted.

E08 parses the E00 timestamp with `datetime.fromisoformat`, matching E00. Any timezone-aware offset
accepted by that parser is accepted, including `Z`, UTC, and positive or negative fixed offsets.
Parse failure, timezone-naive input, missing `utcoffset`, datetime overflow, or impossible
derivation raises `DataIntegrityError`.

Both base and expiry instants normalize to UTC. Their canonical public representation is an exact
`str` produced with `isoformat(timespec="microseconds")`, replacing terminal `+00:00` with uppercase
`Z`: exactly `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Six fractional digits are always present. Parsed input
fractions are represented at Python datetime's exact microsecond precision; no original offset
spelling survives in derived canonical fields.

The exact formula is:

```text
evaluation_instant = datetime.fromisoformat(request.evaluation_timestamp)
evaluation_utc = evaluation_instant.astimezone(timezone.utc)
expires_utc = evaluation_utc + timedelta(seconds=policy.expiration_seconds)
```

No `datetime.now()`, `datetime.utcnow()`, `time.time()`, system or replay clock, timezone-local
current state, or live comparison is allowed. `SignalExpiration` is metadata only and never asks
whether a signal is expired now. A future live decision requires an explicit immutable comparison
time and an authorized successor or runtime contract.

#### `SignalExpiration`

Its fields, constructor/equality order, and ownership are:

| Field | Exact runtime type | Source and contract |
| --- | --- | --- |
| `request` | `StrategyEvaluationRequest` | Caller-supplied exact E00 request. |
| `strategy_confidence` | `StrategyConfidence` | Caller-supplied exact E08 confidence value. |
| `evaluation_timestamp` | `str` | Derived canonical UTC request timestamp. |
| `expiration_seconds` | `int` | Derived exact positive policy duration in seconds. |
| `expires_at` | `str` | Derived canonical UTC timestamp from the formula. |

The constructor accepts only `request` and `strategy_confidence`. Reconstruction accepts all five
fields, recomputes the three derived fields, and rejects an exact-value or type contradiction.
Correct expiration metadata remains structurally valid as an immutable value; passage of wall time
cannot mutate it or make E08 validation false.

#### Diagnostics and validation

`ConfidenceDiagnostics` has one field, `diagnostics: tuple[str, ...]`. Input must be an exact tuple
of exact strings already in lexicographic order. The closed vocabulary contains only
`CONFIDENCE_BELOW_MINIMUM`; the only valid states are `()` and
`("CONFIDENCE_BELOW_MINIMUM",)`. Unknown or malformed values, mutable containers, duplicates, and
non-canonical order raise `DataIntegrityError`. Simultaneous E08 diagnostics cannot occur.
Construction and reconstruction accept the tuple field and enforce identical rules.

`ConfidenceValidation` means only E08 predecessor continuity, confidence acceptance, and structural
expiration consistency; it is not final-signal authorization. Its fields are:

| Field | Exact runtime type | Source and derivation |
| --- | --- | --- |
| `strategy_confidence` | `StrategyConfidence` | Caller-supplied exact E08 value. |
| `signal_expiration` | `SignalExpiration` | Caller-supplied exact E08 expiration. |
| `valid` | `bool` | Derived solely from confidence meeting the threshold. |
| `diagnostics` | `ConfidenceDiagnostics` | Derived empty or below-minimum state. |

The constructor accepts only `strategy_confidence` and `signal_expiration` and requires
`signal_expiration.strategy_confidence == strategy_confidence`; mismatch raises
`DataIntegrityError`. Predecessor gates and expiration structure were enforced by their owning E08
objects. It derives exactly:

```text
accepted: valid=True,  diagnostics=ConfidenceDiagnostics(())
rejected: valid=False, diagnostics=ConfidenceDiagnostics(
    ("CONFIDENCE_BELOW_MINIMUM",)
)
```

Reconstruction accepts all four fields, requires exact built-in `bool` and exact diagnostics type,
recomputes both derived fields, and rejects contradictions. Expiration contributes structural
integrity only; no live time affects `valid`.

#### Malformed, domain-negative, and successor-owned classification

| Condition | Exact behavior |
| --- | --- |
| Wrong E00, E02, E03, E07, or E08 public-object runtime type | Structural `DataIntegrityError`. |
| Invalid/malformed E02 validation | Structural `DataIntegrityError`; no confidence object. |
| Invalid/non-actionable E03 validation or `NO_TRADE` | Structural `DataIntegrityError`; no confidence object. |
| Rejected E07 validation | Structural `DataIntegrityError`; confidence cannot compensate. |
| Any predecessor value-continuity mismatch | Structural `DataIntegrityError`. |
| Wrong confidence type, including bool, int, `Decimal`, string, or subclass | Structural `DataIntegrityError`. |
| NaN, infinity, confidence below zero, or confidence above one | Structural `DataIntegrityError`. |
| Confidence below `minimum_confidence` | Domain-negative validation with exactly `CONFIDENCE_BELOW_MINIMUM`. |
| Confidence equal to or above `minimum_confidence` | Accepted validation with empty diagnostics. |
| Malformed or timezone-naive evaluation timestamp | Structural `DataIntegrityError`. |
| Invalid expiration duration | Frozen E01 structural failure; malformed reconstructed state raises `DataIntegrityError`. |
| Request/policy/evidence continuity mismatch | Structural `DataIntegrityError`. |
| Derived timestamp or expiration contradiction | Structural `DataIntegrityError`. |
| Unknown, duplicate, mutable, malformed, or non-canonical diagnostics | Structural `DataIntegrityError`. |
| Expiration compared with external current time | Not evaluated by E08; explicit-time successor/runtime responsibility. |

Structural failures never become `CONFIDENCE_BELOW_MINIMUM`, predecessor codes are not propagated,
and E08 creates no fallback state.

#### Determinism, trust boundary, and E09 isolation

E08 checks predecessor types, actionability, and continuity; validates and stores confidence;
applies the policy threshold; and derives expiration metadata. It does not recompute evidence,
direction, geometry, risk, reward, RR, policy fingerprints, or predecessor diagnostics. Equivalent
immutable inputs produce identical public values, equality, hashes, and reconstruction.

E08 is independent of wall clock, timezone-local current state, locale, filesystem, network,
environment, providers, market data, broker, MT5, randomness, process identity, unordered
iteration, mutable globals, registries, and caches.

E09 exclusively owns final signal construction, integrated validation, and closure. E08 does not
construct or authorize a final BUY/SELL signal; mutate direction, entry, stop, or target; create a
broker payload; execute; or access MT5. E09 may later consume frozen E08 results.

#### Future E08 test contract and closure

Future tests must cover exact exports, field order, runtime types, and constructor signatures;
predecessor convergence and value-equal reconstruction; invalid E02, non-actionable E03, rejected
E07, `NO_TRADE`, and continuity mismatches; caller-supplied confidence and absence of weighting;
bounds, negative zero, threshold below/equal/above, bool, int, `Decimal`, string, subclass, NaN, and
both infinities; no-rounding storage and Decimal comparison; E00 request continuity; UTC and
positive/negative offsets; malformed/timezone-naive input; duration and seconds unit; exact expiry
formula; UTC normalization, uppercase `Z`, six fractional digits, fractional preservation, and
overflow; wall-clock independence and absence of live evaluation; diagnostics and malformed forms;
validation; exact-type equality, hashing, immutability and nested immutability; reconstruction and
contradictions; determinism; dependency enforcement; external-state independence; and E09, signal,
execution, broker, and MT5 isolation. No arbitrary E08 test count is prescribed.

The canonical pre-E08 baseline is 2504. This governance reconciliation adds no tests, so collection
remains `2504 + 0 = 2504`, with zero predecessor node removal. Future implementation reports its
actual contribution and requires post-E08 collection to equal `2504 + actual E08 contribution`.
E08 may close only after its two implementation files alone are committed; all focused,
predecessor, collection, full-regression, coverage, static, documentation, determinism,
immutability, fail-closed, reconstruction, ownership, and successor-isolation gates pass;
publication succeeds; and every applicable exact-SHA remote gate is green. E08 closure authorizes
no E09 implementation.

### 5.9 E09 normative signal closure contract

#### Purpose, ownership, files, and dependencies

E09 is deterministic final A07 signal assembly, validation, and pipeline closure over already
canonical predecessor semantics. It assembles one immutable actionable BUY or SELL
`StrategySignal` and its success-only `SignalValidation`. Closure means completing the A07 strategy
evaluation pipeline; it never means closing a position, order, or trade.

E09 does not compute evidence, direction, entry, stop, target, risk, reward, RR, confidence, or
expiration. It owns no broker execution, order creation, position management, sizing, spread,
slippage, or MT5 behavior. The future implementation scope is exactly `epip/a07/signal.py` and
`tests/a07/test_signal.py`. E09 exports exactly `StrategySignal`, `SignalValidation`, and
`SignalDiagnostics`; helpers remain private. This contract authorizes no implementation.

The sole direct predecessor is exact E08 `ConfidenceValidation`. E09 does not accept E02-E07
objects, policy, geometry, confidence, timestamps, or thresholds independently. Allowed direct
imports are deterministic Python standard-library immutable-value and typing facilities; E08
`ConfidenceValidation`; E00 `StrategyIdentity` and `StrategyDirection` only for exact public-field
typing and direction membership; and core `DataIntegrityError`. `StrategyConfidence` and
`SignalExpiration` are accessed through `ConfidenceValidation` and need no direct import. E01-E07
are indirect only. Direct A05, A06, analytics, providers, market data, execution, broker, MT5,
filesystem, network, clock, and successor imports are forbidden.

#### Common object rules

All three public objects are immutable and runtime-hashable, compare only by exact type and every
public field in documented order, and contain only immutable nested values. Every public field
participates in equality and `hash()`. E09 owns no persistent signal ID, UUID, reference,
fingerprint, or digest; runtime `hash()` is in-process value hashing only.

Ordinary constructors accept only documented caller-supplied fields and derive every other field.
Each class provides `reconstruct`, accepting all public fields in documented order plus the
authoritative predecessor where needed. Reconstruction independently derives canonical state and
requires exact type and value equality with every supplied derived field. A contradiction raises
`DataIntegrityError`. Successful round trips preserve exact equality, hash, all semantic fields,
and predecessor continuity.

#### Exact predecessor, canonicality, and continuity

`StrategySignal` accepts one exact `ConfidenceValidation`. It requires `valid is True`, exact empty
E08 diagnostics, and canonical E08 state. Canonicality is delegated to the frozen owner by requiring
that:

```text
ConfidenceValidation.reconstruct(
    confidence_validation.strategy_confidence,
    confidence_validation.signal_expiration,
    confidence_validation.valid,
    confidence_validation.diagnostics,
) == confidence_validation
```

E09 does not reproduce E08 threshold or expiration logic. The E08 reconstruction operation is the
authoritative canonicality check. It also requires the frozen continuity already expressed by:

```text
confidence_validation.signal_expiration.strategy_confidence
    == confidence_validation.strategy_confidence
```

Value equality is normative; Python object identity is not required. A wrong type, false E08
validation, non-empty E08 diagnostics, malformed chain, failed reconstruction, or continuity
mismatch raises `DataIntegrityError`. E07 RR rejection, E08 confidence rejection, and E03
`NO_TRADE` therefore never produce an E09 signal. They remain pipeline-negative predecessor
states, not final signals or E09 diagnostics.

#### Final direction and source graph

Let these private access aliases describe the frozen chain:

```text
cv = confidence_validation
sc = cv.strategy_confidence
expiration = cv.signal_expiration
direction_validation = sc.direction_validation
rr_validation = sc.reward_risk_validation
rr_outcome = rr_validation.outcome
entry_validation = rr_outcome.entry_validation
stop_validation = rr_outcome.stop_validation
target_validation = rr_outcome.target_validation
policy = direction_validation.decision.policy
```

Final direction is copied exactly from `direction_validation.decision.direction`. It must be exact
`StrategyDirection.BUY` or `StrategyDirection.SELL`. E09 never recomputes, votes, changes, or
normalizes direction. `NO_TRADE` is structural corruption at this boundary and raises
`DataIntegrityError`.

E09 supports no `NO_TRADE` `StrategySignal` and no rejected `StrategySignal`. Actionable E04-E08
geometry exists only for accepted BUY/SELL chains. E09 has no domain-negative output state.

#### `StrategySignal`

Its exact twelve public fields, constructor/equality order, types, and canonical sources are:

| Field | Exact runtime type | Canonical source |
| --- | --- | --- |
| `strategy_identity` | `StrategyIdentity` | `policy.strategy_identity` |
| `policy_reference` | `str` | `policy.identity.reference` |
| `direction` | `StrategyDirection` | `direction_validation.decision.direction` |
| `entry_price` | `float` | `entry_validation.entry.price` |
| `stop_price` | `float` | `stop_validation.stop.price` |
| `target_price` | `float` | `target_validation.target.price` |
| `risk` | `float` | `rr_outcome.risk` |
| `reward` | `float` | `rr_outcome.reward` |
| `rr` | `float` | `rr_outcome.rr` |
| `confidence` | `float` | `sc.confidence` |
| `evaluation_timestamp` | `str` | `expiration.evaluation_timestamp` |
| `expires_at` | `str` | `expiration.expires_at` |

Every field is derived; the ordinary constructor accepts only `confidence_validation`. E09 copies
the exact canonical values and performs no numeric, text, identity, or timestamp transformation.
It does not recompute the policy fingerprint, normalize prices, derive geometry, divide reward by
risk, compare RR or confidence thresholds, or parse expiration again.

Before publication, minimal structural extraction requires every field to have the exact runtime
type shown, the direction to be BUY or SELL, and the following already-frozen value continuity:

```text
stop_validation.stop.entry_validation == entry_validation
target_validation.target.entry_validation == entry_validation
entry_validation.entry.direction_validation == direction_validation
expiration.strategy_confidence == sc
expiration.request.strategy_identity == policy.strategy_identity
expiration.request.policy_reference == policy.identity.reference
```

These are equality checks, not predecessor recomputation. A missing field, wrong type, malformed
nested state, or mismatch raises `DataIntegrityError`.

For BUY, construction requires only canonical valid `cv` plus final direction BUY. For SELL, it
requires only canonical valid `cv` plus final direction SELL. No E09-specific directional,
geometry, RR, confidence, or expiration acceptance rule exists.

`StrategySignal.reconstruct` accepts `confidence_validation` followed by the twelve serialized
public fields in their documented order. It calls the ordinary constructor, recomputes all twelve
fields from the predecessor chain, and requires exact equality with each supplied field. Any wrong
type or contradiction raises `DataIntegrityError`.

The signal deliberately contains no symbol or instrument field because E00-E08 publish no canonical
instrument identity selected for E09. It contains no diagnostics, validity, closure status,
`generated_at`, `created_at`, `closed_at`, live-expired flag, remaining TTL, broker field, volume,
lot size, order type, or execution instruction.

#### Expiration and timestamp boundary

E09 carries only E08 canonical `evaluation_timestamp` and `expires_at` strings. It owns no new
timestamp and performs no parsing or normalization. It does not evaluate whether the signal is
expired now. No `datetime.now()`, `datetime.utcnow()`, `time.time()`, wall clock, replay clock, or
implicit current time is permitted. Live expiry requires a future authorized runtime boundary with
an explicit immutable comparison timestamp.

#### `SignalDiagnostics` and `SignalValidation`

`SignalDiagnostics` has the sole field `diagnostics: tuple[str, ...]`. The closed vocabulary is
empty and the only canonical state is `()`. Input must be an exact tuple. Non-empty tuples, unknown
or malformed entries, duplicates, and mutable containers raise `DataIntegrityError`. Construction
and reconstruction accept the single tuple field and enforce the same rule. No E02, E03, E07, or
E08 diagnostic is propagated because rejected predecessor validations cannot construct a signal.

`SignalValidation` has exactly these fields in constructor/equality order:

| Field | Exact runtime type | Source and derivation |
| --- | --- | --- |
| `signal` | `StrategySignal` | Caller-supplied exact canonical E09 signal. |
| `valid` | `bool` | Derived exactly `True`. |
| `diagnostics` | `SignalDiagnostics` | Derived exactly `SignalDiagnostics(())`. |

The ordinary constructor accepts only exact `StrategySignal`. A successfully constructed signal is
already the final accepted A07 output, so E09 has no false validation state. `valid=True` means the
signal is structurally canonical, every E00-E08 gate represented in its predecessor chain already
succeeded, and E09 assembly is internally consistent. It does not mean a broker accepted an order,
a trade executed, a position opened, or the signal remains unexpired relative to live time.

`SignalValidation.reconstruct` accepts `signal`, `valid`, and `diagnostics`, requires exact built-in
`bool` and exact `SignalDiagnostics`, derives `True` and empty diagnostics again, and rejects any
contradiction. Round trips preserve equality and hash.

#### Malformed and negative-state classification

| Condition | Exact behavior |
| --- | --- |
| Wrong `ConfidenceValidation` type | Structural `DataIntegrityError`. |
| Non-canonical or `valid=False` `ConfidenceValidation` | Structural `DataIntegrityError`; no signal. |
| E03 `NO_TRADE`, E07 rejection, or E08 rejection | Predecessor pipeline-negative state; no E09 signal. |
| Wrong direction type or `NO_TRADE` in an E09 chain | Structural `DataIntegrityError`. |
| Missing or wrong-type canonical signal field | Structural `DataIntegrityError`. |
| Geometry, identity, policy, confidence, or expiration continuity mismatch | Structural `DataIntegrityError`. |
| Contradictory reconstructed `StrategySignal` field | Structural `DataIntegrityError`. |
| Wrong `StrategySignal` supplied to `SignalValidation` | Structural `DataIntegrityError`. |
| False/non-bool or contradictory validation reconstruction | Structural `DataIntegrityError`. |
| Non-empty, unknown, duplicate, malformed, or mutable diagnostics | Structural `DataIntegrityError`. |
| Expiration relative to external current time | Not evaluated by E09; future/runtime responsibility. |

No structural error becomes `NO_TRADE`, no rejected signal is created, and E09 exposes no
domain-negative validation or diagnostic state.

#### Determinism, predecessor trust, and execution isolation

E09 accepts canonical E08 validation, delegates its canonicality check to E08 reconstruction,
extracts canonical facts, performs only the documented value-continuity and type checks, assembles
the immutable signal, and constructs success-only validation. It never recomputes E02 evidence,
E03 direction, E04 entry, E05 stop, E06 target, E07 risk/reward/RR, or E08 confidence/expiration.

Equivalent value-equal immutable predecessors produce identical signal fields, validation,
diagnostics, equality, hash, and reconstruction. E09 is independent of wall clock, locale,
filesystem, network, environment, market data, providers, broker, MT5, randomness, process state,
mutable globals, registries, and caches.

E09 implements no order creation or submission, broker or MT5 call, lot or position sizing, broker
selection, market/pending order choice, spread or slippage check, execution price, position
management, stop/target modification, or position closure. The final A07 signal is broker-agnostic
and execution-independent.

#### E09 test contract and closure evidence

E09 tests cover exact exports, fields, order, runtime types, and constructor signatures;
valid BUY and SELL signals; `NO_TRADE`, rejected E07, rejected E08, wrong E08 type, and malformed E08
rejection; every canonical source field; exact policy reference and strategy identity; entry, stop,
target, risk, reward, RR, confidence, evaluation timestamp, and expiry copying without
transformation; canonical E08 reconstruction delegation; value-equal independently reconstructed
predecessor acceptance; all continuity mismatches; absent symbol, persistent identity, generated
timestamp, live-expiry, and execution fields; exact-type equality and inequality; hashing;
immutability and nested immutability; signal reconstruction and each field contradiction;
success-only validation; empty diagnostics and rejection of every non-empty or mutable state;
validation reconstruction contradictions; determinism and external-state independence; no
predecessor recomputation; and broker, MT5, execution, position, sizing, spread, and slippage
isolation. The focused E09 suite contributes 62 tests, all passing. E09 statement and branch
coverage are both 100%.

Final accounting is `2581 + 62 = 2643`: PRE-E09 is 2581, the E09 contribution is 62, and POST-E09
is the canonical final A07 collection of 2643. Zero predecessor nodes were removed. E09 was
published as commit `6a83f4d0151ce23a463c6c9297f4cb088cc623b4` with subject
`feat(a07): implement E09 signal closure`. Its focused, predecessor, collection, full-regression,
coverage, static, determinism, immutability, fail-closed, reconstruction, ownership,
execution-isolation, publication, and applicable exact-SHA remote gates passed. E09 is
CLOSED / FROZEN.

#### A07 final-closure and release boundary

E09 closure does not by itself perform A07 final closure. A07 may become COMPLETE / CLOSED / FROZEN
only after E09 closes; E00-E09 are all CLOSED / FROZEN; collection arithmetic reconciles with zero
predecessor removal; the full regression passes; overall coverage meets the repository threshold;
E09 statement coverage is 100% and branch coverage is 100% where measured; EventBus stress, Black,
Ruff, MyPy, `git diff --check`, and all applicable exact-SHA remote workflows pass; the tracked tree
is clean; `HEAD == origin/develop`; no blockers remain; the final package matrix is complete;
required completion documentation is published and validated on its exact commit SHA. Release
preparation and tag-triggered release validation remain separate actions after A07 closure.

Following E00-E09 closure and A07 final governance closure, `v1.6.0` metadata may be prepared.
Creating or pushing the annotated tag, running tag-triggered release validation, and creating the
GitHub release are separate explicitly authorized actions.

#### Final package matrix and closure evidence

| Package | State |
| --- | --- |
| E00 | CLOSED / FROZEN |
| E01 | CLOSED / FROZEN |
| E02 | CLOSED / FROZEN |
| E03 | CLOSED / FROZEN |
| E04 | CLOSED / FROZEN |
| E05 | CLOSED / FROZEN |
| E06 | CLOSED / FROZEN |
| E07 | CLOSED / FROZEN |
| E08 | CLOSED / FROZEN |
| E09 | CLOSED / FROZEN |

The final technical evidence is published in
[`A07_COMPLETION_EVIDENCE.md`](A07_COMPLETION_EVIDENCE.md). The artifact, this reconciled plan, and
the reconciled roadmap passed all applicable exact-SHA remote gates on governance commit
`246e34770c4f3c7c3de5fa95911deab4670dc047`. A07 is COMPLETE / CLOSED / FROZEN.

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
feat(a07): implement E09 signal closure
```

After local validation, commit, push to `origin/develop`, verify exact-SHA remote gates,
then mark the unit CLOSED/FROZEN. Frozen predecessors cannot be silently modified.

## 10. Release model

`v1.6.0` version metadata, changelog, roadmap state, and release notes may be prepared after A07
closure. The annotated tag, tag push, tag-triggered release validation, and GitHub release remain
separate explicitly authorized actions.

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

E00-E09 are COMPLETE only when their contracts, tests, quality gates, coverage, and boundaries
pass. They are CLOSED only after exact authorized-file commit, publication, remote verification,
and clean tracked-tree inspection. A07 is COMPLETE only after all units close and its completion
documentation is published and validated on the exact synchronized SHA. Release preparation and
tag-triggered release verification follow under separate authorization.
