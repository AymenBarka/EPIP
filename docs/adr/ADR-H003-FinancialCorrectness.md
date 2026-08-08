# ADR-H003: Financial Correctness

## Status

Accepted for Hardening-003 review.

## Decision

EPIP retains binary floating-point public APIs for backward compatibility, while every financial
boundary requires finite values and explicit algebraic invariants. Currency quantization remains
the responsibility of the future instrument specification layer because EPIP currently has no
currency, tick-size, or contract-size metadata.

Zero-notional margin uses a finite neutral safety ratio of `1.0`. Exposure identities are enforced
with a scale-relative tolerance of `1e-12` to accommodate IEEE-754 summation without accepting
material accounting inconsistencies.

Average cost is the official position accounting policy. Increases use quantity-weighted average
price; reductions retain the existing basis; complete closes remove the position; and reversals
realize the closed quantity before resetting the residual position basis to the reversal fill.

Daily, weekly, and monthly PnL are explicitly `None` because EPIP has neither a trading calendar
nor a period ledger. Cumulative realized PnL must never be presented as periodic performance.
Previously serialized numeric periodic values remain readable for backward compatibility.

Commission is calculated when a fill is created. `FIXED` is one configured monetary amount per
fill, `PERCENTAGE` is a decimal rate multiplied by fill notional (`quantity * price`), and
`PER_LOT` is a monetary amount multiplied by normalized fill quantity.
