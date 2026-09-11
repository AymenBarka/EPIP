# P04-F00-R02 Normative Configuration Reconciliation

## Decision

P04-F00-R02 is **CLOSED / FROZEN**. It changes no R00 strategy rule. P04-F00 remains blocked only
until P02-R02-I00 is implemented and frozen.

## Policy and freshness

For `elliott-fibonacci-wave3@1.0.0`, `StrategyPolicy.expiration_seconds` is exactly `300` seconds.
It is a post-evaluation signal-validity window, not bar lifetime, analytical freshness, or an
execution guarantee. Five minutes is independent of instrument and bar duration: it limits how
long a completed evaluation may be acted upon. It is stored configuration and reads no clock, so
replay remains deterministic.

All seven required evidence policies use `FreshnessBasis.AVAILABILITY` and
`max_age_seconds == 0`. Elliott, Fibonacci and market-structure evidence use this same synchronous
snapshot rule; entry, stop, target and confidence evidence inherit their selected sources. The
frozen comparison is inclusive: `0 <= int(age_seconds) <= 0`; future timestamps are invalid and
missing required evidence is rejected. This is not a number of bars and remains timeframe agnostic.

P04 declares `bind_primary_timeframe=True`, PRIMARY as its sole role, and no configured concrete
timeframe. P02-R02-I00 binds the exact caller value. No wildcard, sentinel, or P05 behavior exists.

## Rule identity convention

Every identity is `RuleIdentity(rule_id, "1.0.0", "p02-f00-v1", fingerprint)`. Every rule ID has
the prefix `p04.elliott-fibonacci-wave3.`. The complete suffix inventory is:

| Family | Exact suffixes |
| --- | --- |
| `SOURCE_EXTRACTION` | `extract.elliott`, `extract.fibonacci`, `extract.market-structure` |
| `APPLICABILITY` | `applicability.elliott-wave3`, `applicability.fibonacci-wave3`, `applicability.direction`, `applicability.entry`, `applicability.stop`, `applicability.target`, `invalidation.wave3` |
| `CANDIDATE_SELECTION` | `select.wave1-anchor`, `select.entry`, `select.stop`, `select.target` |
| `CANDIDATE_RANKING` | `rank.entry-golden-zone`, `rank.target-extension-1618` |
| `BOUNDARY_SELECTION` | `boundary.entry-0618-0705` |
| `PRECEDENCE` | `precedence.stop-wave1-origin` |
| `PRICE_TRANSFORMATION` | `transform.stop-identity`, `transform.target-extension-1618` |
| `DIRECTION_MAPPING` | `direction.elliott`, `direction.trend`, `direction.structure`, `direction.primary`, `direction.alternate` |
| `MTF_AGGREGATION` | `direction.caller-primary-identity` |
| `CONFIDENCE` | `confidence.elliott-fibonacci-60-40` |
| `TEMPORAL_ELIGIBILITY` | `evidence.validity`, `evidence.revision` |
| `EVIDENCE_MAPPING` | `evidence.elliott-wave3-setup`, `evidence.fibonacci-w1-anchor`, `evidence.structure-direction-alignment`, `evidence.entry-golden-0618-0705`, `evidence.stop-wave1-origin`, `evidence.target-extension-1618`, `evidence.confidence-elliott-fibonacci-60-40` |
| `EVIDENCE_ORDERING` | `evidence.ordering` |

P04 owns fingerprint construction. Each fingerprint is SHA-256 over UTF-8 canonical JSON with
ASCII escaping, sorted object keys and separators `(',', ':')`. Numbers are normalized decimal
strings, tuples are arrays, and sets are forbidden. The exact payload shape is:

```json
{"domain":"epip.p04.semantic-rule.v1","family":"<family>","profile":"elliott-fibonacci-wave3@1.0.0","rule_id":"<complete-rule-id>","rule_version":"1.0.0","semantics":["<ordered governed clauses>"]}
```

The ordered `semantics` clauses are only the applicable subset of: exact contiguous same-degree
W1/W2 with valid primary, zero violations, empty alternates and next WAVE_3; Fibonacci anchors equal
ordered W1 start/end; closed direction mapping; inclusive entry 0.618/0.705; W1-origin identity
stop; direction-aware 1.618 target; confidence 0.60 Elliott plus 0.40 Fibonacci; required
availability freshness zero seconds on PRIMARY; or the exact evidence key operated upon. Mechanical
rules use their named operation and consumed constants. The ordering rule includes these keys in
this exact order:

1. `elliott.wave3_setup`
2. `fibonacci.w1_anchor`
3. `structure.direction_alignment`
4. `entry.golden_0618_0705`
5. `stop.wave1_origin`
6. `target.extension_1618`
7. `confidence.elliott_fibonacci_60_40`

F00 computes each value once at import through the existing pure canonical JSON/SHA-256 convention
and exposes immutable `RuleIdentity` values. It does not store arbitrary digests, add an identity
framework, or hash source code. Later implementation cannot change an identity unless governed
semantics change.

## Adequacy

After P02-R02-I00, existing StrategyPolicy, FreshnessPolicy, RuleIdentity,
StrategySemanticMappingProfile, P01, P03 and A07 contracts suffice. F00 remains inside its four
authorized production files and one test file, declaring immutable objects only. ADR-0029 is
required for reusable P02 caller binding; no separate P04 ADR is needed.
