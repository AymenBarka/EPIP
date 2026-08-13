# Decision Selection

Selection first requires exactly one Confidence Assessment for every Candidate.
Candidates without declared constraints are invalid. A Candidate is admissible
only when every declared mandatory constraint is accepted. Non-mandatory results
remain visible in the trace but do not block selection.

Admissible Candidates use this fixed lexicographic policy:

1. Higher validity.
2. Higher confidence.
3. Higher quality.
4. Lower uncertainty.
5. Higher Evidence coverage.
6. Higher Scenario consistency.
7. Higher completeness.
8. Higher traceability.
9. Lexicographically smaller Candidate identifier.

There are no weights, aggregate scores, random tie-breakers, learned rules, or
implicit collection-order preferences. The final identifier is derived from the
selected Candidate, assessment digest, and immutable decision context.

The engine selects but never analyses market data. Assessment values and
constraint outcomes are consumed as immutable facts and are never recomputed.
