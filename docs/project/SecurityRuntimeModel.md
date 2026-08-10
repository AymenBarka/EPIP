# Security Runtime Model

The runtime model separates three concerns:

- declarative contracts describe architectural expectations;
- bindings identify where an application wants a policy;
- explicit adoptions authorize runtime evaluation.

Decisions are `ALLOW`, `DENY`, `REPORT_ONLY`, `IGNORE`, `DELEGATE`, or
`UNKNOWN`. Results sort violations by stable code and message. Context
attributes and registry contents are read-only and deterministically ordered.

The runtime has no clock, random source, network access, filesystem access, or
implicit identity generator. Repeated evaluation of the same immutable inputs
therefore produces equal results.
