# Fairness

EPIP guarantees eventual progress in the tested finite workloads, not strict scheduling fairness.
The 64-publisher campaign gives every publisher the same work and verifies complete progress without
starvation. Operating-system scheduling and Python runtime scheduling remain outside EPIP control.
