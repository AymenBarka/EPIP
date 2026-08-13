# Decision Certification

Institutional certification is issued only when all required validation domains
pass and stress or benchmark campaigns report no failures or anomalies.

The certification record covers architecture, determinism, explainability,
replay compatibility, immutability, registry integrity, serialization, digest
stability, Decision reproducibility, backward compatibility, and cross-module
consistency. Its canonical SHA-256 digest depends only on these boolean facts.

## Process

1. Instantiate real Decision Domain values and Evidence, Inference, Graph,
   Candidate, Confidence, and Decision engines and registries.
2. Execute the complete Evidence → Hypothesis → Scenario → Decision Graph →
   Candidate → Confidence Assessment → Decision pipeline twice.
3. Compare the real Decisions, explanations, traces, snapshots, digests, and
   canonical JSON byte-for-byte.
4. Validate real registry contents, explanations, serialization, and digests.
5. Execute real-operation stress and fault campaigns.
6. Record real-operation engineering benchmark observations.
7. Produce the immutable certification and validation snapshot.

## Limitations

Certification establishes structural and deterministic conformance for the
validated software and inputs. It does not guarantee trading performance,
profitability, market correctness, future compatibility, latency, availability,
or execution quality. Benchmark measurements establish no SLA.
