# Future

A07 Strategy and Portfolio are implemented. A07 E00-E09 are COMPLETE / CLOSED / FROZEN in
`v1.6.0`. Future work integrates the existing domains through the canonical architecture defined by
[ADR-0016](../adr/ADR-0016-CanonicalStrategyPipeline.md); it does not create a parallel strategy.

## Dependency-ordered program

```mermaid
flowchart LR
    P01[P01 Runtime and adapter contracts] --> P02[P02 Fact adapters]
    P02 --> P03[P03 Strategy Runtime]
    P03 --> P04[P04 Strategy profile]
    P04 --> P05[P05 MTF context]
    P05 --> P06[P06 E2E signal]
    P06 --> P07[P07 Backtest]
    P07 --> P08[P08 Ledger and metrics]
    P08 --> P09[P09 Walk-forward]
    P09 --> P10[P10 Quant validation]
    P10 --> P11[P11 Paper]
    P11 --> P12[P12 MT5 demo]
    P12 --> P13[P13 Observability]
    P13 --> P14[P14 Dashboard]
    P14 --> P15[P15 Live readiness]
```

P01 defines contracts for explicit evaluation context, provenance, Fact Adapters/Profiles,
Strategy Runtime results and diagnostics, signal envelopes, Capital Risk succession, and immutable
portfolio constraints. It is not implemented and requires separate contract authorization.

Later phases implement analysis-to-A07 mapping, the shared runtime, an Elliott/Fibonacci profile,
MTF facts, E2E signals, shared-runtime backtesting, ledger/metrics, walk-forward and quantitative
validation, paper and MT5 demo modes, observability, dashboards, and live-readiness evidence.
Each phase requires separate authorization.

## Deployment invariant

Backtest, paper, MT5 demo, and live must use the same analytical engines, Fact Adapters/Profile,
Strategy Runtime, A07, Capital Risk contract, and execution-plan semantics. Only data, clock,
broker, persistence, safety, and telemetry adapters vary. MT5-specific types remain at the external
boundary.

## AI boundary

AI remains downstream and future. It may consume governed immutable snapshots, histories, graphs,
signals, execution results, metrics, and portfolio state for explanation and research. It must not
bypass A07 strategy authority, Capital Risk, Execution, or Portfolio constraints.
