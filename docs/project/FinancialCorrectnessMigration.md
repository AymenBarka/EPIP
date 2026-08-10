# Financial Correctness Migration

Hardening-003 preserves public signatures. Existing callers must stop constructing inconsistent
`PortfolioExposure`, `PortfolioPnL`, or `PortfolioEquity` objects; these now fail immediately with
`RelationshipIntegrityError`. Zero-notional margin now returns a finite safety ratio of `1.0`
instead of an unusable infinity.

`PortfolioPnL.daily`, `weekly`, and `monthly` now return `None` when produced by the Portfolio
Engine. Their annotations accept `float | None`, so previously serialized numeric values remain
readable. Consumers must treat `None` as "period attribution unavailable" and must use `realized`
for cumulative realized PnL. No numeric zero should be inferred from unavailable periodic data.

Average-cost behavior and commission formulas are unchanged, but are now the formally documented
and regression-tested policies. Inputs remain mono-currency, normalized values. Applications that
require decimal settlement, broker-specific margin, trading-calendar attribution, currency
conversion, or statistical correlation must provide those capabilities outside the current EPIP
contract until their dedicated modules are introduced.
