# Retention Adoption Guide

Use `adopt_runtime_retention(component)` to retain the documented legacy
policy. Use an explicit matching `MemoryRetentionContract` to opt into a bound.

```python
adapter = adopt_runtime_retention(component)
adapter.retain("logical-key", value)
snapshot = adapter.retained_snapshot()
original = adapter.component
```

The original object remains accessible and unchanged. Removing the adapter is
sufficient to reverse adoption. Time-window policies require explicit logical
timestamps on every retained item.
