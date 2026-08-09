# Retry Strategies

| Strategy | Meaning |
| --- | --- |
| `NO_RETRY` | The operation must not be attempted again. |
| `IMMEDIATE` | A future adopter may retry without a declared delay. |
| `FIXED_DELAY` | Every future delay uses one declared interval. |
| `LINEAR_BACKOFF` | Future delays may grow linearly. |
| `EXPONENTIAL_BACKOFF` | Future delays may grow exponentially. |
| `EXPONENTIAL_WITH_CAP` | Exponential growth is bounded by a cap. |
| `CUSTOM` | A future adapter supplies a separately governed policy. |

These meanings are descriptive. Programme C includes no scheduler, loop,
callback, clock access, or random-number generation.
