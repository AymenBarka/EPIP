# Confidence Model

A confidence assessment attaches eight independent descriptive metrics to one
candidate:

- confidence: strength of support in the referenced reasoning chain;
- quality: fitness of the referenced material and derivations;
- validity: eligibility of the referenced material for assessment;
- uncertainty: unresolved ambiguity retained by the chain;
- evidence coverage: proportion of candidate references resolved;
- scenario consistency: proportion of scenarios whose declared provenance is
  present on the candidate;
- completeness: presence of the five required identity and provenance groups;
- traceability: proportion of references and graph nodes that are traceable.

Every normalized metric is in the closed interval from zero to one. Confidence,
quality, validity, and uncertainty retain their distinct meanings and are never
collapsed into one value.

Confidence is not a probability of profit, expected return, risk estimate, or
likelihood that a trade will succeed.

Assessments have a deterministic identifier, candidate reference, ordered graph
references, and canonical SHA-256 digest. They are immutable, comparable,
hashable, serializable, and replay compatible.
