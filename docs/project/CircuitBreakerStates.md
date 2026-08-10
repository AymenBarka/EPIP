# Circuit Breaker States

| State | Behaviour |
| --- | --- |
| `CLOSED` | Operations are permitted and outcomes are measured. |
| `OPEN` | Operations are denied until logical open duration elapses. |
| `HALF_OPEN` | A configured number of trial operations is permitted. |
| `FORCED_OPEN` | Operations are denied by an explicit operator decision. |
| `DISABLED` | Operations are permitted without automatic state changes. |

The normal path is `CLOSED` → `OPEN` → `HALF_OPEN` → `CLOSED`. A failed
half-open trial returns the circuit to `OPEN`. Forced and disabled states require
explicit transitions. Every transition records a non-empty reason.
