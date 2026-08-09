# Performance Baseline

The authoritative EventBus baseline is recorded in `EventBusPerformance.md`: 20,909 events/s under
the 64-thread, 640,000-event campaign, mean publish latency of 0.2728 ms with eight listeners, and
low tuple-snapshot overhead. Existing Replay, Kernel, Portfolio, and Execution benchmark suites
remain the component baselines. No defensible pre-Hardening-004 measurements were retained, so no
before/after percentage is asserted.
