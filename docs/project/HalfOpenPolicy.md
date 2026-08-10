# Half-Open Policy

Half-open behaviour is controlled by:

- maximum trial count;
- consecutive success threshold;
- consecutive failure threshold;
- logical open duration.

Both single-trial and N-trial policies are represented through configuration.
No wall clock is required. The caller supplies monotonic logical time, making
identical sequences produce identical state transitions and snapshots.
