# Input Validation Boundaries

The official registry covers every required ingress or integration boundary:

| Boundary | Principal declared concern |
| --- | --- |
| Public API | Type checking |
| Kernel | Identity verification |
| Replay | Schema verification |
| Providers | Range checking |
| Adapters | Permission declaration |
| Plugins | Identity verification |
| Filesystem | Resource existence |
| Network | Format verification |
| Serialization | Schema verification |
| Configuration | Configuration validation |
| EventBus | Constraint declaration |

These declarations complement security-boundary metadata while remaining
independent of runtime components.
