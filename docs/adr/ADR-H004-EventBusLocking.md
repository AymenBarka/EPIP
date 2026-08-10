# ADR-H004: EventBus Locking Model

## Status

Accepted for Hardening-004 Programme B.

## Context

Synchronous callbacks were previously invoked immediately by `publish()`. Although EventBus
released its own lock first, engines frequently still held their state lock. A listener could then
re-enter a source engine or acquire another engine lock, creating lock inversion and ABBA deadlock
paths. Recursive publication also delivered nested events before the remaining listeners of the
current event.

## Decision

EventBus accepts publications into an in-memory FIFO dispatch queue. Acceptance atomically records
the event and an immutable listener snapshot. One dispatcher drains the queue without holding the
EventBus lock. Concurrent publishers wait for their publication to complete; recursive publication
by the dispatcher thread is queued and returns after acceptance.

Engine state mutation completes under the engine lock. Event construction and publication occur
after that lock is released. Observer notification follows the same rule.

One dispatch cycle is limited to `MAX_REENTRANT_EVENTS` recursive publications. Exceeding the limit
raises `EventReentrancyError` and terminates the recursive chain, preventing an unbounded
publication loop. Ordinary concurrent publications do not consume this reentrancy budget.

## Consequences

- Event acceptance and listener order are FIFO.
- Listeners run in registration order.
- Recursive events run after every listener of the current event.
- Subscription changes do not alter an accepted publication.
- A listener exception keeps its historical propagation behavior for the originating publisher.
- Already queued events are drained even when another listener fails.
- Delivery remains synchronous for ordinary and concurrent publishers.

## Compatibility

Public method signatures and event schemas remain unchanged. Financial calculations, snapshots,
serialization, identity, and data-integrity invariants are unaffected.

## Programme B.1 validation

The locking model passed an experimental campaign covering 640,000 publications from 64 threads,
200 simultaneous publishers behind a 200 ms listener, deep recursion, ABA subscription mutation,
mixed listener speeds, and listener exceptions. No loss, duplicate delivery, deadlock, queue
corruption, or starvation was observed.

The campaign identified one defect in the initial Programme B implementation: its dispatch-cycle
counter included concurrent publications. The counter now applies exclusively to publications
created reentrantly by the dispatcher thread. This prevents legitimate contention from exhausting
the recursion safeguard.

On the validation host, the 640,000-event scenario sustained 20,909.30 events per second. Detailed
results and limitations are recorded in `EventBusStressTests.md` and `EventBusPerformance.md`.

## Programme B.2 failure recovery

Listener boundaries isolate every `BaseException`, including `KeyboardInterrupt`, `SystemExit`,
and `GeneratorExit`. Delivery continues for already accepted publications, dispatcher state is
restored, and the originating synchronous publisher receives its listener failure.

A publication from another thread while a listener callback is active is accepted into the same
FIFO queue and returns after acceptance rather than waiting for delivery. This rule prevents a
listener that joins that publisher thread from indirectly waiting for its own dispatcher. Delivery
still occurs after the current listener snapshot completes. Because this narrow path is deferred,
listener failures from that publication cannot be propagated to the already returned publisher.
