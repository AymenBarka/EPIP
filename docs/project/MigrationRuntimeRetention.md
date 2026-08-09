# Migration Runtime Retention

## Progressive migration

1. Resolve the component's official retention contract.
2. Wrap the existing instance with `adopt_runtime_retention`.
3. Route newly managed retained entries through `retain`.
4. Validate immutable snapshots and eviction counts.
5. Opt into a bounded policy only after domain retention requirements approve
   deletion.

## Compatibility

No existing collection is silently imported, truncated, or serialized by the
adapter. Existing business state remains owned by the original component. This
separation prevents regression and allows incremental adoption per runtime.
