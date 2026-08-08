# Data Integrity Migration Guide

## Consumer Changes

Consumers should catch `DataIntegrityError` at external ingestion boundaries and reject the entire
message or transaction. Catching broad exceptions and continuing with a partial payload is unsafe.

```python
from epip.core import DataIntegrityError

try:
    snapshot = SnapshotType.from_json(payload)
except DataIntegrityError as exc:
    quarantine(payload, reason=str(exc))
```

## Behaviour Changes

- NaN and infinity are rejected instead of propagating.
- Out-of-range probabilities are rejected instead of silently clamped.
- Invalid versions fail during object construction rather than in a later engine.
- Malformed snapshot payloads raise `SerializationIntegrityError`.
- EventBus refuses invalid validatable payloads before adding them to history.

Valid serialized objects and legacy payloads using documented optional defaults remain compatible.
