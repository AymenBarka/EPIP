# P04-F02-R01 — Geometry / A07 RR Ownership Reconciliation

Status: **RECONCILIATION COMPLETE / IMPLEMENTATION NOT AUTHORIZED**

Scope: P04-F02 responsibility reconciliation only; no implementation

## Purpose and authority

This artifact reconciles P04 Governance Authorization, P04-R00, P04-F00-R02,
P04-F00-R03, P04-F01-R01, P02-R03, P02-R04, the frozen A07 execution plan and
A07 completion evidence. P04-F01 remains complete, closed, and frozen.

The strategy-level requirement remains `minimum_rr == 3.0`, with equality
accepted. That requirement does not assign its implementation to P04-F02.
Frozen A07 E07 exclusively derives directional risk and reward, calculates the
canonical reward/risk ratio, applies `RR >= minimum_rr`, and fails closed for
zero or non-positive risk. P04-F02 MUST NOT compute or gate RR.

## Reconciled responsibility boundary

P04-F02 owns construction and geometric validation of StrategyDirection,
ENTRY, STOP, and TARGET candidates. Geometry completeness means:

- BUY: `stop < entry < target`;
- SELL: `target < entry < stop`.

It does not mean trade-acceptance completeness. P04-F04 will eventually bind
final P04 outputs into the existing A07 evaluation path. A07 E07 then consumes
the canonical A07 entry, stop, and target validations and enforces the RR
requirement. This artifact does not authorize or implement F04.

Any earlier P04 planning prose assigning RR calculation, minimum-RR gating, or
zero-risk decisions to F02 is superseded only for implementation ownership.
The overall P04 strategy requirement `RR >= 3.0` is unchanged.

No new F02 RuleIdentity is required or authorized. RR must not be hidden in an
entry, stop, target, direction, selection, ranking, boundary, or transformation
rule.

## Frozen geometry facts

- The entry interval is the closed ratio interval `[0.618, 0.705]` of W1.
- The snapshot must contain exactly one matching `GoldenZone` and exactly one
  `FibonacciLevel` labelled `ENTRY` inside that zone.
- The P04 entry fact is the entire zone; A07 E04 later chooses the BUY upper
  bound or SELL lower bound and performs policy-precision normalization.
- STOP is W1 `start_price` for BUY and SELL, unchanged and without a buffer.
- TARGET is `W1.start + 1.618 * (W1.end - W1.start)`.
- P04 rejects stop or target candidates on the wrong side of entry, but never
  moves geometry to improve RR.

## Exact F02 catalog ownership matrix

All 20 identities remain `DECLARATION_ONLY` until a later reconciliation
resolves the blockers below. `RR involvement` is `NONE` for every rule.

| Identity suffix | Family | Exact responsibility | Existing request → result | Dependency | F02 state | RR involvement |
| --- | --- | --- | --- | --- | --- | --- |
| `extract.market-structure` | extraction | Extract governed structure direction facts | `SourceExtractionRequest` → `CandidateRuleResult` | MarketStructure snapshot | DECLARATION_ONLY | NONE |
| `applicability.direction` | applicability | Require complete direction agreement or preserve a complete non-actionable result | `ApplicabilityRequest` → `ApplicabilityResult` | Direction facts | DECLARATION_ONLY | NONE |
| `applicability.entry` | applicability | Validate golden-zone ENTRY membership and direction relation | `ApplicabilityRequest` → `ApplicabilityResult` | Fibonacci geometry | DECLARATION_ONLY | NONE |
| `applicability.stop` | applicability | Validate STOP side relative to ENTRY | `ApplicabilityRequest` → `ApplicabilityResult` | ENTRY and STOP | DECLARATION_ONLY | NONE |
| `applicability.target` | applicability | Validate TARGET side relative to ENTRY | `ApplicabilityRequest` → `ApplicabilityResult` | ENTRY and TARGET | DECLARATION_ONLY | NONE |
| `select.entry` | selection | Select the unique governed ENTRY candidate | `CandidateSelectionRequest` → `SelectionRuleResult` | Entry candidates | DECLARATION_ONLY | NONE |
| `select.stop` | selection | Select the unique governed STOP candidate | `CandidateSelectionRequest` → `SelectionRuleResult` | Stop candidates | DECLARATION_ONLY | NONE |
| `select.target` | selection | Select the unique governed TARGET candidate | `CandidateSelectionRequest` → `SelectionRuleResult` | Target candidates | DECLARATION_ONLY | NONE |
| `rank.entry-golden-zone` | ranking | Order governed entry candidates without first-match behavior | `CandidateRankingRequest` → `RankingRuleResult` | Entry candidates | DECLARATION_ONLY | NONE |
| `rank.target-extension-1618` | ranking | Order governed exact-extension candidates | `CandidateRankingRequest` → `RankingRuleResult` | Target candidates | DECLARATION_ONLY | NONE |
| `boundary.entry-0618-0705` | boundary | Materialize the inclusive entry range | `BoundarySelectionRequest` → `BoundaryRuleResult` | Selected zone | DECLARATION_ONLY | NONE |
| `precedence.stop-wave1-origin` | precedence | Prefer the governed W1-origin stop | `CandidateSelectionRequest` → `SelectionRuleResult` | Stop candidates | DECLARATION_ONLY | NONE |
| `transform.stop-identity` | transformation | Convert W1 origin to STOP without changing price | `PriceTransformationRequest` → `PriceTransformationResult` | W1 origin | DECLARATION_ONLY | NONE |
| `transform.target-extension-1618` | transformation | Produce the exact direction-aware W1 extension | `PriceTransformationRequest` → `PriceTransformationResult` | Ordered W1 anchors | DECLARATION_ONLY | NONE |
| `direction.elliott` | direction | Map W1 `UP`/`DOWN` to BUY/SELL | `DirectionRuleRequest` → `DirectionRuleResult` | Elliott direction candidate | DECLARATION_ONLY | NONE |
| `direction.trend` | direction | Reserved catalog declaration; profile currently uses direct-enum mapping | `DirectionRuleRequest` → `DirectionRuleResult` | Structure trend fact | DECLARATION_ONLY | NONE |
| `direction.structure` | direction | Reserved catalog declaration; profile currently uses direct-enum mapping | `DirectionRuleRequest` → `DirectionRuleResult` | Structure state fact | DECLARATION_ONLY | NONE |
| `direction.primary` | direction | Map caller-bound PRIMARY W1 orientation | `DirectionRuleRequest` → `DirectionRuleResult` | Elliott primary fact | DECLARATION_ONLY | NONE |
| `direction.alternate` | direction | Copy primary direction because eligible F01 inputs require empty alternates | `DirectionRuleRequest` → `DirectionRuleResult` | Primary direction | DECLARATION_ONLY | NONE |
| `direction.caller-primary-identity` | MTF aggregation | Identity aggregation over the single caller-bound PRIMARY frame | `MtfAggregationRequest` → `MtfAggregationResult` | PRIMARY direction | DECLARATION_ONLY | NONE |

The current executable catalog remains the five frozen F01 rules. Therefore:

- F01 executable: 5;
- F02 newly executable: 0;
- total executable closure: 5;
- declaration-only: 32.

## Remaining implementation blockers

### Fibonacci geometry transport

Frozen F01 `extract.fibonacci` emits exactly two W1 PRICE anchors and explicitly
emits no ZONE, ENTRY, or TARGET candidate. The entry and target profile
selectors nevertheless reference that same extraction identity. Existing
directional applicability and price-transformation requests do not carry the
typed `FibonacciSnapshot` or an ordered anchor pair. An implementation cannot
lawfully recover the exact GoldenZone, ENTRY level, or extension candidate.

Resolution must preserve F01 and determine an existing-contract dataflow or a
separately governed predecessor amendment. F02 must not mutate F01 output,
encode fields in metadata, infer tuple position, or overload another identity.

### Market-structure fact discrimination

The profile uses one `extract.market-structure` selector for both TREND and
STRUCTURE direct-enum policies. `MarketStructureSnapshot` exposes distinct
trend direction and structure state, while a generic SemanticCandidate has no
direction-fact-name discriminator. A deterministic extraction contract must
freeze how both facts are distinguished without tuple-position semantics or
first-match behavior.

### Ranking and executable closure

The authorities require exactly one GoldenZone, one ENTRY level, W1-origin
STOP, and one exact 1.618 target, but the profile also requires entry/target
ranking and stop precedence identities. Their executable necessity, input
populations, canonical tie behavior, and interaction with unique-candidate
requirements are not yet sufficiently exact. Consequently no non-zero F02
executable set or implementation test count is frozen here.

## Failure and execution boundary

Malformed types, identities, provenance, non-finite prices, or impossible
populations follow P02 `INVALID_INPUT`. Missing required geometry, outside-zone
ENTRY, wrong-side STOP/TARGET, or well-formed unresolved ambiguity follows P02
`REJECTED`. Complete neutral or contradictory direction facts remain a valid
non-actionable path that A07 converts to no signal.

Future F02 execution must stop after each non-success stage: direction failure
prevents entry; entry failure prevents stop and target; stop failure prevents
target handoff; target failure prevents F03/F04 progression. F02 performs no
A07 RR invocation.

## Future validation obligations

A later readiness contract must freeze an exact test-condition count covering
direction, PRIMARY binding, market structure, trend/structure discrimination,
entry boundaries, stop and target geometry, ranking, selection, ambiguity,
provenance, order independence, barriers, isolation, catalog closure, and
predecessor compatibility. It must explicitly prove that P04 contains no RR
calculation and run the frozen A07 regression for RR equality, below-threshold,
and zero-risk behavior without modifying A07 production.

## Gap classification and decision

- G0: RR ownership, strategy threshold, entry inclusivity, W1-origin stop,
  target formula, geometry/decision boundary, and F04 handoff ownership are
  exact.
- G1: earlier prose assigning RR execution to F02 is narrowly superseded.
- G2: existing A07 E07 fully preserves RR evaluation.
- G3: exact Fibonacci geometry transport, structure-fact discrimination,
  ranking/precedence behavior, executable set, and test count remain open.
- G4: the former RR ownership conflict is resolved; no remaining RR conflict.
- G5: Fibonacci geometry transport may require separately governed generic
  contract work if no existing dataflow can be proven sufficient.

Ownership reconciliation is **COMPLETE**. P04-F02 remains **NOT AUTHORIZED**.
P04-F03, P04-F04, and P05 remain **NOT AUTHORIZED**.
