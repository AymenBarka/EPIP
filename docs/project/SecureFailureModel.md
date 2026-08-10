# Secure Failure Model

`SecureFailureIncident` records stable identity, category, severity, boundary,
component, and a concise summary. `SecureFailureContext` contains only explicit
caller input. Neither object captures live exceptions, tracebacks, clocks, or
runtime state.

`SecureFailureContract` declares the categories and severities understood by a
component together with containment intent. `SecureFailureResult` contains the
deterministic decision. `SecureFailureStatistics` derives counters from supplied
results and creates no observations implicitly.

`SECURE_FAILURE_CONTRACTS` is immutable, deterministic, complete across the
official containment boundaries, and inactive by default.
