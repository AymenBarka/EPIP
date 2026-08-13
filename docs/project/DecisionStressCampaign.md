# Decision Stress Campaign

The institutional campaign defines these deterministic operation counts:

- 100,000 Evidence registrations;
- 100,000 Hypothesis generations;
- 100,000 Scenario generations;
- 100,000 graph traversals;
- 100,000 Candidate generations;
- 100,000 Confidence assessments;
- 100,000 Decision selections;
- 1,000 complete Decision pipelines.

The benchmark entry point executes these counts explicitly against real EPIP-016
operations. Each iteration creates or evaluates an actual immutable framework
artifact: an Evidence registration, Hypothesis or Scenario registration, graph
construction or traversal, Candidate generation, Confidence assessment,
Decision selection, or the complete Evidence-to-Decision pipeline. No no-op
callback is accepted as campaign evidence. Ordinary unit tests exercise the
same operations at bounded counts so continuous validation remains practical.

Campaign outputs are not retained. Only sorted operation counts, failures, and
a canonical digest survive. This bounds registry, snapshot, diagnostics, audit,
and immutable-object retention regardless of campaign size.

Injected faults stop their affected campaign, are recorded deterministically,
and are never repaired.
