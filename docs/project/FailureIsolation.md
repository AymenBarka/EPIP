# Failure Isolation

Official isolation scopes are Provider, Adapter, Plugin, External Boundary,
Component, and Caller.

Isolation denies permission for a future operation while a circuit is open. It
does not roll back, mutate, replace, or reinterpret domain state. The caller
retains responsibility for respecting the permit decision and for selecting an
appropriate boundary contract.

Failure accounting uses only an explicit `RetryContract`, `FailureContract`,
and exception taxonomy contract. No exception-name heuristic or hidden retry
rule is permitted.
