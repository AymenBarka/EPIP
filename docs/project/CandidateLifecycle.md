# Candidate Lifecycle

Every decision candidate follows one explicit, forward-only lifecycle.

## States

1. `CREATED`
2. `GENERATED`
3. `VALIDATED`
4. `REGISTERED`
5. `AVAILABLE`
6. `SNAPSHOTTED`
7. `ARCHIVED`
8. `DISCARDED`

## Transition policy

Transitions are legal only between adjacent states in the sequence above. A
transition cannot skip a state, move backward, or continue after `DISCARDED`.
Invalid transitions raise the candidate lifecycle error without changing the
candidate or registry state.

The lifecycle describes candidate availability, not trading intent. In
particular, `AVAILABLE` means that a candidate can be inspected by downstream
decision components; it does not mean selected, recommended, or executable.

## Immutability

Lifecycle changes produce a new immutable candidate value. Existing values,
snapshots, digests, audit entries, and registry query results remain unchanged.
