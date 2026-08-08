# Financial Validation Matrix

| Area | Formula or invariant | Automated coverage |
| --- | --- | --- |
| Exposure | Gross, net, long, short identities | Long, short, hedged |
| Allocation | Market value / total market value; fractions sum to one | Multi-position |
| Margin | Required = notional / leverage; used = prior used + required; remaining = max(0, available - used) | Normal and zero notional |
| Kelly | Bounded optimal fraction | Zero, neutral, positive, certain |
| PnL | Floating = unrealized; realized is cumulative net commission | Construction and calculation |
| Periodic PnL | Daily, weekly, monthly are unavailable without a period ledger | `None` and serialization round trip |
| Equity | Current = initial + realized + unrealized - commission; peak = max(previous peak, current); drawdown = (peak - current) / peak | Identity and boundary tests |
| Average cost | Weighted increase, unchanged partial-close basis, close removal, reversal basis reset | Long and short lifecycle tests |
| Commission | Fixed per fill; rate times notional; amount times normalized quantity | Exact parameterized formulas |
| Execution | Quantity-weighted price; unique fills; no overfill | Partial, complete, duplicate, overfill |

The matrix validates only computations currently exposed by EPIP. Multi-currency, settlement,
instrument metadata, mark-to-market sourcing, calendars, and statistical correlation are deferred
capabilities and are not simulated by Hardening-003.
