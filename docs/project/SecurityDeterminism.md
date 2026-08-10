# Security Determinism

Given identical declarations, observations, logical time, and ordering inputs, H007
produces identical decisions, diagnostics, snapshots, and canonical JSON reports.

Validation hashes canonical representations with sorted keys and compact separators.
Wall-clock time, object identity, random values, filesystem ordering, and thread
scheduling are excluded from security equality and acceptance decisions.
