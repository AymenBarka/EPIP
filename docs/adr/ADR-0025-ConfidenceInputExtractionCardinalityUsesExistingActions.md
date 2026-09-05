# ADR-0025: Confidence Input Extraction Cardinality Uses Existing Actions

- **Status:** Accepted
- **Milestone:** P02-F14 confidence input candidate cardinality reconciliation
- **Decision scope:** Generic P02 mapping behavior only

## Context

Source extraction returns a tuple containing zero, one, or many semantic candidates, while one
`ConfidenceInputValue` contains one candidate. `ConfidenceInput` has no selection or ranking rule.
Choosing an item by tuple position, canonical identifier, frame, or binding order would add hidden
semantic ranking to generic P02 execution.

`ConfidencePolicy` already contains `missing_action` and `conflict_action`, and each
`ConfidenceInput` already declares whether it is required. These fields are serialized and
profile-identified.

## Decision

Confidence input cardinality is a mechanical boundary:

- zero candidates and source-extraction `NO_MATCH` activate `missing_action`;
- exactly one candidate constructs one `ConfidenceInputValue` using that exact candidate;
- two or more candidates activate `conflict_action` without selecting a winner.

`NO_FACT` may omit only an optional input. Required inputs never omit. `REJECT` and
`REQUIRE_SINGLE` reject a cardinality failure. Because the current confidence profile has no
selection-rule field, activated `REQUIRE_EXPLICIT_SELECTION_RULE` is invalid input rather than an
instruction to discover or invent a rule.

`ConfidenceInputValue` remains singular. No new selection rule, ranking rule, profile field,
closure edge, executable type, or serialization schema is introduced. Included inputs retain
canonical policy order. Every confidence variant requires at least one included runtime input;
`DIRECT` requires exactly one.

## Consequences

P02 can distinguish missing, singular, and conflicting extraction outcomes without semantic
guessing. Optional omissions are explicit and diagnosed. A zero-input model invocation is
forbidden. F10/F11 frame scope and F12/F13 exact closure remain sufficient and unchanged.

The rejected alternatives are first/canonical winner selection, hidden ranking, a new selection
rule, and collection-valued `ConfidenceInputValue`. Each either invents meaning or expands frozen
public contracts unnecessarily.

P02-F15 will implement and test only this cardinality boundary. P02-F09 remains blocked until
P02-F15 closes. P01, A07, P03, P04, and P05 are unchanged.
