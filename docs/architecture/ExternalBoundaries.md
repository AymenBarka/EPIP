# External Boundaries

## Inventory

EPIP recognizes external EventBus subscribers, feature and market-data providers, MT5, TwelveData,
paper and broker adapters, filesystem, network, logging, system clock, system identity generation,
and user callbacks.

## Ownership Rule

EPIP owns validation, local ordering, immutable results, and local transaction commit. The external
system owns availability, latency, remote state, durability, settlement, transport, callback state,
wall-clock accuracy, and entropy.

## Commit Rule

An external read needed to prepare state must complete before local commit. An external
notification or callback occurs after local commit and cannot roll it back. A timeout means the
outcome is unknown unless the external protocol proves otherwise.
