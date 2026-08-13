# Candidate Generation

Candidate generation converts explicit inference outcomes into a complete,
deterministic set of candidates.

## Generation flow

1. Receive explicit scenarios, evidence identifiers, and graph-node references.
2. Resolve and validate every reference.
3. Build immutable candidates in canonical order.
4. Advance each candidate through the required pre-registration lifecycle.
5. Register candidates atomically in deterministic indexes.
6. Produce a generation report, audit information, and diagnostics.

## Deterministic behavior

Identical inputs produce identical candidate identifiers, ordering, digests,
snapshots, and serialized output. Caller collection order does not alter the
canonical result. Duplicate identities or relationships are rejected rather
than silently overwritten.

## Registry queries

The registry supports deterministic lookup by candidate identifier, candidate
type, scenario, evidence identifier, graph-node identifier, and digest. Query
results are immutable and ordered canonically.

## Failure behavior

Missing references, invalid lifecycle transitions, malformed serialized data,
duplicate relationships, and digest mismatches fail explicitly. Failed
generation does not expose a partially registered candidate set.

## Non-goals

Generation does not rank candidates, choose a preferred outcome, make a trading
recommendation, or invoke execution and portfolio services.
