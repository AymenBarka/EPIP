# Confidence Propagation

Propagation follows the explicit EPIP-016 provenance chain:

```text
Evidence -> Hypothesis -> Scenario -> Candidate -> Confidence Assessment
```

The builder resolves every reference through the frozen Programme B–E
registries. Missing or invalid references fail structural validation.

For confidence, quality, validity, and uncertainty, propagation is the
arithmetic mean of the candidate and every resolved Evidence, Hypothesis, and
Scenario value. Every source has equal weight. This declared rule is stable,
reproducible, and contains no hidden heuristic.

Qualitative confidence and quality levels use five equal-width bands. Validity
is invalid at zero, unknown below one half, conditional below one, and valid at
one. These labels describe propagated values; they do not rank candidates.

Evidence coverage, scenario consistency, completeness, and traceability are
calculated separately. No combined or final score is produced. Reordering input
candidate identifiers or graph references cannot alter canonical output.
