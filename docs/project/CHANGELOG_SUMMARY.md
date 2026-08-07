# Changelog Summary

This summary groups the tagged framework milestones. Detailed capability lists remain in the root
`CHANGELOG.md` and module architecture documents.

| Release | Modules and architecture | Quality | Benchmark summary |
|---|---|---|---|
| v1.0.0-pre | Core through Market Context; immutable snapshots, events, graphs, histories, and deterministic serialization established as framework conventions | Black, Ruff, MyPy, Pytest PASS; module coverage 95–96% | Per-engine benchmark suite established for feature, data, replay, swing, structure, liquidity, Fibonacci, and Context operations |
| v1.1.0 | Elliott Wave Engine; rules, alternate counts, degrees, projections, scoring, Context integration | All gates PASS; coverage 96% | Elliott benchmark added; consolidated hardware-neutral baseline is not recorded in release metadata |
| v1.2.0 | Decision Engine; sole trading-intent authority with rules, scores, probability, priority, rationale, graph/history | All gates PASS; coverage 96% | Decision benchmark added; performance remains environment-dependent |
| v1.3.0 | Risk Engine; sole sizing authority and official `PositionPlan`; limits, stops, targets, exposure, drawdown, leverage, margin | All gates PASS; 186 tests; coverage 96% | Reference run: about 703k–708k sizing calculations/s and 1.41–1.42 µs latency |
| v1.4.0 | Execution Engine; sole broker boundary and official `ExecutionSnapshot`; lifecycle, adapters, fills, retry, slippage, commission | All gates PASS; 205 tests; coverage 97% | Reference run: about 402k–424k order constructions/s and 2.36–2.49 µs latency |

## Major design progression

The early releases established deterministic domain analysis. v1.1 added explicit probabilistic wave
interpretation; v1.2 separated trading intent; v1.3 separated position sizing and constraints; v1.4
separated broker execution. The result is a pipeline in which every major calculation has one owner
and every downstream integration consumes an immutable official object.
