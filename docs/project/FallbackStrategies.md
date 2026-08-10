# Fallback Strategies

EPIP supports the following explicit strategies:

- cached value;
- last known value;
- secondary provider;
- secondary adapter;
- empty response;
- default response;
- partial response;
- read-only mode;
- degraded mode;
- disabled mode;
- skipped operation;
- manual fallback;
- custom fallback.

The selected action is part of the immutable contract. The runtime never
searches for an alternative and never substitutes a value implicitly. Every
value is provided in the evaluation context.

Partial and empty results require explicit configuration flags. Disabled and
read-only strategies expose their lost capabilities in diagnostics.
