# Security Model

EPIP security metadata separates four concerns:

1. classification describes architectural exposure;
2. trust records the assumption at the boundary;
3. responsibility identifies who must satisfy restrictions;
4. capability records what the component may consume or expose.

Security declarations are deterministic and immutable. They describe the current
architecture but do not grant permissions. A capability is an inventory item,
not an authorization decision.

Unknown components fail explicit contract resolution. Invalid declarations fail
construction, and registry audits reject duplicate or contradictory metadata.
