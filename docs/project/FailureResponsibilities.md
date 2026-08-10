# Failure Responsibilities

| Responsible party | Responsibility |
| --- | --- |
| Framework | Preserve documented invariants and surface implementation defects |
| Caller | Supply valid data and choose an allowed recovery action |
| Plugin | Contain and report failures produced by plugin code |
| Provider | Honour the provider contract and expose provider failures |
| Adapter | Preserve external uncertainty and adapter-specific guarantees |
| External System | Restore unavailable remote services or resources |
| Operating System | Govern process, filesystem, network, and memory resources |
| User | Correct invalid configuration or operational input |

Exactly one primary responsibility is declared per failure contract. This identifies ownership; it
does not prevent other parties from participating in diagnosis or recovery.
