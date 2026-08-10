# Retry Timing

Every retry configuration can declare maximum attempts, maximum elapsed
duration, initial and maximum delay, backoff coefficient, delay cap, retry
budget, and jitter policy.

Supported jitter declarations are `NONE`, `FIXED`, `FULL`, `EQUAL`, and
`DECORRELATED`. They do not generate random values in Programme C.

All counts and durations must be non-negative. Backoff must be positive,
maximum delay cannot exceed its cap, and `NO_RETRY` requires zero attempts and
zero budget. These construction-time rules make contradictory policies fail
before runtime adoption.
