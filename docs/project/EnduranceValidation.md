# Endurance Validation

EPIP defines three explicit endurance tiers:

| Tier | Cycles | Execution policy |
| --- | ---: | --- |
| CI | 100,000 | Required for bounded recovery and retention scenarios |
| Extended | 500,000 | Manual or scheduled benchmark |
| Institutional | 1,000,000 | Dedicated benchmark environment |

Every tier validates completed cleanup, zero open scopes, deterministic
retention order, stable audit output, and the absence of observable orphaned
objects after ownership is released.

Recovery trace and lifecycle audit history intentionally preserve complete
evidence for compatibility. Their workload-proportional logical growth is
expected retention, not an unexplained leak. Production owners must use the
documented lifecycle and retention boundaries when choosing campaign scope.
