# Input Validation Contracts

Input-validation contracts are architecture metadata describing what a
boundary is expected to validate and who owns that responsibility.

## Contract structure

Each `InputValidationContract` declares:

- a stable name and boundary;
- one or more immutable rules;
- supported validation capabilities;
- the responsible party;
- explicit restrictions;
- deterministic declaration semantics.

`InputValidationRegistry` exposes the official declarations through a
read-only mapping. `ValidationAudit` checks structural consistency without
executing any rule.

## Runtime guarantee

The infrastructure is descriptive only. Importing or resolving a contract
does not validate, normalize, reject, mutate, log, or publish anything.
