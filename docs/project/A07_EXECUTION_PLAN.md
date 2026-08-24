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
