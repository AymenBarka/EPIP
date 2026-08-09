# Engine Atomicity

EPIP stateful engines follow a single in-memory commit model:

1. validate inputs;
2. calculate using local temporary values;
3. build immutable snapshot, history and graph candidates;
4. replace all engine-owned references under the existing engine lock;
5. publish events after releasing the engine lock;
6. return the committed snapshot.

The boundary prevents snapshots, histories, graphs, caches and portfolio
position accounting from exposing partially constructed state.
