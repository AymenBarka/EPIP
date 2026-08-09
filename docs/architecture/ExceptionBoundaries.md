# Exception Boundaries

Each boundary declares the complete propagation contract without implementing
it.

| Boundary | Visibility | Owner | Recovery expectation |
| --- | --- | --- | --- |
| Internal | Internal | Framework | None |
| Public API | Public | Framework | Caller correction |
| Plugin | Operator | Plugin | Recreate component |
| Provider | Operator | Provider | External recovery |
| Adapter | Operator | Adapter | External recovery |
| External | External | External system | External recovery |
| Serialization | Public | Caller | Caller correction |
| Thread | Operator | Framework | Recreate component |
| Replay | Public | Framework | Rollback |
| Kernel | Public | Framework | Rollback |
| EventBus | Public | Framework | Recreate component |

The `capture`, `translation`, `propagation`, `wrapping`, logging responsibility,
visibility, and recovery fields are immutable. Contradictory declarations are
rejected during registry construction.
