# Reliability Diagnostics

Reliability diagnostics are deterministic explanations of objective contract
or observation violations. They include stable codes for missing declarations,
invalid boundaries, contract contradictions, incompatible retry decisions,
incoherent circuit-breaker observations, and incompatible fallbacks.

Diagnostics do not recover a component and do not modify the observed source.
An empty diagnostic collection is valid. Consumers should use the code for
automation and the message for operator context.
