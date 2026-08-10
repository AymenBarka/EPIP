# Memory Lifecycle

Memory contracts identify the scope that bounds retained state.

| Lifecycle | Boundary |
| --- | --- |
| Call | State is not retained beyond one operation |
| Instance | State remains while the component instance is reachable |
| Run | State belongs to one engine or replay run |
| Application | State is intended to live for the application process |
| Persistent | State is retained as an explicit historical record |
| External | An external dependency controls lifetime |

## Release policies

Garbage-collected components become eligible after their owning instance or
run is released. Explicit and context-managed policies require their declared
operation. Process-lifetime state is released at shutdown. External resources
follow the external owner contract.

Programme A documents these policies only. It introduces no cleanup calls,
finalizers, context managers, or retention limits.
