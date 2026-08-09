# Reliability Validation Matrix

| Capability | Fault validation | Stress validation | Determinism | Retention |
| --- | --- | --- | --- | --- |
| Reliability contracts | Typed failures | Registry resolution | Stable contracts | Immutable |
| Exception taxonomy | Fifteen boundaries | Repeated classification | Stable type/message | No storage |
| Retry contracts | Retry-path fault | 100,000 decisions | Stable decision | Context not retained |
| Circuit breakers | Isolation fault | 100,000 decisions | Stable snapshot | Bounded history |
| Graceful degradation | Availability fault | 100,000 decisions | Stable result | Bounded history |
| Fallback runtime | Fallback fault | 100,000 decisions | Stable result | Context not retained |
| Reliability audit | Component faults | 100,000 snapshots/reports | Canonical JSON | Caller-owned reports |
| Integrated path | Mixed deterministic faults | 1,000 cycles | Identical campaigns | Bounded runtimes |

The matrix validates compatibility with H001 determinism, H002 data integrity,
H003 financial correctness, H004 concurrency, H005 memory safety, and H006
reliability contracts.
