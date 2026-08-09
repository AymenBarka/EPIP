# Memory Growth Model

The H005 registry derives mandatory retention declarations from Programme A
memory contracts. A component is included when it is Cached, Persistent, has a
cache policy, or has a history policy.

Bounded contracts have configuration-bounded growth. Disabled contracts retain
nothing. Manual and Unbounded contracts may grow with input and therefore
require explicit ownership, justification, and cleanup documentation.

`MemoryRetentionRegistry.audit()` reports every relevant component without a
policy. Contract construction rejects negative or zero limits, missing bounded
limits, invalid windows, conflicting cleanup modes, and unjustified unlimited
growth.
