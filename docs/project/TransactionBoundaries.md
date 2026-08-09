# Transaction Boundaries

`BEGIN → VALIDATION → CALCULATION → BUILD → COMMIT → EVENTS → RETURN`

Validation and calculation are mutation-free with respect to the observable
engine aggregate. Immutable history and graph successors are prepared before
commit. Commit replaces complete references while holding the engine's existing
lock. Event publication is deliberately outside that lock.

Failures before commit preserve the previous snapshot, history, graph and
cache. Provider and plugin side effects remain owned by their respective
adapters and are not represented as engine state transactions.
