# P01 Canonical Strategy Runtime Contract Specification

Status: IMPLEMENTED CONTRACT

Authority: [ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md) and
[ADR-0017](../adr/ADR-0017-CanonicalStrategyRuntimeContracts.md).

## Contract inventory

- Evaluation: `RuntimeMode`, `EvaluationContext`.
- Provenance: `SourceProvenance`, `FactProvenance`, `ProvenanceManifest`.
- Profile: `StrategyProfileIdentity`, `StrategyProfile`, exact registry protocol.
- MTF: `TimeframeRole`, `TimeframeInput`, `MultiTimeframeInputSet`.
- Facts: `AnalyticalInputBundle`, `StrategyFactBundle`.
- Adapter boundary: identity, protocol, result, and state; no concrete adapter.
- Runtime boundary: closed options, request, states, diagnostics, and result; no orchestrator.
- Signal boundary: `StrategySignalEnvelope` around frozen A07 `StrategySignal`.
- Capital Risk: request, assessment, reasons, states, and `SizedPositionPlan`.
- Portfolio constraint input: `PortfolioRiskView`.

All P01 contracts are immutable. Canonical JSON uses explicit type/enum/tuple tags, sorted keys,
finite floats, UTC timestamps, and strict reconstruction. SHA-256 identities exclude only their own
derived identity fields. Malformed or inconsistent payloads fail closed.

## Ownership

A07 remains the only final strategy authority. Fact bundles contain inputs to A07, not A07
outputs. Signal envelopes do not copy strategy semantics. Capital Risk adds sizing/capital facts
and may reject but cannot repair. Portfolio risk views contain no strategy semantics.

## Classification

- A07 E00-E09: FROZEN.
- P01 models and protocols: IMPLEMENTED CONTRACT.
- Decision/Risk `PositionPlan` pipeline: COMPATIBILITY API.
- Concrete Fact Adapters: FUTURE IMPLEMENTATION / P02.
- Strategy Runtime behavior: FUTURE IMPLEMENTATION / P03.
- Strategy Profile behavior: FUTURE IMPLEMENTATION / P04.
- MTF analytical behavior: FUTURE IMPLEMENTATION / P05.
