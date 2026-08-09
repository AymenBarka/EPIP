# Commit Model

`EngineTransaction` is an internal reference-replacement primitive. Engines
stage complete candidate attributes and invoke one commit. If a replacement
unexpectedly fails, the primitive restores all prior references and re-raises
the original exception.

The model is intentionally limited to in-memory engine state. It introduces no
public API, persistence mechanism, rollback journal or new synchronization
primitive.
