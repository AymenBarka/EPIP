# Resource State Machine

## States

| State | Meaning |
| --- | --- |
| Created | Handle exists but is not initialized |
| Initialized | Resource initialization is complete |
| Active | Resource can be used |
| Idle | Resource remains initialized but inactive |
| Closing | Cleanup is in progress |
| Closed | Cleanup completed successfully |
| Failed | Operation or cleanup failed coherently |
| Aborted | Work was abandoned before normal completion |

## Transitions

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Initialized
    Initialized --> Active
    Initialized --> Idle
    Active --> Idle
    Idle --> Active
    Created --> Closing
    Initialized --> Closing
    Active --> Closing
    Idle --> Closing
    Failed --> Closing
    Aborted --> Closing
    Closing --> Closed
    Closing --> Failed
    Created --> Failed
    Initialized --> Failed
    Active --> Failed
    Idle --> Failed
    Created --> Aborted
    Initialized --> Aborted
    Active --> Aborted
    Idle --> Aborted
    Failed --> Aborted
```

Closed is terminal. Use is allowed only after initialization and outside
Closing, Closed, Failed, and Aborted. Unsupported transitions raise
`InvalidLifecycleTransitionError` and are audited.
