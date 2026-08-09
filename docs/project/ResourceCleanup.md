# Resource Cleanup

## Close policy

`ResourceHandle.close()` changes the resource to Closing before invoking its
cleanup operation. A successful operation commits Closed. A raised exception
commits Failed and is wrapped in `ResourceCleanupError`; a later explicit close
may retry cleanup.

Repeated close after Closed is safe and does not invoke cleanup again. It is
recorded as a double-close attempt for audit purposes.

## Cleanup selection

The caller may provide a typed close callback. Otherwise, a resource satisfying
`AutoCloseableResource` has its `close()` method called. A handle without a
runtime cleanup function still transitions deterministically, which supports
logical handles whose cleanup is owned externally.

## Group cleanup

`LifecycleManager.close_all()` snapshots handles in sorted-name order and
attempts every cleanup even when an earlier resource fails. The manager raises
one aggregate `ResourceCleanupError` after all attempts.

## Audit signals

The immutable audit reports resources never closed, abandoned resources,
double close, use after close, invalid transitions, and ownership violations.
