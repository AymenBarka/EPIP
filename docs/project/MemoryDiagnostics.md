# Memory Diagnostics

Diagnostics map normalized observations to explicit H005 violations.

The model detects:

- missing memory or retention contracts;
- active resources without cleanup declarations;
- invalid lifecycle or retention state;
- incomplete rollback and open recovery scopes;
- orphaned handles;
- multiple owners for the same logical resource;
- growth beyond an explicitly supplied logical limit.

Each diagnostic identifies a stable component and resource name. Leak
candidates contain evidence only; they never trigger automatic cleanup.
