# Financial Correctness

EPIP validates these core identities at construction and in institutional tests:

- `gross exposure = long exposure + short exposure`
- `net exposure = long exposure - short exposure`
- `abs(net exposure) <= gross exposure`
- `floating PnL = unrealized PnL`
- `equity peak >= current equity`
- `used margin <= current equity`
- `required margin = notional / leverage`
- allocations over a non-empty portfolio sum to one
- weighted fill price is quantity weighted

## Position accounting

EPIP uses average-cost accounting. Same-direction fills update the basis with a
quantity-weighted mean. Partial closes leave that basis unchanged and realize PnL only on the
closed quantity. A complete close removes the position. A direction reversal first realizes the
closed quantity and then opens the residual quantity at the reversal fill price.

## Execution charges and fills

- Fixed commission: configured monetary amount per generated fill.
- Percentage commission: decimal rate times normalized fill notional.
- Per-lot commission: configured monetary amount times normalized fill quantity.
- Fill commissions are applied at fill creation and aggregated over the order.
- Execution average price is weighted by fill quantity.
- Duplicate fill identifiers and aggregate overfills are rejected.

## Explicit boundaries

The current framework is mono-currency and assumes all values are already normalized into a
common monetary unit. It has no FX conversion, settlement or cash ledger, instrument
specification, corporate-action processing, trading calendar, or mark-to-market price provider.
Margin is the simplified identity `notional / leverage`; it is not broker-specific settlement
margin. Named correlation groups are allocation labels and are not statistical correlation.

Because no period ledger exists, daily, weekly, and monthly PnL are unavailable (`None`). Realized
PnL remains cumulative and is exposed only through the `realized` field.

All accepted financial values must be finite. Float remains appropriate for dimensionless scores,
ratios, market prices, and deterministic research calculations. It is not yet approved for final
broker cash settlement without instrument-specific decimal quantization.
