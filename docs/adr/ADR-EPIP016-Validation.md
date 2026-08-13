# ADR-EPIP016 Validation and Certification

## Status

Accepted for Programme H.

## Decision

EPIP validates Programmes A through G through an additive, read-only
certification layer. Validation observes canonical serialized artifacts,
registries, replay results, explanations, traces, and digests. It introduces no
business capability and never repairs observed data.

Certification requires architecture completeness, determinism, explainability,
replay compatibility, immutability, registry integrity, serialization, digest
stability, decision reproducibility, backward compatibility, and cross-module
consistency.

Stress and benchmark timing are engineering observations. Timing values do not
participate in deterministic certification digests and establish no SLA.

## Consequences

- A–G remain frozen and independently authoritative.
- Identical validation inputs produce identical reports and certification.
- Faults and anomalies fail certification instead of being corrected.
- Large campaigns retain counts and digests, not generated object histories.
- Validation performs no market, financial, portfolio, risk, or execution work.
