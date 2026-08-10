# Graceful Degradation

The graceful-degradation layer is an optional core runtime. It sits above the
official reliability, exception, retry, and circuit-breaker contracts and does
not replace any of them.

## Decision inputs

A fallback decision depends only on:

- an immutable `FallbackContract`;
- an explicit `FallbackContext`;
- the declared failure and exception classification;
- retry exhaustion;
- circuit-breaker state;
- current service availability;
- caller-supplied logical time.

## Runtime boundary

`FallbackRuntime` performs no primary operation. It evaluates a context,
selects only the action declared by its contract, returns an immutable result,
and records bounded diagnostic history. Values used for cached, previous,
secondary, default, partial, or custom responses are supplied explicitly by
the adopter.

## Adoption

No engine, provider, adapter, EventBus, Replay component, or Kernel component
adopts fallback automatically. Adoption requires a declared contract and an
explicit runtime call.
