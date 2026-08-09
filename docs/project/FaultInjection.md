# Fault Injection

H006 fault injection is test-only, deterministic, reproducible, and configurable.
An injection target and positive period define exactly which logical ticks fail.

| Boundary | Injected condition | Official exception family |
| --- | --- | --- |
| Provider | unavailable, slow, intermittent | Provider or timeout |
| Adapter | unavailable | Adapter |
| Plugin and callback | execution failure | Plugin or framework |
| Network and filesystem | external or infrastructure failure | Infrastructure |
| EventBus, Replay, Kernel | component failure | Component taxonomy |
| Recovery, retry, circuit, fallback | policy-path failure | Reliability taxonomy |

No wall-clock, random source, real network, filesystem mutation, or process signal
is used. Repeating a campaign with the same target, period, and logical ticks must
produce the same ordered outcomes.
