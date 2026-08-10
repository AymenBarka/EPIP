# Concurrency Model

## Current Model

EPIP is an in-process synchronous framework. Locks protect selected mutable structures, immutable
snapshots carry results between domains, and EventBus invokes listeners synchronously. Contracts
describe these current guarantees without changing execution.

The supported baseline is:

1. isolate Thread Confined providers and replay state;
2. serialize each Thread Compatible engine instance;
3. share Thread Safe registries, caches, clocks, statistics, histories, and graphs only within their
   stated restrictions;
4. treat plugin, broker, and provider contracts independently;
5. never infer async, multi-process, cluster, transactional, or exactly-once guarantees.

## Determinism

Sequential determinism and concurrent determinism are distinct. A deterministic clock or identity
generator protects its state, but concurrent assignment order still follows lock acquisition order.
Contracts therefore declare `deterministic_under_concurrency` explicitly.

## Reentrance

Reentrance is declared independently from thread safety. A reentrant lock can permit nested calls
without making their business ordering safe. Components classified as Thread Compatible must be
treated as non-reentrant unless their contract explicitly states otherwise.

EventBus permits bounded recursive publication. Nested events are queued and delivered after all
listeners of the current event. The dispatcher rejects a cycle exceeding 10,000 publications.

## Publication Lock Boundary

Stateful engines commit snapshots under their local lock and publish only after releasing it.
EventBus captures an immutable listener snapshot under its own lock, releases that lock, and then
dispatches. No user callback may execute while either lock is retained.

## Engine Atomicity

Stateful engines prepare immutable successor state without replacing observable
references. Snapshot, history, graph and cache references are replaced together
under the existing engine lock. Portfolio position accounting is calculated on
a private working copy. Event publication follows the completed commit.

## Replay Isolation

Replay sessions use a wider orchestrator boundary over Replay-owned mutable
components. Existing locks are acquired in a fixed order, state is checkpointed
before execution, and Replay-owned events are deferred until session commit.
Failures restore session, clock, scheduler, statistics and FeatureStore state.

## Kernel Orchestration

Kernel pipelines use a local transaction and per-plugin isolated contexts. Plugin results,
evidence, registry mutations and events remain private until the complete pipeline validates.
Failure discards temporary artifacts and stops subsequent plugins. A Kernel instance rejects
overlapping and recursive execution without waiting; committed events are published afterwards.

## External Boundaries

External providers, brokers, filesystems, networks, callbacks, logging handlers, system time, and
system identity sources are outside EPIP local transactions. Required reads complete before local
commit; notifications and callbacks execute after commit. Their failures cannot reverse remote or
already committed local effects, and exactly-once delivery is not claimed.

## Future Programmes

The completed model includes EventBus locking, engine atomicity, Replay isolation, Kernel
orchestration atomicity, and explicit non-transactional external-effect contracts.

## Production validation

The production validation campaign and its scalability, fairness, and memory limits are documented
in `ProductionStress.md`, `Scalability.md`, `Fairness.md`, and `MemoryProfile.md`.
