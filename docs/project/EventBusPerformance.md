# EventBus Performance

## Measurement scope

These measurements validate the synchronous in-process EventBus introduced by Hardening-004.
They are diagnostic baselines, not contractual latency or throughput guarantees.

## Recorded results

| Measurement | Result |
| --- | ---: |
| 64-thread throughput, one listener | 20,909.30 events/s |
| Mean publish latency, eight threads and eight listeners | 0.2728 ms |
| Maximum observed publish latency | 185.2061 ms |
| Sequential throughput, no listeners | 22,107.47 events/s |
| Sequential throughput, eight listeners | 21,981.86 events/s |
| Eight-listener snapshot overhead over 20,000 events | 5.1695 ms |

The measured listener snapshot overhead is approximately 0.00026 ms per event for eight listeners
on the test host. Under 64-thread contention, throughput is dominated by synchronous dispatch,
validation, scheduling, and publisher coordination rather than tuple snapshot construction.

## Interpretation

- Listener snapshots have low measured cost at the tested listener count.
- Maximum latency is scheduler-sensitive because concurrent publishers synchronously wait for FIFO
  delivery.
- A slow listener intentionally applies backpressure to every later publication.
- The model optimizes integrity and deterministic ordering rather than parallel callback execution.

No comparable pre-Hardening-004 benchmark was retained, so a defensible before/after percentage
cannot be reported. This campaign establishes the baseline for future performance hardening.

## Non-guarantees

EventBus does not guarantee fixed latency, strict publisher fairness, listener isolation, parallel
delivery, persistence, or cross-process transport. Applications requiring those capabilities need
a future asynchronous event infrastructure with an explicit compatibility boundary.
