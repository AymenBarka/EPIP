# Inference Lifecycle

Hypotheses and scenarios follow one explicit lifecycle:

```text
CREATED -> SUPPORTED -> VALIDATED -> REGISTERED -> AVAILABLE
AVAILABLE -> SNAPSHOTTED -> ARCHIVED
CREATED|SUPPORTED|VALIDATED|REGISTERED|AVAILABLE -> DISCARDED
```

Builders create domain values but do not mutate registries. Successful
registration performs the structural support and validation stages and stores
the value as `REGISTERED`. Callers explicitly move registered values to
`AVAILABLE`. Snapshot creation moves available values to `SNAPSHOTTED` and
returns a new engine plus an immutable snapshot.

Invalid transitions raise `RelationshipIntegrityError`. Rejected registrations
can be captured through the non-throwing `try_register_*` methods; diagnostics
report those failures but never repair state automatically.

Archived and discarded values remain traceable in the immutable registry.
Lifecycle state is technical metadata and is intentionally separate from the
hypothesis or scenario content digest.
