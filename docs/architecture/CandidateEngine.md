# Candidate Engine

The Candidate Engine is the EPIP-016 boundary that transforms validated decision
inference outputs into deterministic decision candidates. It does not rank,
recommend, execute, or apply financial policy.

## Responsibilities

- Build immutable candidates from explicit scenario, evidence, and graph inputs.
- Enforce the official candidate lifecycle.
- Validate references before registration.
- Maintain deterministic indexes and snapshots.
- Produce audit, diagnostic, statistical, and generation reports.

## Components

| Component | Responsibility |
| --- | --- |
| `CandidateBuilder` | Builds one immutable candidate from validated inputs. |
| `CandidateEngine` | Coordinates generation without selecting a preferred candidate. |
| `CandidateRegistry` | Stores and queries candidates through deterministic indexes. |
| `CandidateReferenceResolver` | Validates scenario, evidence, and graph references. |
| `CandidateCollection` | Provides an immutable ordered candidate collection. |
| `CandidateSnapshot` | Captures replay-compatible registry state. |
| `CandidateDigest` | Exposes stable content identity. |

## Architectural boundaries

The engine consumes decision-domain objects, evidence results, inference results,
and decision-graph references. It produces candidate-domain records only. It
does not consume market, risk, execution, or portfolio engines directly.

All ordering, identifiers, digests, snapshots, and serialized payloads are
deterministic for identical inputs. Registry queries return immutable tuples and
never expose mutable internal indexes.

## Compatibility

The Programme E API is additive. Existing EPIP-001 through EPIP-015 APIs and the
EPIP-016 Programme A through D behavior remain unchanged.
