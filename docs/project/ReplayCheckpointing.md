# Replay Checkpointing

Replay checkpoints are private immutable descriptions of mutable runtime
state. They copy containers while reusing immutable candles, contexts and
feature sets.

Rollback restores session state, contexts, windows, clock position, scheduler
heap, iterator pages and cursors, statistics, FeatureStore cache and history.
Temporary iterators and events created by a failed run become unreachable.

The mechanism does not checkpoint providers, Kernel, plugins or EventBus.
