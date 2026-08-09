# External Effect Contracts

The machine-readable registry is `epip.core.external_effects.EXTERNAL_EFFECT_CONTRACTS`.

| Boundary | Thread safety | Idempotence | Deterministic | Delivery |
| --- | --- | --- | --- | --- |
| External EventBus | Thread Safe | Non-idempotent | No | Best effort |
| Feature provider | Thread Safe by base contract | Conditional | Yes when pure | N/A |
| Market-data provider | Thread Confined | Conditional | No | N/A |
| MT5 | Thread Confined | Non-idempotent | No | Caller retry is at least once |
| TwelveData | Thread Confined | Conditional reads | No | N/A |
| Paper adapter | Thread Safe | Non-idempotent | Sequentially deterministic | N/A |
| Broker adapter | Thread Confined | Non-idempotent | No | Caller retry is at least once |
| Filesystem | Thread Compatible | Conditional | No | N/A |
| Network | Thread Confined | Conditional | No | Best effort |
| Logging | Thread Compatible | Non-idempotent | No | Best effort |
| System clock | Thread Safe | Non-idempotent | No | N/A |
| System identity | Thread Safe | Non-idempotent | No | N/A |
| User callback | Non Thread Safe by default | Non-idempotent | No | Best effort |

No listed boundary is an EPIP distributed transaction or automatically compensable.
