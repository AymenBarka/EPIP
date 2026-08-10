# Security Classification

| Classification | Meaning |
| --- | --- |
| Public | Supported externally visible surface |
| Internal | Framework implementation surface |
| Trusted | Explicitly trusted integration surface |
| Untrusted | Input or behavior requiring external validation |
| External | Boundary implemented outside the framework |
| System | Operating-system or host-provided service |
| Plugin | Extension-controlled surface |
| Framework | Framework-owned orchestration surface |

Classification is distinct from sensitivity and trust. `SecurityLevel` records
sensitivity, while `TrustLevel` records whether a boundary is trusted,
conditional, or untrusted. This separation prevents classification labels from
being interpreted as access-control decisions.
