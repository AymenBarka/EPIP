# ADR-H004 — Replay Atomicity

## Status

Accepted.

## Decision

A Replay run owns one in-memory transaction spanning ReplaySession,
ReplayScheduler and its iterators, ReplayClock, ReplayStatistics, and the
FeatureStore cache and history used by Replay.

The transaction holds the existing locks in a fixed order, captures immutable
checkpoints, and restores every checkpoint on any pre-commit `BaseException`.
Replay-owned events are buffered and published only after session commit.

## Exclusions

Provider, Kernel, plugin and EventBus rollback are not part of this boundary.
No distributed transaction or external compensation is introduced.
