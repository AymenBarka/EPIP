# Memory Profile

EventBus history intentionally retains published events until `clear()` is called. Memory validation
therefore distinguishes configured retention from leaks. Repeated batches followed by `clear()` and
garbage collection remain below the one-megabyte residual-allocation threshold used by the test.

Snapshots, immutable graphs, and histories retain data by domain design. Production deployments must
apply lifecycle and retention policies appropriate to their workload.
