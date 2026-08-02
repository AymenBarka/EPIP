# ADR-0002: Event Bus and Kernel for EPIP Execution

## Status

Accepted

## Context / Problem

The EPIP execution pipeline needed a predictable way to coordinate plugins, publish domain events, and aggregate results without coupling the core domain to implementation details. A simple direct invocation approach would make the flow harder to observe, test, and extend.

## Decision

Introduce an in-process EventBus to support deterministic publish/subscribe behavior and a Kernel to orchestrate plugin execution through a registry. Plugins receive an immutable PluginContext and return an immutable PluginResult, which allows the kernel to collect evidence, build scenarios and decisions, and publish domain events consistently.

## Alternatives Considered

- Direct plugin invocation from the caller without an orchestration layer
- Ad-hoc callback chaining between plugins
- External message brokers, which would add operational complexity for this project scope

## Consequences

- Plugin execution becomes decoupled, observable, and easier to test.
- The kernel can apply deterministic ordering and collect execution results in a consistent way.
- The architecture is now extensible for future plugins and event-driven workflows, while keeping the domain layer independent from execution concerns.
