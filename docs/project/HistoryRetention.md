# History Retention

Complete historical retention remains the compatibility default for existing
History and Graph objects. Those contracts are explicitly Unbounded, justified
by snapshot and replay completeness, and expose manual cleanup policy.

New deployments may place produced entries behind a Fixed Size, FIFO, Ring
Buffer, or Time Window `RetentionManager`. This opt-in boundary truncates only
the managed view and does not alter existing domain serialization.

Unlimited history must always have a documented justification and an explicit
manual-cleanup responsibility.
