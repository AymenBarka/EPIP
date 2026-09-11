# P04-F00-R03 — Manifest and Candidate-Binding Reconciliation

Status: **COMPLETE / CLOSED / FROZEN**

Scope: additive P04-F00 declaration migration

Successor authorization: withheld

## Decision and authority

P04-F00 now uses the frozen P02-R03 declaration contracts. The complete P04
inventory is a `SemanticRuleCatalog`; an executable `ResolvedRuleManifest` is
published only when at least one rule has an authorized implementation. P04-F00
has no rule implementation, so `RULE_MANIFEST` is `None` and the executable
closure is exactly empty. The 29 identities referenced by `SEMANTIC_PROFILE`
remain static semantic configuration, not executable bindings.

This record follows P04 Governance Authorization, P04-R00, P04-F00-R02,
P02-R03, ADR-0029, and the current public contracts. It authorizes no P04-F01
or later implementation.

## Catalog and executable closure

All 37 frozen `RuleIdentity` values and fingerprints are unchanged. Every F00
entry is `DECLARATION_ONLY`, has no implementation ID, and is absent from the
executable closure. The catalog is deterministically ordered and round-trips
through the generic P02 serializer.

```text
executable catalog identities = {}
executable semantic-profile closure = {}
ResolvedRuleManifest identities = {}
resolved implementation identities = {}
declaration-only identities ∩ executable closure = {}
```

`SEMANTIC_PROFILE` continues to contain 29 future rule references. Those
references describe required profile semantics; they do not assert that a
callable exists. No generic or P04 callable currently implements any of them.

## Exact 37-rule matrix

| Identity suffix | Family | Owner | F00 state | Static profile | Transition |
| --- | --- | --- | --- | --- | --- |
| `extract.elliott` | extraction | F01 | DECLARATION_ONLY | yes | F01 |
| `extract.fibonacci` | extraction | F01 | DECLARATION_ONLY | yes | F01 |
| `extract.market-structure` | extraction | F02 | DECLARATION_ONLY | yes | F02 |
| `applicability.elliott-wave3` | applicability | F01 | DECLARATION_ONLY | no | F01 |
| `applicability.fibonacci-wave3` | applicability | F01 | DECLARATION_ONLY | no | F01 |
| `applicability.direction` | applicability | F02 | DECLARATION_ONLY | no | F02 |
| `applicability.entry` | applicability | F02 | DECLARATION_ONLY | yes | F02 |
| `applicability.stop` | applicability | F02 | DECLARATION_ONLY | yes | F02 |
| `applicability.target` | applicability | F02 | DECLARATION_ONLY | yes | F02 |
| `invalidation.wave3` | applicability | F03 | DECLARATION_ONLY | no | F03 |
| `select.wave1-anchor` | selection | F01 | DECLARATION_ONLY | no | F01 |
| `select.entry` | selection | F02 | DECLARATION_ONLY | yes | F02 |
| `select.stop` | selection | F02 | DECLARATION_ONLY | yes | F02 |
| `select.target` | selection | F02 | DECLARATION_ONLY | yes | F02 |
| `rank.entry-golden-zone` | ranking | F02 | DECLARATION_ONLY | yes | F02 |
| `rank.target-extension-1618` | ranking | F02 | DECLARATION_ONLY | yes | F02 |
| `boundary.entry-0618-0705` | boundary | F02 | DECLARATION_ONLY | yes | F02 |
| `precedence.stop-wave1-origin` | precedence | F02 | DECLARATION_ONLY | yes | F02 |
| `transform.stop-identity` | transformation | F02 | DECLARATION_ONLY | yes | F02 |
| `transform.target-extension-1618` | transformation | F02 | DECLARATION_ONLY | no | F02 |
| `direction.elliott` | direction | F02 | DECLARATION_ONLY | yes | F02 |
| `direction.trend` | direction | F02 | DECLARATION_ONLY | no | F02 |
| `direction.structure` | direction | F02 | DECLARATION_ONLY | no | F02 |
| `direction.primary` | direction | F02 | DECLARATION_ONLY | yes | F02 |
| `direction.alternate` | direction | F02 | DECLARATION_ONLY | yes | F02 |
| `direction.caller-primary-identity` | MTF | F02 | DECLARATION_ONLY | yes | F02 |
| `confidence.elliott-fibonacci-60-40` | confidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.validity` | temporal | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.revision` | temporal | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.elliott-wave3-setup` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.fibonacci-w1-anchor` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.structure-direction-alignment` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.entry-golden-0618-0705` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.stop-wave1-origin` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.target-extension-1618` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.confidence-elliott-fibonacci-60-40` | evidence | F03 | DECLARATION_ONLY | yes | F03 |
| `evidence.ordering` | ordering | F03 | DECLARATION_ONLY | yes | F03 |

The eight catalog-only identities are `applicability.direction`,
`applicability.elliott-wave3`, `applicability.fibonacci-wave3`,
`direction.structure`, `direction.trend`, `invalidation.wave3`,
`select.wave1-anchor`, and `transform.target-extension-1618`.

## Structural applicability, roles, and transition

`applicability.elliott-wave3` and `applicability.fibonacci-wave3` declare
`STRUCTURAL_APPLICABILITY`. Their future input is
`StructuralApplicabilityRequest`; a directional request fails checked dispatch.
F01 needs no `StrategyDirection` and may inspect only analytical orientation.

Future P04 candidates use only generic roles: setup maps to `QUALIFICATION`, W1
start/end to `ANCHOR_START`/`ANCHOR_END`, and geometry to `ZONE`, `ENTRY`,
`STOP`, and `TARGET`.

The governed transition is explicit:

```text
DECLARATION_ONLY
  -> feature authorization
  -> implementation and implementation identity
  -> executable profile closure
  -> exact ResolvedRuleManifest
  -> catalog state EXECUTABLE
```

It changes no rule ID, version, fingerprint, or family. There is no automatic
promotion, discovery, placeholder implementation, or hidden runtime path.

## Frozen semantic boundaries

F01 may later implement only `extract.elliott`, `extract.fibonacci`,
`applicability.elliott-wave3`, `applicability.fibonacci-wave3`, and
`select.wave1-anchor`. It owns structural W1/W2/W3 qualification, exact anchor
continuity, and raw analytical orientation. It does not emit BUY, SELL, or
NO_TRADE.

Elliott and Fibonacci bindings independently validate against the same
evaluation context, manifest authority, instrument, concrete PRIMARY timeframe,
and PRIMARY role. Their binding or producer-provenance identities need not be
equal. Each candidate retains its own valid identity and provenance.

The enforceable join is exact W1 start/end price equality with Fibonacci
retracement and extension endpoints plus orientation, instrument, timeframe,
role, and evaluation authority. Fibonacci has no Elliott wave indices,
timestamps, count identity, or degree; those joins must not be fabricated.

W1 and W2 are exactly two completed, same-degree, contiguous primary waves,
labelled `WAVE_1` and `WAVE_2`, with opposing orientations and exact
`W2.start_price == W1.end_price`. The count is valid with no violations or
alternates; the projection exists with `next_wave == WAVE_3`.

The W2 origin boundary is strict: bullish requires
`W2.end_price > W1.start_price`; bearish requires
`W2.end_price < W1.start_price`. Equality is invalid. Comparisons use exact
finite values without tolerance. A well-formed non-match is `REJECTED`;
malformed input is `INVALID_INPUT`.

## Ownership and supersession

F00 owns configuration, identity, catalog, and static profile declarations. F01
owns structural setup and anchors. F02 exclusively owns StrategyDirection,
inclusive ENTRY membership, entry, stop, and target. F03 owns confidence,
invalidation, expiration, and evidence. F04 owns integration and A07 invocation.
P05 owns higher/lower timeframe hierarchy, confirmation, voting, and aggregation.

This narrowly supersedes P04-R00's implication that direction conversion or
ENTRY membership resides in the setup slice. R00's mapping and inclusive ENTRY
semantics remain authoritative, but their runtime owner is F02. Analytical
orientation is not strategy direction.

## Implementation evidence

- focused P04-F00: 10 passed;
- P02: 241 passed; P03: 59 passed; A07: 571 passed;
- combined predecessor/P04 selection: 881 passed;
- collection: 2,961, three additions and zero removals;
- selected regression: 2,960 passed, one stress test deselected;
- EventBus stress: passed independently;
- aggregate coverage: 97%; changed P04 package coverage: 100%;
- compliance inventory: 609 with unchanged digest.

Final static, documentation, and exact-SHA remote evidence belongs to the
closure commit. P04-F01 through P04-F04 and P05 remain **NOT AUTHORIZED**.
