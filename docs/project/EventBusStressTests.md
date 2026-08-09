# EventBus Stress Tests

## Purpose

Hardening-004 Programme B.1 validates the EventBus locking model experimentally without changing
financial algorithms, domain models, serialization, or public method signatures.

## Test environment

The recorded campaign ran on Windows with Python 3.13.14. Timing results characterize this test
host and are not service-level objectives. Correctness assertions are platform-independent.

## Results

| Scenario | Load | Result |
| --- | ---: | --- |
| Concurrent publication | 64 threads × 10,000 events | 640,000 accepted and delivered |
| Slow listener | 200 simultaneous publishers, 200 ms blocker | Completed without deadlock |
| Recursive publication | 10,000 permitted reentrant events | Limit enforced and bus recovered |
| ABA subscription mutation | subscribe/unsubscribe/subscribe/clear | Current snapshot remained stable |
| Mixed contention | 16 publishers, three listener behaviours | History and listener order preserved |

The 640,000-event test compares the complete listener trace with EventBus history, verifies global
FIFO acceptance order, verifies uniqueness, and verifies each publisher's local sequence. No event
was lost or delivered twice.

## Fairness observations

Every one of the 64 publishers completed all 10,000 publications. The fastest publisher completed
in 14.8905 seconds and the slowest in 30.5160 seconds. No starvation or infinite wait was observed.

EventBus guarantees FIFO after acceptance, not strict operating-system thread fairness. Lock
acquisition before acceptance remains governed by the Python runtime and host scheduler. The
single-dispatcher design prevents delivery overtaking but does not promise equal completion time.

## Reentrancy and memory

The recursive chain raised `EventReentrancyError` at `MAX_REENTRANT_EVENTS`, left the queue empty,
and accepted a subsequent normal event. After clearing history and garbage collection, traced
memory was 6,376 bytes against a 2,514,318-byte peak. This demonstrates reclamation in the tested
cycle; it is not a general heap-size guarantee.

## Reproduction

```powershell
python -m pytest tests/core/test_eventbus_stress.py -q -s --durations=10
```
