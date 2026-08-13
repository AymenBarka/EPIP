# Decision Determinism

EPIP-016 determinism requires identical immutable inputs to reproduce identical
Evidence, Hypotheses, Scenarios, graph, Candidates, Confidence Assessments,
Decisions, explanations, traces, digests, and snapshots.

Programme H compares complete canonical pipeline payloads. Equality is byte
identity of sorted, compact JSON rather than runtime object identity.

Certification digests exclude system time, benchmark timing, random values,
memory addresses, hash seeds, discovery order, and mutable runtime state.
Collections and report fields use explicit ordering before serialization.

A mismatch produces determinism, digest, and serialization diagnostics and
prevents certification. Replay differences are preserved for audit; they are
never normalized away or repaired.
