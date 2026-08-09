# ADR-H004: Kernel Atomicity and Plugin Isolation

## Status

Accepted.

## Context

The Kernel previously exposed its live registry and EventBus to plugins and retained successful
results when a later plugin failed. This allowed partial pipeline progress to become observable.

## Decision

One Kernel run is an in-memory transaction. The Kernel snapshots the ordered plugin set, creates a
fresh `PluginContext`, registry snapshot, and EventBus for each plugin, and retains results and
events privately. A failed or invalid result stops the pipeline and discards all earlier temporary
artifacts. Any `BaseException` rolls back and propagates. Only a completely validated pipeline is
committed; its events are then published in deterministic order.

Only one run may be active on a Kernel instance. Concurrent and recursive entry fails immediately
with `KernelPipelineBusyError`, preventing plugin/thread self-deadlock.

## Consequences

Plugin registry mutations and publications remain isolated until commit. The transaction does not
roll back external provider, broker, network, disk, database, or post-commit listener effects.
These are explicitly outside Programme E.
