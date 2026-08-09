# Degradation Policies

`FallbackPolicy` defines the only supported high-level responses:

- `FAIL`;
- `RETURN_DEFAULT`;
- `RETURN_EMPTY`;
- `RETURN_LAST_KNOWN_VALUE`;
- `RETURN_CACHED_VALUE`;
- `RETURN_DEGRADED_RESULT`;
- `SKIP_OPERATION`;
- `DISABLE_FEATURE`;
- `READ_ONLY_MODE`;
- `CUSTOM`.

`FAIL` records a deterministic rejection and never applies a fallback. Other
policies apply only when an official failure is classified, the service is
degraded, the circuit is open, or the caller makes an explicit manual request.

Policy and action are separate: policy expresses intent, while action records
the exact strategy used to materialize the result.
