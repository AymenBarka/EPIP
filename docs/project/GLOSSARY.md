# Glossary

- **Swing:** a directional price movement between confirmed pivots.
- **SwingPoint:** a confirmed local high or low with price, time, classification, and scope.
- **SwingSequence:** an ordered immutable collection of swing points used by structural analysis.
- **BOS (Break of Structure):** continuation event where price breaks a structurally significant
  level in the prevailing direction.
- **CHOCH (Change of Character):** structural break suggesting a potential change in directional
  behavior.
- **Liquidity:** executable interest expected around price levels where orders or stops accumulate.
- **Liquidity Pool:** a bounded price area containing concentrated potential liquidity.
- **Liquidity Sweep:** price trading through a liquidity level and taking available orders, often
  followed by a reaction.
- **Liquidity Void:** an imbalanced area traversed with little opposing activity.
- **Fair Value Gap (FVG):** a multi-candle price imbalance leaving a range with limited overlap.
- **Market Structure:** the classified relationship between swings, trends, breaks, and ranges.
- **Premium:** the upper portion of a reference dealing range, commonly above equilibrium.
- **Discount:** the lower portion of a reference dealing range, commonly below equilibrium.
- **OTE (Optimal Trade Entry):** a configured Fibonacci retracement region used as confluence for a
  potential entry.
- **Golden Zone:** a configured cluster of Fibonacci ratios considered structurally significant.
- **Market Context:** the immutable aggregate of official structure, liquidity, Fibonacci, phase,
  bias, and confluence information for a stream.
- **Wave Degree:** the hierarchical scale assigned to an Elliott wave count.
- **Impulse:** a directional Elliott wave pattern progressing with the larger-degree trend.
- **Correction:** a counter-trend or consolidating Elliott pattern that modifies an impulse.
- **TradeDecision:** the Decision Engine's official immutable trading intent, including action,
  scores, reasoning, priority, and suggested zones.
- **PositionPlan:** the Risk Engine's official immutable sizing and risk-management output consumed
  by Execution.
- **ExecutionSnapshot:** the official immutable point-in-time result of order execution, containing
  its report, order lifecycle, fills, costs, and source PositionPlan link.
- **Snapshot:** a versioned immutable representation of one engine's state or output at a timestamp.
- **History:** an immutable append-only sequence of versioned snapshots supporting lookup and replay.
- **Graph:** immutable nodes and typed edges preserving sequence, hierarchy, and upstream lineage.
- **EventBus:** the deterministic thread-safe in-process publisher/subscriber used for domain events.
- **Version:** a monotonic or schema identifier that makes output evolution and compatibility
  explicit.
- **Serialization:** deterministic conversion between typed domain objects and dictionary/JSON
  representations.
- **Confluence:** agreement among independent official signals, represented by a bounded score or
  structured evidence.
- **Risk Profile:** configuration or decision metadata describing risk tolerance, maximum risk, and
  reward/risk requirements.
- **Execution Priority:** the ranked urgency assigned by Decision to a possible action.
- **Position Size:** quantity and notional exposure assigned to a trade under a sizing method.
- **Margin:** capital required or reserved by a broker to support leveraged exposure.
- **Leverage:** ratio of position notional to supporting account equity or margin.
- **Drawdown:** decline from a reference equity peak, tracked over defined periods or portfolios.
- **Exposure:** capital or risk sensitivity allocated to a symbol, correlation group, direction, or
  total portfolio.
- **Kelly Criterion:** probability-and-payoff sizing formula that estimates the growth-optimal
  fraction; EPIP also supports fractional Kelly to reduce aggressiveness.
- **Paper Trading:** simulated order execution without transmitting orders to a live broker.
- **Broker Adapter:** protocol implementation translating EPIP orders to an external or simulated
  broker while isolating vendor dependencies.
- **State Machine:** explicit set of states and validated transitions governing a domain lifecycle,
  such as order creation through fill, rejection, cancellation, or expiry.
