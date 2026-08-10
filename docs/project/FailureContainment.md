# Failure Containment

Containment boundaries are declarative:

- component isolation;
- plugin isolation;
- provider isolation;
- adapter isolation;
- session isolation;
- call isolation;
- security-boundary isolation;
- external-system isolation.

A boundary describes intended ownership. It does not start threads, terminate
resources, suppress failures, or roll back state. Runtime enforcement requires a
separate, explicit application integration.
