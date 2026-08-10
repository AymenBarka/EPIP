# Leak Detection

A resource becomes a leak candidate when deterministic evidence shows an
incomplete ownership lifecycle, including:

- an orphaned resource handle;
- an incomplete recovery rollback;
- an active resource without a cleanup declaration.

An open recovery scope is reported independently because it may still represent
valid work in progress. Operators decide when that scope has exceeded its
expected logical lifetime.

Leak detection is observational. It never calls `close`, `clear`, `rollback`,
garbage collection, or a finalizer.
