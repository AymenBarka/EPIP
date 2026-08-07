# Frequently Asked Questions

## Why immutable objects?

They prevent consumers from rewriting published facts, make concurrency safer, and improve replay,
comparison, hashing, testing, and auditability.

## Why EventBus?

It lets engines publish domain facts without knowing every observer. This keeps monitoring,
reporting, and later integrations outside the producer's business logic.

## Why snapshots?

A snapshot is a versioned point-in-time contract. It carries the official result and enough stream
metadata to trace how later outcomes were produced.

## Why graphs?

Markets and decisions are not only flat sequences. Graphs preserve parent/child hypotheses,
previous/next evolution, and links to upstream objects for explanation and traversal.

## Why histories?

Immutable histories provide chronological lookup and deterministic replay without exposing an
engine's mutable internal registries.

## Why DDD?

DDD assigns vocabulary and invariants to the module that owns them. It stops order execution from
deciding trades and stops analysis modules from sizing positions.

## Why prohibit duplicated calculations?

Two implementations of the same decision, sizing, or exposure rule eventually disagree. EPIP uses
one official producer and immutable downstream contracts to keep results consistent.

## Why adapters?

Market-data vendors and brokers change independently from the domain. Protocol-backed adapters
isolate credentials, transport, retries, vendor models, and optional dependencies.

## Is EPIP a trading strategy?

No. It is framework infrastructure. A strategy must define its own validated policies and accept
responsibility for market, operational, and financial risk.

## Can engines be used independently?

Many can, provided their official input contract is supplied. Dependency rules still apply; an
independent consumer must not recreate an upstream module's owned calculation.
