# Evidence Lifecycle

Evidence follows one forward-only lifecycle:

```text
CREATED -> VALIDATED -> REGISTERED -> AVAILABLE -> SNAPSHOTTED -> ARCHIVED -> DISCARDED
```

Each transition is explicit and advances exactly one state. Skipping a state,
moving backwards, or transitioning from `DISCARDED` is rejected.

Registration creates an internal `CREATED` entry, performs structural
validation, then advances through `VALIDATED` to `REGISTERED`. Availability is
an explicit caller decision. Snapshot creation advances every currently
available entry to `SNAPSHOTTED` before capturing the immutable registry view.

Archived and discarded evidence remains addressable for traceability unless a
higher-level retention policy removes the complete registry instance. The
Evidence Engine itself performs no implicit deletion and no automatic repair.
