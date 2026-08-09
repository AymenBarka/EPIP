# Kernel Atomicity

## Guarantee

A Kernel invocation has exactly two observable outcomes:

- the complete validated result is returned and all staged events are published after commit; or
- the pipeline exposes no result, evidence, scenario, hypothesis, decision, registry mutation, or
  pre-commit event from completed plugins.

`Exception` is normalized into a failed `PluginResult`. Invalid or unsuccessful results use the
same rollback path. A `BaseException` is propagated after rollback. No later plugin executes.

## Boundary

The transaction owns temporary plugin results, evidence, Kernel domain objects, isolated plugin
events, and structural registry snapshots. The Kernel has no persistent cache or history in the
current architecture, so there is no additional mutable Kernel state to checkpoint.

Event publication is deliberately post-commit. Failures caused by external listeners after commit
are not reversible by this local transaction.
