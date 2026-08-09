# Memory Ownership

Ownership determines who must retain and release references or resources.

| Owner | Responsibility |
| --- | --- |
| Caller | Inputs and returned values remain under caller control |
| Component | The component owns its internal state for its declared lifecycle |
| Framework | EPIP infrastructure owns the state |
| Shared | Multiple framework participants may observe the state |
| External system | A broker, network service, filesystem, or provider owns it |

Ownership is independent of thread visibility. Immutable values may be shared
without transferring ownership, while mutable shared state remains governed by
its H004 concurrency contract.

Releasing an EPIP object means removing references according to its declared
policy. Memory contracts do not override provider, adapter, or broker cleanup
requirements.
