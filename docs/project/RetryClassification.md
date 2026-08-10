# Retry Classification

| Classification | Authority |
| --- | --- |
| Retryable | Explicitly eligible under its contract. |
| Non-retryable | Rejected until its cause is corrected. |
| Conditionally retryable | Requires the declared condition to remain true. |
| Never retry | Retry is forbidden. |
| External retry only | Recovery belongs beyond the framework boundary. |
| Framework retry | A future framework adopter may own retry. |
| Caller retry | The caller alone decides whether to retry. |

Responsibilities are assigned to Framework, Caller, Provider, Adapter, Plugin,
External System, Operating System, or User. Classification and responsibility
are separate: eligibility does not transfer ownership.
