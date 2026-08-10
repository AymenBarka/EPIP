# Runtime Security Policies

| Policy | Violation decision | Default state |
| --- | --- | --- |
| `NO_SECURITY` | `IGNORE` | Disabled |
| `MONITOR_ONLY` | `REPORT_ONLY` | Disabled |
| `VALIDATE_ONLY` | `DENY` | Disabled |
| `VALIDATE_AND_REPORT` | `DENY` | Disabled |
| `STRICT` | `DENY` | Disabled |
| `CUSTOM` | `DELEGATE` | Disabled |
| `DISABLED` | `IGNORE` | Disabled |

An enabled validating policy allows an evaluation with no supplied violation.
No policy performs discovery, normalization, or validation by itself.
