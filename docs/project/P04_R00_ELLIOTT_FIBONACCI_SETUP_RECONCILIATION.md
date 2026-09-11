# P04-R00 Elliott/Fibonacci Setup Reconciliation

## Decision

P04-R00 is **CLOSED / FROZEN**. It resolves the analytical-adequacy blocker without changing P01,
P02, A07, P03, or an analytical producer. P04 is **READY FOR GOVERNANCE AUTHORIZATION**; no P04
implementation and no P05 work is authorized by this record.

The one initial P04 setup is a deterministic, single-frame **wave-3 continuation after a completed
wave-2 correction**. Bullish and bearish are exact mirrors. No wave-5, completed-impulse reversal,
post-ABC, diagonal, alternate-count, or multi-timeframe setup belongs to the initial profile.

## Existing-contract adequacy

The existing contracts are sufficient. No new P04 public value contract is required:

- `StrategyProfile` owns exact profile identity, compatibility, sources, evidence, and semantic
  references;
- `StrategyPolicy` owns enabled directions, minimum RR, minimum confidence, evidence requirements,
  expiration, precision, and the frozen Elliott policy declaration;
- `StrategySemanticMappingProfile`, `ResolvedSemanticRuleSet`, and P02 rule requests/results express
  exact selectors, candidates, cross-candidate selection, confidence, evidence, and failure paths;
- `StrategyFactBundle` carries the complete caller-authoritative A07 facts; and
- frozen A07 and `StrategyRuntime` remain the final decision and orchestration authorities.

P02 source extraction remains source-local. Elliott and Fibonacci extractors emit typed candidates
with their source and provenance identities. Existing geometry selection requests then receive the
combined candidate population and prove anchor equality before selecting geometry. Nothing new must
flow through a frozen P02 request.

## Canonical Elliott lifecycle

The initial setup uses the current public `WaveSnapshot` as follows:

1. the primary sequence contains exactly two ordered waves, `WAVE_1` then `WAVE_2`;
2. its `WavePattern.UNKNOWN` value means only that the analytical producer has not observed five
   completed impulse legs; P04 interprets this exact two-leg prefix as a candidate progression, not
   as a completed impulse;
3. both waves have one degree, contiguous indices and timestamps, and W2 starts at W1's endpoint;
4. W1 is the completed motive leg and W2 is the completed correction;
5. W2 must not cross W1's origin, and the primary count must be `VALID` with no violations;
6. the projection must exist and name `WAVE_3` as `next_wave`; and
7. setup activation means all Elliott predicates, anchor continuity, entry eligibility, structure
   alignment, geometry, RR, and confidence requirements are satisfied.

A full W1-W5 impulse is explicitly not required and is not eligible for this setup. ABC, diagonals,
empty/partial one-wave sequences, additional waves, noncontiguous waves, and any violation are not
eligible. No minimum Elliott quality is imposed separately; Elliott probability enters confidence.
Primary alternates must be empty. Supporting an alternate count requires a future profile version.

### Closed direction mapping

P04 accepts the upstream wave direction strings `UP` and `DOWN` only. `UP` maps to `BUY`; `DOWN`
maps to `SELL`; every other string maps to `NO_TRADE`. W1 must be `UP` and W2 `DOWN` for BUY, or W1
`DOWN` and W2 `UP` for SELL. This closed P04 rule does not change the free-text upstream contract.

For an actionable bundle, all six A07 directional facts must agree:

- Elliott and primary: W1 direction;
- alternate: the primary direction because alternates are required to be empty;
- trend: `UPTREND` to BUY and `DOWNTREND` to SELL;
- structure: `UPTREND` to BUY and `DOWNTREND` to SELL; and
- MTF: an identity rule over the single PRIMARY-frame primary direction.

`RANGE`, `UNKNOWN`, accumulation/distribution, missing alignment, or any contradiction produces a
valid strategy-negative `NO_TRADE` direction when the required bundle can still be constructed.

## Elliott-to-Fibonacci anchor continuity

W1 supplies the sole anchor pair. The ordered anchors are W1 start then W1 end. For BUY they are
low-to-high; for SELL they are high-to-low. The Fibonacci snapshot must have the same instrument,
timeframe and governed source/provenance binding, and both its retracement and extension
`start_price`/`end_price` must exactly equal those W1 prices using exact finite-float equality.

Its direction must be `BULLISH` for BUY and `BEARISH` for SELL. Every emitted anchor candidate
retains its Elliott or Fibonacci source binding ID and provenance reference; P02 candidate and
evidence identities preserve these values. Missing, reordered, numerically unequal, differently
directed, or differently bound anchors are an anchor mismatch. No tolerance or guessed anchor is
allowed.

## Geometry and policy

All ratios and thresholds below are immutable named P04 configuration values included transitively
in exact rule/profile/policy identities. They are not implicit defaults or scattered literals.

### Entry

The required entry zone is the Fibonacci golden retracement interval, inclusive, from ratio
`0.618` through `0.705` of W1. The snapshot must contain exactly one `GoldenZone` whose bounds equal
the prices derived from those ratios and exactly one `FibonacciLevel` labelled `ENTRY`. The ENTRY
price must lie inside the closed zone. The P04 entry fact is the entire zone; frozen A07 chooses the
BUY upper bound or SELL lower bound and performs policy precision rounding.

### Stop

The only stop is W1's origin: W1 `start_price`. It must be below the A07 BUY entry or above the A07
SELL entry. The initial profile uses an identity price transformation: no offset, ATR, volatility,
spread, tick, swing, or discretionary buffer.

### Target

The only target is the W1 `1.618` Fibonacci extension, calculated from the same ordered anchor pair.
The snapshot must contain exactly one extension level with ratio `1.618`; its price must equal the
canonical projection and lie above a BUY entry or below a SELL entry. P04 selects structural
geometry; it never moves the target merely to satisfy RR.

### Reward/risk

`StrategyPolicy.minimum_rr` is exactly `3.0`. It is only an acceptance threshold. Frozen A07 E07
calculates risk, reward, and RR and accepts equality (`RR >= 3.0`). A structurally selected target
below the threshold reaches `A07_REJECTION`; P04 does not recompute or repair it.

### Confidence

The P02 weighted confidence model has exactly two required inputs:

```text
confidence = 0.60 * Elliott primary probability
           + 0.40 * Fibonacci snapshot confluence_score
```

Inputs are already normalized to `[0, 1]`; no calibration or quality conversion is applied. The
result is evaluated by frozen A07 against `StrategyPolicy.minimum_confidence == 0.70`, inclusive.
Missing either input prevents a complete mapping and is `REJECTED`. A computed value below `0.70`
forms a complete bundle but is rejected by A07. Market-structure confidence is not an input.

## Context and indicators

| Input | Initial status | Use |
| --- | --- | --- |
| Elliott | MANDATORY | Setup, direction, W1 anchors, stop, probability |
| Fibonacci | MANDATORY | Anchor confirmation, entry, target, confluence |
| Market structure | MANDATORY | Trend and structure directional alignment |
| Market context | NOT USED | No phase or bias filter |
| Liquidity | NOT USED | Already upstream of Fibonacci; no P04 rule |
| Swing | NOT USED | Already upstream of structure/Fibonacci/Elliott |
| Decision/Core Kernel | NOT USED | No alternate final authority |
| EMA, ADX, RSI, ATR | DEFERRED | Not canonical initial-profile inputs |

The profile is instrument- and timeframe-agnostic. It requires exactly one closed PRIMARY frame;
instrument names and timeframe labels are fixture/configuration data, never strategy architecture.

## Outcome and invalidation taxonomy

| Condition | Frozen path |
| --- | --- |
| Wrong type/schema/identity/instrument/time/revision/provenance or malformed contract | P02 `INVALID_INPUT` -> runtime `INVALID_INPUT` |
| Missing required Elliott, Fibonacci, structure, confidence, geometry, or evidence candidate | P02 `REJECTED` -> runtime `REJECTED` |
| Fibonacci anchor or direction mismatch | P02 `REJECTED` -> runtime `REJECTED` |
| ENTRY marker outside the golden zone or duplicate required candidate | P02 `REJECTED` -> runtime `REJECTED` |
| W2 crosses W1 origin, wave continuity fails, violation exists, or stop ordering is invalid | P02 `REJECTED` -> runtime `REJECTED` |
| Well-formed two-wave setup but structure/trend is neutral or contradictory | accepted facts -> A07 nonactionable direction -> runtime `NO_SIGNAL` |
| Unsupported upstream direction text with otherwise complete facts | accepted facts with `NO_TRADE` -> runtime `NO_SIGNAL` |
| Canonical RR below `3.0` | accepted facts -> A07 E07 rejection -> runtime `A07_REJECTION` |
| Canonical confidence below `0.70` | accepted facts -> A07 E08 rejection -> runtime `A07_REJECTION` |
| Unexpected rule implementation exception | P02 `FAILED` -> runtime `ADAPTER_FAILURE` |

`NO_SIGNAL` therefore means structurally valid and completely mapped facts with no actionable
direction. `REJECTED` means the profile cannot produce a complete trustworthy fact bundle.
`A07_REJECTION` means a complete actionable bundle failed a frozen A07 gate. No state is added.

## Evidence and explainability

The required evidence taxonomy contains these canonically ordered keys:

1. `elliott.wave3_setup` — exact W1/W2 progression, status, projection, direction and provenance;
2. `fibonacci.w1_anchor` — exact anchor equality, direction and provenance;
3. `structure.direction_alignment` — trend/structure mapping and provenance;
4. `entry.golden_0618_0705` — ENTRY membership and selected zone;
5. `stop.wave1_origin` — selected invalidation source and identity transform;
6. `target.extension_1618` — selected extension source;
7. `confidence.elliott_fibonacci_60_40` — both selected inputs and model identity.

All are required and fresh/temporally eligible under explicit P02 policies. RR and final confidence
acceptance remain reconstructable from the bundle and A07 predecessor chain. Non-actionability and
rejection are exposed through existing deterministic diagnostics; no new diagnostic vocabulary is
authorized.

## Canonical synthetic fixtures

Prices below are exact illustrative fixture values; instrument and timeframe are arbitrary coherent
values and do not become profile configuration.

| Fixture | W1 | W2 end | Golden zone | ENTRY | Stop | 1.618 target | Structure | Confidence inputs | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bullish | `100.0 -> 110.0` (`UP`) | `103.82` (`DOWN`) | `[102.95, 103.82]` | `103.50` | `100.0` | `116.18` | UPTREND | `0.80`, `0.80` | ACCEPTED_SIGNAL |
| Bearish | `110.0 -> 100.0` (`DOWN`) | `106.18` (`UP`) | `[106.18, 107.05]` | `106.50` | `110.0` | `93.82` | DOWNTREND | `0.80`, `0.80` | ACCEPTED_SIGNAL |
| No trade | bullish geometry above | `103.82` | `[102.95, 103.82]` | `103.50` | `100.0` | `116.18` | RANGE | `0.80`, `0.80` | NO_SIGNAL |

Every fixture uses an exact W1/W2 sequence, `VALID`, no violations, empty alternates, and a W3
projection. The fixture policy precision is two decimals. Test calculation must use the repository's
canonical decimal/rounding behavior rather than binary-float approximations.

Required failure fixtures mutate one fact at a time: invalid count/violation, unequal Fibonacci
anchor, ENTRY outside the inclusive zone, W2 beyond origin or stop on the wrong side, target causing
RR below `3.0`, and weighted confidence below `0.70`. Their outcomes are exactly those in the
taxonomy above.

## Package boundary and versioning

Future P04 production belongs only under:

```text
epip/strategy_profiles/elliott_fibonacci/
```

The parent `epip.strategy_profiles` package is a profile-provider namespace, not a runtime or
adapter replacement. The initial identities are:

- strategy: `elliott-fibonacci-wave3@1.0.0`;
- P01 profile: `elliott-fibonacci-wave3@1.0.0` with its canonical fingerprint;
- A07 policy: `elliott-fibonacci-wave3@1.0.0` with its canonical fingerprint; and
- P02 semantic profile and every executable rule: exact version `1.0.0` identities and fingerprints.

Resolution is exact identity only. There is no alias, latest, fallback, environment selection,
filesystem discovery, registry mutation, or dynamic import. Configuration consists of immutable
module constants plus existing immutable profile/policy objects and P02 rule declarations.

## Rule ownership matrix

| Rule | Owner | Input | Output | Configuration | Failure outcome |
| --- | --- | --- | --- | --- | --- |
| Elliott applicability | P04 | `WaveSnapshot` | setup candidates | W1/W2/W3 predicates | REJECTED |
| Fibonacci applicability | P04 | `FibonacciSnapshot` | anchor/zone/extension candidates | 0.618, 0.705, 1.618 | REJECTED |
| Anchor binding | P04 | combined Elliott/Fibonacci candidates | selected coherent candidates | exact W1 equality | REJECTED |
| Direction | P04 | Elliott and structure candidates | six `StrategyDirection` facts | closed mappings | NO_TRADE or REJECTED |
| Entry | P04 -> A07 | coherent golden-zone candidates | `EntryFacts` | inclusive 0.618-0.705 | REJECTED; A07 constructs entry |
| Stop | P04 -> A07 | W1-origin candidate | `StopFacts` | identity/no buffer | REJECTED; A07 validates |
| Target | P04 -> A07 | extension candidates | `TargetFacts` | 1.618 | REJECTED; A07 validates |
| RR | A07 E07 | canonical entry/stop/target | RR outcome | policy minimum 3.0 | A07_REJECTION |
| Confidence | P04/P02 -> A07 | probability and confluence | `[0,1]` scalar | 0.60/0.40; minimum 0.70 | REJECTED if missing; A07_REJECTION if low |
| Invalidation | P04/P02 | setup candidates | terminal mapping | taxonomy above | INVALID_INPUT/REJECTED |
| No trade | P04/A07/P03 | complete neutral/contradictory facts | existing result | closed direction rules | NO_SIGNAL |

## Frozen future test contract

P04 tests must prove: bullish and bearish fixtures; the complete valid NO_SIGNAL fixture; invalid
Elliott state and every continuity predicate; anchor direction/order/value/provenance mismatch;
inclusive entry boundaries and outside-zone rejection; W1-origin stop and invalid ordering; exact
1.618 target; RR below/equal/above 3.0; confidence below/equal/above 0.70 and exact 60/40 formula;
profile/policy/rule identities; exact resolution; deterministic repeat and concurrent use; immutable
input preservation; complete ordered evidence; P02 adapter, P03 runtime and A07 integration; package
API, purity, serialization regression, compliance and successor isolation. Fixtures are synthetic,
immutable, local, clock-free, random-free and network-free.

## Implementation sequence

| Slice | State after R00 | Objective | Future production files | Future tests | Predecessor and freeze gate |
| --- | --- | --- | --- | --- | --- |
| P04-F00 | READY FOR IMPLEMENTATION AUTHORIZATION | Exact constants, identities, profile/policy factory, rule manifest skeleton | `epip/strategy_profiles/__init__.py`; `epip/strategy_profiles/elliott_fibonacci/__init__.py`; `configuration.py`; `profile.py` | `tests/strategy_profiles/elliott_fibonacci/test_profile.py` | R00; exact fingerprint/closure/API tests |
| P04-F01 | NOT AUTHORIZED | Elliott lifecycle, direction, Fibonacci extraction and anchor rules | `elliott_rules.py`; `fibonacci_rules.py`; `direction_rules.py` | `test_setup_rules.py` | F00 frozen; bullish/bearish/no-trade and failure matrix |
| P04-F02 | NOT AUTHORIZED | Entry, stop, target, confidence and evidence rules | `geometry_rules.py`; `confidence_rules.py`; `evidence_rules.py` | `test_geometry_confidence_evidence.py` | F01 frozen; exact geometry/threshold/evidence gates |
| P04-F03 | NOT AUTHORIZED | Compose resolved rule set and generic adapter/runtime integration | `binding.py` | `test_integration.py` | F02 frozen; P02/P03/A07 end-to-end matrix |
| P04-F04 | NOT AUTHORIZED | Determinism, API, compliance, regression and final closure evidence | none expected | `test_closure.py` | F03 frozen; all local/remote closure gates |

No slice may change P01, P02, A07, P03, or analytical producers. Each requires separate
authorization. P04-F00 is only ready to be reviewed for implementation authorization; this record
does not authorize it.

## Final closure and successor consequence

P04 may become **COMPLETE / CLOSED / FROZEN** only after all five slices close; every canonical and
failure fixture passes; identities, evidence, determinism, immutability, single-frame and successor
isolation are proven; P01/P02/A07/P03 regressions remain green; aggregate coverage is at least 95%;
compliance and documentation gates pass; exact-SHA Quality, CodeQL and Documentation pass; and no
normative ambiguity remains.

The initial setup needs one PRIMARY frame only. Its MTF rule is a structural identity over that
single primary direction, not cross-frame confirmation. P05 remains **NOT AUTHORIZED**. Successful
future P04 closure will make P05 **READY FOR AUTHORIZATION** so a later profile version may govern
actual multi-timeframe semantics.

No ADR is required: R00 selects concrete strategy content inside the accepted ADR-0016/0018/0019
architecture and creates no new architectural boundary.
