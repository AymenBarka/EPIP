# P04 Governance Authorization

## Decision and objective

P04 governance is **AUTHORIZED**. Only P04-F00 is **AUTHORIZED / READY FOR IMPLEMENTATION**;
P04-F01 through P04-F04 and P05 remain **NOT AUTHORIZED**. This milestone changes documentation
only and does not implement a strategy, rule, profile, or package.

P04 will implement one deterministic concrete Elliott/Fibonacci wave-3 strategy profile that
supplies the frozen P02 adapter, P03 runtime, and A07 decision pipeline with exact strategy-specific
rules and configuration. P04 is a profile provider, never a runtime, adapter framework, decision
pipeline, analytical engine, or execution system.

This authorization adopts `P04_R00_ELLIOTT_FIBONACCI_SETUP_RECONCILIATION.md` exactly. R00 is the
normative semantic authority where this program document summarizes its values.

## Frozen canonical setup

The only initial setup is a single-frame wave-3 continuation after completed W1 and corrective W2:

- the primary count is `VALID`, has zero violations and empty alternates;
- its sequence is exactly contiguous, same-degree `WAVE_1`, `WAVE_2` with W2 opposing W1;
- its projection exists and names `WAVE_3` next;
- `UP` W1 plus aligned bullish structure maps to `BUY`;
- `DOWN` W1 plus aligned bearish structure maps to `SELL`;
- neutral, range, unsupported, or contradictory complete facts map to `NO_TRADE`;
- Fibonacci retracement and extension anchors exactly equal ordered W1 start then W1 end;
- entry is the inclusive `0.618`-`0.705` golden zone with exactly one `ENTRY` level inside;
- stop is W1 origin with no buffer;
- target is the exact direction-aware W1 `1.618` extension;
- `StrategyPolicy.minimum_rr` is `3.0`;
- confidence is `0.60 * Elliott primary probability + 0.40 * Fibonacci confluence`; and
- `StrategyPolicy.minimum_confidence` is `0.70`, inclusive.

Market structure is mandatory. EMA, ADX, RSI, ATR, context phase/bias, liquidity, swing, Decision,
Kernel, alternate-count, wave-5, post-ABC, and every multi-frame strategy semantic are excluded.

## Existing contracts and boundaries

No new public contract or predecessor change is authorized. Existing contracts are sufficient:

- P01 `StrategyProfile` and exact registry resolution provide profile identity and compatibility;
- A07 `StrategyPolicy` provides RR/confidence thresholds, directions, evidence policy, precision,
  expiration, and Elliott policy content;
- P02 `StrategySemanticMappingProfile`, rule identities, declarations, requests/results, resolved
  rule set, source binding, adapter and evidence machinery express the complete profile;
- `StrategyFactBundle` carries caller-authoritative A07 facts; and
- P03 `StrategyRuntime` executes the configured adapter and frozen A07 E00-E09.

P04 owns concrete profile identity/version, immutable configuration, Elliott eligibility,
Fibonacci extraction and anchor binding, structure alignment, direction mapping, geometry candidate
rules, confidence inputs/weights, invalidation choices, evidence taxonomy, and explainability
bindings.

P04 does not own P02 adaptation, source resolution, freshness, temporal/revision validation,
candidate mechanics, evidence ordering/identity, or adapter states. It does not own P03
orchestration/states, A07 sequencing/RR calculation/final confidence acceptance, serialization
infrastructure, analytical production, MTF interpretation, capital sizing, execution, broker/MT5,
positions, persistence, scheduling, telemetry, or deployment.

## Package and identity

The full P04 production package is exactly:

```text
epip/strategy_profiles/__init__.py
epip/strategy_profiles/elliott_fibonacci/__init__.py
epip/strategy_profiles/elliott_fibonacci/configuration.py
epip/strategy_profiles/elliott_fibonacci/profile.py
epip/strategy_profiles/elliott_fibonacci/elliott_rules.py
epip/strategy_profiles/elliott_fibonacci/fibonacci_rules.py
epip/strategy_profiles/elliott_fibonacci/direction_rules.py
epip/strategy_profiles/elliott_fibonacci/geometry_rules.py
epip/strategy_profiles/elliott_fibonacci/confidence_rules.py
epip/strategy_profiles/elliott_fibonacci/evidence_rules.py
epip/strategy_profiles/elliott_fibonacci/binding.py
```

No other production module is implied. The package may import public P01/P02/A07 and analytical
contracts but must not modify or duplicate them.

The exact strategy/profile/policy identity is `elliott-fibonacci-wave3@1.0.0`. P02 semantic profile
and executable rules use exact `1.0.0` identities/fingerprints. Lookup is exact only: no alias,
latest, compatibility fallback, dynamic discovery/import, filesystem/environment selection, or
mutable registration.

## Configuration ownership

`configuration.py` contains only immutable named scalar/tuple constants: entry ratios `0.618` and
`0.705`, target ratio `1.618`, minimum RR `3.0`, Elliott weight `0.60`, Fibonacci weight `0.40`,
minimum confidence `0.70`, the exact identity/version, required PRIMARY role/source domains, and
the seven ordered evidence keys. No new configuration record is authorized.

`profile.py` constructs existing immutable `StrategyIdentity`, `StrategyProfile`, `StrategyPolicy`,
P02 semantic-profile declarations and exact references. Values that A07 owns reside in
`StrategyPolicy`; selector/rule/evidence references reside in the P02 semantic profile; P04-only
constants reside in `configuration.py`. Fingerprints transitively bind the content.

## Rule contracts and outcome mapping

| Rule | Owner | Existing input | Existing output | Frozen configuration | Failure path |
| --- | --- | --- | --- | --- | --- |
| Elliott eligibility | P04 | `WaveSnapshot` | semantic candidates/direction | exact W1/W2/W3 predicates | P02 REJECTED |
| Fibonacci eligibility | P04 | `FibonacciSnapshot` | anchor/zone/extension candidates | 0.618, 0.705, 1.618 | P02 REJECTED |
| Anchor binding | P04 | combined candidates | exact selected subset | ordered W1 equality and lineage | P02 REJECTED |
| Structure alignment | P04 | `MarketStructureSnapshot` | direction candidate | UPTREND/DOWNTREND; neutral otherwise | NO_TRADE; missing/malformed REJECTED |
| Direction | P04/A07 | Elliott/structure candidates | six `DirectionalFacts` values | closed UP/DOWN mapping | NO_SIGNAL or REJECTED |
| Entry | P04/A07 | coherent golden-zone candidates | `EntryFacts` | inclusive 0.618-0.705 | P02 REJECTED; A07 constructs |
| Stop | P04/A07 | W1-origin candidate | `StopFacts` | identity transform, no buffer | P02 REJECTED; A07 validates |
| Target | P04/A07 | extension candidates | `TargetFacts` | exact 1.618 | P02 REJECTED; A07 validates |
| RR | A07 E07 | entry/stop/target | canonical RR outcome | minimum 3.0 | A07_REJECTION |
| Confidence | P04/P02/A07 | probability/confluence | `[0,1]` scalar | weights 0.60/0.40; minimum 0.70 | missing REJECTED; low A07_REJECTION |
| Invalidation | P04/P02 | governed candidates | terminal adapter mapping | R00 taxonomy | INVALID_INPUT/REJECTED |
| No trade | P04/A07/P03 | complete nonactionable facts | existing runtime result | closed direction mapping | NO_SIGNAL |

Malformed type, schema, identity, instrument, time, revision, provenance, or request data follows
the frozen `INVALID_INPUT` path. Missing semantic facts, invalid Elliott setup, anchor mismatch,
outside-zone ENTRY, invalid stop ordering, or incomplete evidence is P02 `REJECTED`. Complete
neutral/contradictory structure is accepted and becomes runtime `NO_SIGNAL`. Low RR or confidence
is `A07_REJECTION`. Unexpected rule failure follows P02 `FAILED` to runtime `ADAPTER_FAILURE`.

## Evidence and explainability

The exact required P02 evidence order is:

1. `elliott.wave3_setup`
2. `fibonacci.w1_anchor`
3. `structure.direction_alignment`
4. `entry.golden_0618_0705`
5. `stop.wave1_origin`
6. `target.extension_1618`
7. `confidence.elliott_fibonacci_60_40`

Each item retains selected candidate, source binding, rule identity, evidence identity, and
provenance continuity through existing P02/A07 contracts. BUY and SELL therefore require typed,
identity-bound evidence for the setup, anchors, structure, geometry and confidence; free text alone
is never acceptance evidence.

## Single-frame and deterministic model

One closed PRIMARY frame is necessary and sufficient. The MTF result is an identity over that
frame's primary direction. Higher/lower frames, confirmation, voting, hierarchy and priority remain
P05. The strategy is instrument/timeframe agnostic; symbols, timeframe labels and fixture prices do
not enter architecture.

All P04 objects and rules are immutable or stateless, synchronous, deterministic and safe for
concurrent invocation. Clock, random, UUID generation, I/O, network, filesystem configuration,
environment selection, mutable globals and caches are forbidden. Existing canonical serializers
are reused; no serializer or schema fork is authorized.

## Authorized program slices

### P04-F00 — profile and configuration foundation

**State:** AUTHORIZED / READY FOR IMPLEMENTATION.

Objective: create only the package shells, immutable constants, exact existing-contract profile and
policy construction, semantic identities/references, source/evidence declarations, and a
deterministic registry-ready profile object. It must not inspect analytical snapshots, implement an
`ExecutableSemanticRule`, derive candidates/directions/geometry/confidence/evidence, construct an
adapter, or invoke P02/P03/A07.

Authorized production files are exactly:

```text
epip/strategy_profiles/__init__.py
epip/strategy_profiles/elliott_fibonacci/__init__.py
epip/strategy_profiles/elliott_fibonacci/configuration.py
epip/strategy_profiles/elliott_fibonacci/profile.py
```

Authorized test file is exactly:

```text
tests/strategy_profiles/elliott_fibonacci/test_profile.py
```

Inputs are R00 constants and existing P01/P02/A07 contract constructors. Outputs are exact immutable
profile/policy/declaration objects only. Closure requires exact identity/fingerprint/reference
coherence, values, source requirements, evidence order, rule manifest declarations, immutability,
deterministic equality/hash where supported, exact resolution behavior, package isolation, no
dynamic selection, serialization regression, collection accounting, compliance forecast/actual,
predecessor regressions, coverage and exact-SHA remote gates.

### P04-F01 — Elliott/Fibonacci eligibility and anchors

**State:** NOT AUTHORIZED. Future files: `elliott_rules.py`, `fibonacci_rules.py`; future test:
`test_setup_rules.py`. It consumes F00 declarations plus existing `WaveSnapshot` and
`FibonacciSnapshot`, and emits typed setup/anchor/zone/extension candidates through existing P02
rule contracts. It owns the bullish/bearish Elliott lifecycle, anchor equality, ENTRY membership,
and their invalid/rejected fixtures. F00 may declare these rule identities but must not implement
their behavior.

### P04-F02 — direction and geometry mapping

**State:** NOT AUTHORIZED. Future files: `direction_rules.py`, `geometry_rules.py`; future test:
`test_direction_geometry.py`. It consumes F01 candidates plus market structure and emits exact
direction, entry, stop, and target semantic results. It owns BUY/SELL/NO_TRADE, inclusive boundary,
W1-origin stop, 1.618 target, invalid ordering and geometry tests.

### P04-F03 — confidence, invalidation and evidence

**State:** NOT AUTHORIZED. Future files: `confidence_rules.py`, `evidence_rules.py`; future test:
`test_confidence_evidence.py`. It implements the exact 60/40 model, required evidence mapping/order,
temporal eligibility declarations, invalidation terminal mappings and threshold-boundary evidence.
It does not calculate authoritative RR or confidence acceptance.

### P04-F04 — integration and final closure

**State:** NOT AUTHORIZED. Future production file: `binding.py`; future tests:
`test_integration.py`, `test_closure.py`. It composes the exact resolved rule set and existing
`CanonicalFactAdapter`, exercises frozen P02/P03/A07 end to end, proves deterministic repeat and
shared-runtime concurrency, closes regressions/API/purity/compliance/successor evidence, and creates
the final P04 closure record. It adds no second adapter/runtime/result/state.

Order is F00 -> F01 -> F02 -> F03 -> F04. Each slice requires separate governance authorization
and predecessor freeze. No later-slice behavior may be pulled into an earlier slice.

## Golden fixtures and final test contract

F00 tests configuration only. F01 owns the underlying W1/W2 and Fibonacci candidate forms. F02 owns
the final geometry and NO_TRADE behavior. F03 owns confidence/evidence thresholds. F04 owns complete
runtime outcomes.

- bullish: W1 `100 -> 110`, W2 end `103.82`, entry `[102.95, 103.82]`, stop `100`, target `116.18`;
- bearish: W1 `110 -> 100`, W2 end `106.18`, entry `[106.18, 107.05]`, stop `110`, target `93.82`;
- no trade: complete bullish geometry with market structure `RANGE`.

The final matrix includes valid BUY, SELL and NO_SIGNAL; invalid Elliott, anchors, outside-zone
entry and stop geometry; RR below/equal/above 3.0; confidence below/equal/above 0.70; identity,
evidence ordering, deterministic repeat, immutability, concurrency/statelessness, P02/P03/A07
integration, serialization regression, package/API/purity and successor isolation. Every slice also
preserves frozen P02, P03, A07, Elliott and Fibonacci regressions with zero predecessor removals.

## Final closure and P05

P04 becomes **COMPLETE / CLOSED / FROZEN** only when F00-F04 are individually closed/frozen; the
canonical setup and full matrix pass; no predecessor changes; one-frame/P05 isolation and
determinism are proven; aggregate coverage is at least 95%; compliance and documentation are valid;
exact-SHA Quality, CodeQL and Documentation pass; and no normative ambiguity remains.

Successful P04 closure makes P05 **READY FOR AUTHORIZATION**, not authorized. No new ADR is needed:
P04 implements concrete content within the already accepted architecture.
