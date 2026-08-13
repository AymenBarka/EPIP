# Decision Constraints

Decision constraints are immutable results produced by their authoritative
domains. Supported ownership categories include Risk, Portfolio, Exposure,
Capital, Policy, Compliance, Security, and Runtime.

Each result declares an identifier, category, acceptance result, mandatory flag,
reason, and version. The Decision Engine validates uniqueness and consumes the
declared result. It does not calculate or reinterpret the underlying fact.

Mandatory constraints fail closed. A rejected mandatory result makes its
Candidate inadmissible. A missing constraint set is a structural validation
failure rather than implicit approval. Optional rejections remain in the
Decision Trace and explanation.

The engine performs no financial validation, market validation, portfolio
calculation, policy derivation, or security evaluation.
