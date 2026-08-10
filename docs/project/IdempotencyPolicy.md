# Idempotency Policy

EPIP does not claim exactly-once execution across an external boundary.

- Pure feature calculations and stable reads may be idempotent for identical immutable inputs.
- Provider reads are conditionally idempotent because remote data can change.
- Paper and broker submissions are non-idempotent unless the external protocol deduplicates a
  stable client request identifier.
- Event publications, callbacks, logging, clock reads, and UUID generation are non-idempotent.
- Retrying a timeout produces at-least-once attempts and can duplicate a remote write.

The adapter or caller decides whether an operation is safe to retry. EPIP never interprets retry
success as proof of exactly-once delivery.
