# External Failure Model

This document now forms part of the wider Hardening-006 reliability model. External-effect rules
remain unchanged; `epip.core.reliability` makes their ownership and recovery expectations
machine-readable.

| Failure | Local state rule | Rollback | Compensation | Retry |
| --- | --- | --- | --- | --- |
| Provider unavailable | Do not commit dependent state | Local preparation only | No | Adapter policy |
| Timeout or network error | Treat remote outcome as unknown | No remote rollback | Protocol-specific | Only when safe |
| Broker error | Do not commit unconfirmed execution | No broker rollback | Broker-specific cancel | May duplicate |
| Filesystem error | Reject incomplete input/output | No general rollback | Caller strategy | Caller policy |
| Callback error | Preserve committed state and bus invariants | No | Callback owner | Caller policy |
| External EventBus error | Preserve local commit | No | Subscriber owner | Caller policy |
| Logging error | Exclude logging from commit decisions | No | No | Handler policy |
| System clock error | Propagate before object completion | N/A | No | Inject another clock |
| System identity error | Propagate before object completion | N/A | No | Inject another generator |

Failure propagation never proves that a remote write did not occur. Adapters preserve this
uncertainty instead of reporting a distributed rollback.

## Framework failure rules

- Programming errors fail fast and are never retried.
- Invalid data and configuration are corrected by the caller or user.
- Permanent failures prohibit retry until their cause is corrected.
- Interruptions abort the active operation and remain observable.
- Cancellation remains an explicit caller-controlled outcome.
- External retries are allowed only when the operation is explicitly safe and idempotent.
- Resource exhaustion is not converted into partial success.

The contracts describe these rules; they do not execute retries, compensation, or recovery.
