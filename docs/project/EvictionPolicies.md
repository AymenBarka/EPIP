# Eviction Policies

Eviction is deterministic and operates under one lock over an ordered mapping.
FIFO, Fixed Size, and Ring Buffer remove the earliest retained key. LRU moves a
successfully accessed key to the newest position. Time Window removes entries
whose explicit timestamp is older than the calculated logical cutoff.

The manager exposes immutable ordered snapshots and an eviction counter.
Equivalent insertions, accesses, policies, and timestamps produce equivalent
snapshots. No policy depends on wall-clock time, GC timing, random values, or
hash iteration order.
