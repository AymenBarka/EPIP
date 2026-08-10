# Scalability

EventBus was exercised with 1, 2, 8, 32, 64, 128, and 256 concurrent publishers. Every publisher
completed, all identifiers were unique, and per-publisher FIFO was preserved. Because callbacks are
synchronous, throughput is expected to plateau under contention; this is an explicit contract, not a
parallel-dispatch promise.

The always-on longevity test processes 100,000 events. The 640,000-event concurrent campaign is the
standard heavy test. Runs of 5 and 10 million events were excluded from CI because their cost is not
proportionate to the additional evidence they provide.
