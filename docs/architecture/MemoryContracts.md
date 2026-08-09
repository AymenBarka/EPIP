# Memory Contracts

EPIP memory contracts provide the official vocabulary for memory ownership and
resource management. They are architecture metadata, not runtime controls.

## Contract API

The additive API in `epip.core.memory` exposes:

- `MemoryContract`, the immutable declaration;
- `MemoryAware`, the optional structural protocol;
- `MemoryRegistry`, the immutable lookup service;
- `MEMORY_CONTRACTS`, the official registry;
- `get_memory_contract()`, resolution by name, type, or instance;
- `declared_memory_contracts()`, deterministic registry enumeration.

## Classification

Each contract declares one or more official classifications:

| Classification | Meaning |
| --- | --- |
| Memory Stateless | No component-owned state survives a call |
| Memory Owned | The component owns retained in-process state |
| Memory Shared | State may be visible to multiple callers or threads |
| Memory Cached | Retention is governed by cache semantics |
| Memory Ephemeral | State is temporary and non-persistent |
| Memory Persistent | State intentionally grows with retained history |
| Resource Managed | The component participates in resource lifecycle management |
| Resource External | An external system defines the resource lifecycle |

## Compatibility

Contracts do not modify allocation, release, serialization, algorithms, or
public constructor signatures. Existing components are resolved without being
required to inherit a framework base class.
