# ADR-0018: Typed Strategy Mapping and Analytical Availability Boundaries

## Status

Accepted

## Context

ADR-0016 assigns analysis-to-A07 mapping to the Strategy Fact Adapter/Profile boundary. ADR-0017
freezes P01 transport, provenance, coherence, profile-reference, result, and serialization
contracts. The P02 readiness audit found that P01 can validate a completed `StrategyFactBundle`,
but cannot itself prove instrument identity, availability, revision legality, typed per-timeframe
content, or the rules used to produce that bundle.

Reopening P01 would invalidate a closed milestone. Encoding Elliott/Fibonacci or MTF choices in a
universal adapter would move P04/P05 authority into P02. An additive, strategy-neutral contract
foundation is required.

## Decision

The milestone is **P02-F00 — Additive Strategy Mapping Foundation**. It composes new immutable
contracts with P01 and changes no P01 field, identity, serialization, or result state.

Every future P02 source is supplied as one explicit `AnalyticalSourceBinding`. It carries an exact
typed public analytical payload, canonical instrument binding, timeframe, observation time,
availability time, as-of time, immutable revision identity, closed state, and P01 provenance
reference. Observation records when a fact occurred; availability records the earliest instant the
complete revision was legally consumable; as-of records the cutoff under which P03 resolved it.

P02 never queries "latest" state. P03 or an upstream deterministic assembler selects one revision
as of evaluation time and supplies it explicitly. P02 validates:

```text
observation <= availability <= as-of <= evaluation
```

A producer unable to prove availability creates structurally invalid input. Observation and
availability may be equal only when the producer contract explicitly guarantees immediate final
availability.

Canonical instrument identity is not inferred from symbol equality. An immutable
`InstrumentBinding` relates `EvaluationContext.instrument_id` to one canonical symbol and exact
provider aliases. Every source and MTF frame must carry the same binding identity.

The payload is a closed union of official Swing, Market Structure, Liquidity, Fibonacci, Context,
Elliott, Decision, and authorized Core Kernel contracts. Arbitrary mappings, private objects, and
duck typing are forbidden.

`MultiTimeframeAnalyticalBundle` composes P01 `MultiTimeframeInputSet` with one typed analytical
source set per declared frame. It requires exactly the same unique frames, one primary frame,
canonical ordering, closed frames, one instrument, resolvable provenance, and eligible source
availability. It derives no direction; P05 owns MTF aggregation.

`StrategySemanticMappingProfile` is the immutable executable rule schema for future profiles. Its
identity composes exact P01 `StrategyProfileIdentity` and fingerprints every typed rule. It contains
direction, entry, stop, target, confidence, evidence, freshness, temporal eligibility, conflict,
and MTF declarations. There is no implicit lookup, latest version, fallback, or default rule.

The schema may express exact enum maps or exact versioned strategy-rule references. Concrete
Elliott/Fibonacci source choices, ranking, confidence parameters, and evidence keys remain P04.
Concrete MTF direction remains P05. P02 may execute only supplied immutable rules.

P01 `FactAdapterState` remains sufficient:

- a complete valid bundle is `ACCEPTED`;
- profile-governed legitimate non-acceptance is `REJECTED`;
- malformed type, identity, instrument, time, revision, profile, or provenance is `INVALID_INPUT`;
- an unexpected adapter implementation fault is `FAILED`.

P02 owns structural validation, canonical ordering, execution of supplied rules, and P01 result
creation. P03 owns orchestration and resolved revision/profile provision. P04 owns the concrete
Elliott/Fibonacci profile. P05 owns concrete MTF direction. A07 remains final strategy authority.

## Consequences

The future adapter can be deterministic, instrument-safe, provenance-safe, and lookahead-safe
without reopening P01. Identical context, source bindings, profile, provenance, and adapter version
must produce identical results.

P02-F00 is governance only. Its contracts require a separate implementation authorization before
P02 implementation can be authorized.
