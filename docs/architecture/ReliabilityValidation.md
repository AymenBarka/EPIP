# Reliability Validation

Reliability validation closes H006 by exercising the contracts already owned by
the framework. It adds no execution policy and does not replace component tests.

The validation chain is:

1. deterministic fault selection from a logical tick;
2. typed exception classification;
3. retry, isolation, and fallback contract evaluation;
4. immutable audit snapshot and report generation;
5. canonical JSON comparison and retention checks.

The campaign covers providers, adapters, plugins, callbacks, external resources,
EventBus, Replay, Kernel, recovery, retry, circuit breakers, and fallbacks. Tests
never read system time, sleep, perform network I/O, or mutate production state.
