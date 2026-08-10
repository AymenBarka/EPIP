# Secure Recovery Policies

Supported policies are fail fast, fail safe, contain, isolate, report, escalate,
ignore, delegate, and custom. They map to deterministic decisions only through
an explicit `SecureFailureAdapter.decide` call.

Official contracts remain disabled. A disabled contract always produces the
`UNKNOWN` decision, ensuring that importing or registering declarations cannot
change historical runtime behaviour. Custom policy execution is not provided;
it remains an explicit integration responsibility.
