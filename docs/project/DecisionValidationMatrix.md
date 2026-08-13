# Decision Validation Matrix

| Area | Validation evidence |
| --- | --- |
| Architecture | Required A–G modules are present |
| Determinism | Complete canonical pipelines are byte identical |
| Explainability | Decision explanation and trace are non-empty |
| Replay | Canonical snapshots reproduce identical payloads |
| Immutability | Frozen business models and integrity inventory |
| Registries | Required registries are present and complete |
| Serialization | Canonical JSON is byte stable |
| Digests | SHA-256 values are stable across replay |
| Reproducibility | Identical inputs reproduce identical Decisions |
| Compatibility | Existing public surfaces remain present |
| Integration | A–G registry and reference chain is complete |

Fault injection covers missing references, graph failures, duplicates, illegal
lifecycle transitions, missing Confidence or constraints, malformed payloads,
invalid snapshots, and registry inconsistencies through the dedicated A–G and
Programme H test suites.

A failed matrix item prevents certification. No validation step automatically
repairs an artifact.
