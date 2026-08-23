# A07 Execution Plan

Status: APPROVED FOR GOVERNANCE DELIVERY  
Baseline: A05-v1.0.0 / A06 v1.5.21  
Reserved release: v1.6.0  
Implementation authorization: E00 ready after this document is published

## 1. Mission and boundaries

A07 is the deterministic Strategy Engine. It consumes immutable analytical,
risk, temporal, and provenance facts and produces `BUY`, `SELL`, or `NO_TRADE`.

A07 does not acquire data, compute predecessor analytics, execute orders, access
MT5, backtest, optimize, walk forward, manage portfolios, or render dashboards.

## 2. Frozen contracts

- `StrategyDirection` is exactly `BUY`, `SELL`, `NO_TRADE`.
- `NO_TRADE` has `entry=None`, `stop=None`, `target=None`, and `rr=None`.
- Public outputs are immutable, deterministic, hashable, and reconstructable.
- Numeric domain is finite float with canonical decimal serialization and
  policy-defined precision; NaN and infinity fail closed.
- Hard-gate failures cannot be compensated by confidence.
- No wall-clock reads or broker precision lookup are permitted.

## 3. Package sequence and ownership

| Unit | Production file | Test file | Public outputs | Owns |
| --- | --- | --- | --- | --- |
| E00 | `epip/a07/foundation.py` | `tests/a07/test_foundation.py` | `StrategyIdentity`, `StrategyEvidenceIdentity`, `StrategyEvaluationRequest`, `StrategyDirection`, `StrategyFoundationDiagnostics` | identity and request foundation |
| E01 | `epip/a07/policy.py` | `tests/a07/test_policy.py` | `StrategyPolicyIdentity`, `StrategyPolicy`, `PolicyValidation`, `PolicyDiagnostics` | policy configuration and fingerprint |
| E02 | `epip/a07/evidence.py` | `tests/a07/test_evidence.py` | `StrategyEvidenceSnapshot`, `EvidenceBinding`, `EvidenceValidation`, `EvidenceDiagnostics` | immutable predecessor evidence binding |
| E03 | `epip/a07/direction.py` | `tests/a07/test_direction.py` | `DirectionalDecision`, `DirectionValidation`, `DirectionDiagnostics` | directional eligibility and NO_TRADE reasons |
| E04 | `epip/a07/entry.py` | `tests/a07/test_entry.py` | `EntryPrice`, `EntryValidation`, `EntryDiagnostics` | entry geometry only |
| E05 | `epip/a07/stop.py` | `tests/a07/test_stop.py` | `StopLoss`, `StopValidation`, `StopDiagnostics` | stop geometry only |
| E06 | `epip/a07/target.py` | `tests/a07/test_target.py` | `TakeProfit`, `TargetValidation`, `TargetDiagnostics` | target geometry only |
| E07 | `epip/a07/reward_risk.py` | `tests/a07/test_reward_risk.py` | `RewardRiskOutcome`, `RewardRiskValidation`, `RewardRiskDiagnostics` | RR and applicable risk acceptance |
| E08 | `epip/a07/confidence.py` | `tests/a07/test_confidence.py` | `StrategyConfidence`, `SignalExpiration`, `ConfidenceValidation`, `ConfidenceDiagnostics` | confidence, expiry, rationale inputs |
| E09 | `epip/a07/signal.py` | `tests/a07/test_signal.py` | `StrategySignal`, `SignalValidation`, `SignalDiagnostics` | integrated signal closure |

Only the listed files may be changed by each unit. No aliases, wildcard exports,
predecessor internals, or successor imports are allowed.

## 4. Dependency DAG

```text
E00 -> E01 -> E02 -> E03
                 |\
                 | +-> E04
                 | +-> E05
                 | +-> E06
E03 + E04 + E05 + E06 -> E07
E02 + E03 + E07 -> E08
E02 + E03 + E04 + E05 + E06 + E07 + E08 -> E09
```

E04, E05, and E06 are siblings and must not import one another.

## 5. Unit contracts

E00 validates identity, evidence identity, request shape, canonical timestamps,
baseline references, immutability, hashing, and reconstruction. It owns no strategy logic.

E01 validates policy identity, enabled directions, minimum RR/confidence, evidence
requirements, expiration, numeric policy, Elliott policy, and deterministic fingerprints.

E02 adapts only immutable predecessor snapshots. It preserves provenance, freshness,
temporal eligibility, mandatory/optional evidence, and A05/A06 continuity. It never recomputes analytics.

E03 resolves BUY/SELL/NO_TRADE from eligible Elliott, trend, structure, policy, and
MTF facts. Primary/alternate conflict is NO_TRADE. It owns no geometry.

E04 derives and validates supported entry geometry only.

E05 derives stops with precedence: Elliott invalidation, structure/swing, supported
volatility, explicit policy buffer. BUY stop is below entry; SELL stop is above entry.

E06 derives targets with precedence: Elliott projection, Fibonacci extension,
structure/liquidity, and policy-authorized RR fallback. It may not manufacture targets.

E07 validates finite positive risk/reward and `RR >= minimum_rr`, plus immutable risk acceptance.

E08 computes confidence in `[0,1]`, applies `confidence >= minimum_confidence`, derives
expiry from immutable evaluation time and policy, and never reads the wall clock.

E09 validates identity, policy, evidence, provenance, direction, geometry, RR, confidence,
expiry, and diagnostics without recomputation. BUY/SELL require complete geometry.

## 6. Hard gates and diagnostics

Hard gates are: identity, provenance, policy, temporal eligibility, freshness, direction
permission, Elliott validity/tradeability, structure compatibility, MTF compatibility,
entry, stop, target, RR, risk acceptance, and confidence threshold.

Contract corruption is a contract failure. A valid but non-tradeable market setup is
`NO_TRADE`. Canonical reasons include missing evidence, stale evidence, temporal ineligibility,
identity mismatch, context conflict, invalid wave, trend/MTF conflict, invalid geometry,
low RR, risk rejection, insufficient confidence, and policy rejection.

## 7. Required tests and baselines

Each unit requires positive, negative, boundary, immutable, hash/equality, deterministic
reconstruction, permutation, provenance, and fail-closed tests. Required invariants include:

- BUY: `stop < entry < target`;
- SELL: `target < entry < stop`;
- positive risk and reward;
- NO_TRADE has no executable geometry;
- invalid evidence never produces BUY/SELL.

Baseline accounting is explicit: historical A06 evidence is 2075 tests; current PRE-A07
full tracked baseline is 2085. Every unit reports pre-package baseline, package contribution,
post-package baseline, and current full baseline.

## 8. Quality and remote gates

Every unit requires Black, Ruff, MyPy strict, component tests, A05 regression, A06 regression,
full tracked regression, statement and branch coverage, `git diff --check`, and documentation
validation where applicable. Required remote workflows are Quality, CodeQL, and Documentation.

## 9. Git, publication, and freeze

Use one atomic commit per package with subjects:

```text
feat(a07): establish E00 strategy foundation
feat(a07): establish E01 strategy policy
feat(a07): bind E02 strategy evidence
feat(a07): establish E03 directional decision
feat(a07): derive E04 entry geometry
feat(a07): derive E05 stop geometry
feat(a07): derive E06 target geometry
feat(a07): establish E07 reward risk
feat(a07): establish E08 confidence and expiration
feat(a07): complete E09 strategy signal
```

After local validation, commit, push to `origin/develop`, verify exact-SHA remote gates,
then mark the unit CLOSED/FROZEN. Frozen predecessors cannot be silently modified.

## 10. Release model

`v1.6.0` remains RESERVED during implementation. No tag or release document is created now.
The release may be prepared only after E00–E09 are CLOSED/FROZEN, full regression, coverage,
Quality, CodeQL, Documentation, clean synchronization, and final closure review all pass.

## 11. Governance acceptance

```gherkin
Feature: package ownership
  Scenario: unauthorized file change
    Given a unit owns its declared production and test files
    When another file is modified
    Then delivery is blocked

Feature: predecessor freeze
  Scenario: successor attempts predecessor mutation
    Then delivery is blocked pending governance reconciliation

Feature: baseline accounting
  Scenario: package contribution
    Then pre-package, contribution, post-package, and full baselines are recorded

Feature: remote gate closure
  Scenario: pending workflow
    Then the unit is not CLOSED

Feature: release reservation
  Scenario: incomplete A07
    Then v1.6.0 remains RESERVED and untagged
```

## 12. Acceptance criteria

E00–E09 are COMPLETE only when their contracts, tests, quality gates, coverage, and boundaries
pass. They are CLOSED only after exact authorized-file commit, publication, remote verification,
and clean tracked-tree inspection. A07 is COMPLETE only after all units close and final release
verification succeeds.
