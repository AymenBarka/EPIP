# Trust Transitions

Trust transitions record source, destination, direction, ownership,
responsibility, expected validation, and source trust. They are immutable and
returned in deterministic boundary-name order.

## Policy vocabulary

- **Allowed** — capability is architecturally accepted.
- **Restricted** — capability requires documented boundary validation.
- **Forbidden** — capability must not cross the boundary.
- **Delegated** — responsibility belongs to the destination integration.
- **Observed** — capability is monitored by architectural review.
- **Documented** — no enforcement is claimed beyond explicit documentation.

These values are descriptive. No policy in Programme B changes execution.
