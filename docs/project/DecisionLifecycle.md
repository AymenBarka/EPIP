# Decision Lifecycle

Final decisions follow an explicit immutable registry lifecycle:

```text
CREATED
  -> SELECTED
  -> VALIDATED
  -> REGISTERED
  -> AVAILABLE
  -> SNAPSHOTTED
  -> ARCHIVED
  -> DISCARDED
```

Registration advances through the first five states only after structural
validation. Snapshot, archive, and discard transitions are explicit operations.
Every other transition is illegal and rejected.

Lifecycle changes produce a new registry. Existing Decisions, traces,
collections, snapshots, audits, and statistics remain unchanged and hashable.

The lifecycle describes availability of the Decision record. It does not place
orders, mutate positions, or claim that execution occurred.
