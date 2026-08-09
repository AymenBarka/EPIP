# Replay Atomicity

ReplayEngine exposes a fully completed ReplaySession or the exact state that
preceded `run()`. While execution is active, existing Replay-owned locks prevent
session, clock, scheduler, statistics and FeatureStore readers from observing
intermediate state.

The checkpoint contains session state, contexts, candle windows, clock
position, scheduler heap and iterator cursors, statistics counters, and
FeatureStore cache/history. Replay events remain local until commit.
