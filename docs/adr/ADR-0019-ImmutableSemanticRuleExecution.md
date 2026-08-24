# ADR-0019: Immutable Semantic Rule Execution and Exact-Version Resolution

## Status

Accepted

## Context

ADR-0018 and the implemented P02-F01 foundation provide exact immutable identities and policy
schemas for analysis-to-A07 mapping. `RuleIdentity` intentionally contains no Python behavior.
Consequently, a generic adapter cannot execute extraction, ranking, geometry, confidence,
eligibility, or MTF references without either inventing strategy semantics or discovering mutable
runtime code. Both outcomes violate ADR-0016 ownership and deterministic replay.

The frozen P01 adapter protocol also accepts only its four original arguments, while P02-F01 adds
an exact semantic profile and typed availability-safe MTF bundle. Those additive dependencies need
an explicit lifecycle without reopening P01 or creating divergent sources of truth.

## Decision

EPIP adopts explicitly injected, immutable, exact-version semantic rule execution.

Persistent `SemanticRuleDeclaration` values bind one `RuleIdentity` to a closed family,
invocation/result kinds, and an immutable implementation declaration ID. A
`ResolvedRuleManifest` is the serializable, fingerprinted closed set. Runtime
`ExecutableSemanticRule` instances declare exactly the same properties and are supplied in a
`ResolvedSemanticRuleSet`. The set validates one-to-one correspondence and exact profile closure.
Missing rules, extras, duplicates, family conflicts, and identity mismatches fail closed.

Python code is never serialized, hashed by address or `repr`, dynamically imported from user data,
or discovered from a registry. P03 will explicitly construct and inject implementations. P04 owns
concrete Elliott/Fibonacci rule implementations and profile content. P05 owns concrete MTF
aggregation implementations. P02 owns only structural filtering, exact dispatch, output validation,
fact assembly, and P01 result construction.

Rules use closed immutable request and result unions. Source extraction is performed only by exact
source-extraction rules over one `AnalyticalSourceBinding`; reflection-based field guessing and
private APIs are forbidden. Native P02 logic retains instrument, timeframe, provenance,
closed-state, availability, as-of, revision, and freshness validation.

The future adapter remains conformant with frozen `FactAdapterProtocol`. It is constructed as an
immutable, evaluation-scoped service with the exact semantic profile, resolved rules, typed source
bundle, and an `AdapterInvocationBinding`. On invocation it proves complete equality and identity
continuity with P01 `context`, `inputs`, `profile`, and `policy`. P03 constructs a new bound adapter
for each adaptation; P02 contains no mutable current profile, source, cache, or resolver.

A07 `StrategyEvidenceIdentity` is one deterministic identity for the complete evidence set. Its ID
is a domain-separated SHA-256 over strategy, semantic profile, adapter, typed bundle, manifest, and
ordered evidence-key lineage. Its provenance value is the exact P01 manifest identity. Concrete
keys are taken unchanged from the P04-owned taxonomy.

## Consequences

P02 can later be implemented and tested generically using test-only deterministic rules without
shipping fake strategy semantics. Production acceptance still requires P04 rules and P05 MTF
rules. Persistent documents describe identities and manifests only; executable implementations
must be injected and revalidated after reconstruction.

P01 and P02-F01 remain frozen. P02-F02 is governance only. P02-F03 must implement these additive
contracts before the generic adapter can be authorized. Dynamic lookup, plugin discovery,
filesystem/network resolution, ambient clocks, randomness, `eval`, `exec`, and pickle remain
forbidden.
