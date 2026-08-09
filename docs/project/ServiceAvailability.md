# Service Availability

EPIP declares seven service-availability levels:

- `AVAILABLE`;
- `DEGRADED`;
- `LIMITED`;
- `UNAVAILABLE`;
- `READ_ONLY`;
- `DISABLED`;
- `UNKNOWN`.

Transitions are validated by a deterministic state table. Invalid transitions,
including a direct transition from `DISABLED` to `READ_ONLY`, are rejected.

Every applied fallback reports its resulting level, remaining capabilities,
and disabled features. Availability describes the service surface; it does not
alter a financial result or infer the health of another component.
