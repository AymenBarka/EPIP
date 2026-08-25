# ADR-0020: Evidence Mapping and Fail-Fast Semantic Execution

## Status

Accepted

## Context

ADR-0019 made evidence mapping a closed executable semantic-rule family, but the implemented
profile has no place to bind its `RuleIdentity`. Exact profile closure therefore rejects every
evidence-mapping implementation as an unused extra. The execution contract also defines terminal
rule states without deciding whether an adapter stops or continues independent work to aggregate
diagnostics. Both gaps would force `CanonicalFactAdapter` to invent observable policy.

## Decision

Each `EvidenceKeyPolicy` will contain one mandatory `mapping_rule: RuleIdentity`. Mapping executes
once per taxonomy key because the existing request names one exact key. Multiple keys may share an
explicit identity. The identity participates in taxonomy serialization and semantic-profile
fingerprinting, and exact rule-set closure traverses it as `EVIDENCE_MAPPING`.

P02 adopts dependency-aware fail-fast execution. All structural validation completes before rule
execution. The first terminal semantic non-success in canonical stage order stops subsequent work.
Only omission explicitly permitted for optional evidence is non-terminal. Diagnostics include only
work performed through the terminal outcome and are canonically sorted. Unexpected executable-rule
exceptions become sanitized P01 `FAILED` outcomes; raw exception text is not semantic data.

## Alternatives rejected

Native evidence mapping was rejected because choosing which candidates substantiate a taxonomy key
is strategy-specific. A taxonomy-wide mapping identity was rejected because the frozen request is
per key and would couple independent keys. Continue-and-aggregate execution was rejected because
downstream requests depend on successful upstream outputs and independent continuation would create
unnecessary semantic side effects and a larger execution graph.

## Consequences

P02-F05 must add the field, update profile closure and fingerprinting, preserve canonical
serialization, implement any required private failure-control helpers, add focused tests, and update
the compliance digest. P01, A07, and existing public execution vocabularies remain unchanged.
`CanonicalFactAdapter` is still unauthorized until P02-F05 closes.
