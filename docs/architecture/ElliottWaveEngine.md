# Elliott Wave Engine Architecture (EPIP-011)

## Purpose and Boundary

The Elliott Wave Engine is EPIP's only official wave-analysis source. Its production dependencies
are limited to Core, EventBus, and Market Context. It never imports or recomputes Swing, Market
Structure, Liquidity, or Fibonacci; all evidence is consumed through `MarketContextSnapshot`.

## Wave Model

Immutable waves carry label, degree, endpoints, direction, and length. Sequences represent impulse,
ABC, flat, zigzag, triangle, diagonal, combination, or incomplete patterns. Counts include bounded
confidence, probability, confluence, quality, status, and explicit rule violations.

## Rules and Validation

Rules are pure, independently registered checks. Canonical rules prevent Wave 2 from exceeding the
Wave 1 origin, prevent Wave 3 from being shortest, and prevent Wave 4 overlap unless diagonal
overlap is configured. Pattern validation covers impulse, ABC, flat, zigzag, triangle, and diagonal
cardinality and labels.

Official Fibonacci probability and confluence validate wave proportions. Official resting liquidity
pools validate termination evidence. Both are read only from Market Context.

## Counts, Alternates, and Projections

The primary counter scores completeness and upstream confluence deterministically. Alternate counts
retain their own probability, confidence, quality, confluence, and status. Projections identify the
next wave, expected retracement, targets, and termination zones using official Fibonacci extension
levels, with liquidity pools as a fallback.

## Graph and History

History is immutable and queryable by version or timestamp. The graph supports previous/next,
parent/child, alternate, and projection relations for future Decision traversal. Engine state is
isolated per symbol/timeframe under `RLock`.

## Integration

Decision, Risk, Execution, and AI modules consume only immutable `WaveSnapshot` instances. Typed
events expose detection, validation, invalidation, alternates, count updates, and projections.
