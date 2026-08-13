# Inference Engine

The EPIP-016 Inference Engine converts registered evidence into immutable
hypotheses and scenarios. It is an interpretation boundary: it does not rank
actions, select trades, calculate risk, or make decisions.

## Responsibilities

- build canonical hypotheses from explicit evidence references;
- build canonical scenarios from registered hypotheses and evidence;
- validate relationship integrity without evaluating market truth;
- maintain immutable registries and lifecycle state;
- expose deterministic snapshots, audits, diagnostics, and SHA-256 digests.

All inputs are explicit. The engine reads an `EvidenceRegistry` supplied by the
caller and never invokes providers, clocks, random sources, portfolio services,
or lower-level market engines.

## Architecture

`HypothesisBuilder` and `ScenarioBuilder` normalize unordered inputs and compute
content digests. `InferenceValidator` verifies references, duplicates,
self-reference, and digest integrity. `HypothesisRegistry` and
`ScenarioRegistry` return new values for every registration or transition.
`InferenceEngine` coordinates those values and produces `InferenceSnapshot`.

Snapshot JSON is canonical: keys are sorted and insignificant whitespace is
removed. A round trip therefore preserves identities and produces identical
bytes for identical content.

## Boundaries

The module contains no candidate actions, ranking policy, scoring policy,
portfolio logic, risk calculation, or execution instruction. Those concerns
remain downstream of inference.
