# Thread Safety Matrix

## Orchestration and Core

| Component | Classification | Ownership | Scope |
| --- | --- | --- | --- |
| Kernel | Thread Compatible | Caller | One active pipeline; overlapping entry fails fast |
| Registry | Thread Safe | Shared | Shared instance |
| EventBus | Thread Safe | Shared | Shared instance |
| PluginContext | Thread Safe | Shared | Shared instance |
| PluginResult | Thread Safe | Shared | Shared instance |
| SystemClock | Thread Safe | Shared | Shared instance |
| DeterministicClock | Thread Safe | Shared | Shared instance |
| SystemIdGenerator | Thread Safe | Shared | Shared instance |
| DeterministicIdGenerator | Thread Safe | Shared | Shared instance |

Thread Safe does not mean deterministic callback completion order. Plugin metadata is safe only
when contained values satisfy their own immutability contracts.

EventBus now serializes accepted events through a FIFO dispatcher. Recursive publication is bounded
and queued; callbacks run without EventBus or source-engine locks.

## Replay and Features

| Component | Classification | Ownership | Scope |
| --- | --- | --- | --- |
| ReplayEngine | Thread Confined | Thread | Per thread |
| ReplaySession | Thread Confined | Thread | Per thread |
| ReplayScheduler | Thread Safe | Shared | Shared instance |
| ReplayClock | Thread Safe | Shared | Shared instance |
| ReplayController | Thread Compatible | Caller | Serialized instance |
| ReplayIterator | Thread Safe | Shared | Shared instance |
| FeatureStore | Thread Compatible | Caller | Serialized instance |
| DataSourceCache | Thread Safe | Shared | Shared instance |

Feature providers are stateless and classified Thread Safe. Their input payloads remain caller-owned.

## Market Data

| Component | Classification | Ownership | Scope |
| --- | --- | --- | --- |
| BaseProvider | Thread Confined | Thread | Per thread |
| CSVProvider | Thread Confined | Thread | Per thread |
| FakeProvider | Thread Confined | Thread | Per thread |
| MT5Provider | Thread Confined | Thread | Per thread |
| TwelveDataProvider | Thread Confined | Thread | Per thread |
| Execution MT5 stub | Thread Safe | Shared | Shared instance |
| Null MT5 adapter | Thread Safe | Shared | Shared instance |
| Null TwelveData adapter | Thread Safe | Shared | Shared instance |

Provider confinement includes connection lifecycle and adapter ownership.

## Domain Engines and Execution

| Component | Classification | Ownership | Scope |
| --- | --- | --- | --- |
| SwingEngine | Thread Compatible | Caller | Serialized instance |
| MarketStructureEngine | Thread Compatible | Caller | Serialized instance |
| LiquidityEngine | Thread Compatible | Caller | Serialized instance |
| FibonacciEngine | Thread Compatible | Caller | Serialized instance |
| MarketContextEngine | Thread Compatible | Caller | Serialized instance |
| ElliottWaveEngine | Thread Compatible | Caller | Serialized instance |
| DecisionEngine | Thread Compatible | Caller | Serialized instance |
| RiskEngine | Thread Compatible | Caller | Serialized instance |
| ExecutionEngine | Thread Compatible | Caller | Serialized instance |
| PortfolioEngine | Thread Compatible | Caller | Serialized instance |
| PaperTradingAdapter | Thread Safe | Shared | Shared instance |

Each stateful engine serializes its prepare/commit boundary with its existing
instance lock. Readers observe either the previous immutable aggregate or the
fully committed successor; they do not observe partially replaced history or
graph references.

## Supporting Structures

All eleven classified statistics collectors are Thread Safe with serialized writes. All nine
classified histories and all nine classified graphs are Thread Safe immutable value structures.
The machine-readable registry contains the exact qualified names and restrictions.

## External Effects

| Boundary | Classification | Required ownership |
| --- | --- | --- |
| External EventBus | Thread Safe locally | External subscriber owns effects |
| Feature providers | Thread Safe base contract | Concrete provider contract applies |
| Market-data providers | Thread Confined | One lifecycle owner |
| MT5 and TwelveData | Thread Confined | Adapter owner |
| Paper adapter | Thread Safe | Shared EPIP instance |
| Broker adapters | Thread Confined by default | Broker adapter owner |
| Filesystem and logging | Thread Compatible | Caller or handler synchronization |
| Network clients | Thread Confined by default | Adapter owner |
| System clock and identity | Thread Safe | Shared service |
| User callbacks | Non Thread Safe by default | Callback owner |

## Validation coverage

The classifications in this matrix are exercised by the Hardening-004 production stress campaign,
including 1–256 concurrent publishers, isolation, longevity, and memory-release checks.
