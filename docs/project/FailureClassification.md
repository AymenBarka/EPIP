# Failure Classification

| Category | Meaning | Default treatment |
| --- | --- | --- |
| Programming Error | Framework invariant or implementation defect | Fail fast |
| Data Error | Invalid or inconsistent caller input | Propagate for correction |
| Configuration Error | Invalid component or application configuration | Fail fast |
| Transient Error | Temporary condition that may clear | Retry only when explicitly safe |
| Permanent Error | Condition that requires correction | Retry forbidden |
| External Failure | Failure owned outside the framework | Propagate with uncertainty |
| Resource Failure | Memory, file, network, or OS resource failure | Abort affected operation |
| Timeout | External completion was not observed in time | Propagate external uncertainty |
| Interruption | Process or thread interruption | Abort and propagate |
| Cancellation | Explicit cancellation request | Propagate as an expected outcome |

Severity is independent of category and is one of informational, warning, error, or critical.
Classification never turns a failed operation into success.
