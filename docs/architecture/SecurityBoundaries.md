# Security Boundaries

EPIP models a security boundary as an immutable declaration connecting two
architectural zones. A contract records its classification, directional trust
transition, owner, responsible party, expected validation, visible
capabilities, policy, and restrictions.

The registry is deterministic and read-only. It exists for architecture review,
documentation, and compliance checks. It does not enforce access control.

## Official boundaries

| Boundary | Transition | Ownership | Trust |
| --- | --- | --- | --- |
| `core-provider` | Core → Provider | Core | Partially trusted |
| `core-plugin` | Core ↔ Plugin | Kernel | Untrusted |
| `plugin-eventbus` | Plugin → EventBus | EventBus | Untrusted |
| `provider-engine` | Provider → Engine | Engine | Partially trusted |
| `engine-adapter` | Engine → Adapter | Engine | Trusted |
| `adapter-external` | Adapter ↔ External | Adapter | External trust |
| `user-framework` | User → Framework | Framework | Untrusted |
| `filesystem-framework` | Filesystem → Framework | Framework | External trust |
| `network-provider` | Network → Provider | Provider | External trust |

Every transition declares validation expectations, but validation remains the
responsibility of the named boundary owner or integration component.
