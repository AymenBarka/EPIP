# Changelog

## EPIP-015

### Added

- Portfolio Engine
- Portfolio Snapshot
- Portfolio State
- Multi-Position Management
- Global Long / Short Exposure
- Net / Gross Exposure
- Capital Allocation
- Cash and Margin Management
- Portfolio PnL and Equity
- Drawdown Management
- Correlation Groups
- Risk Limits and Concentration
- Portfolio Rebalancing
- Immutable History and Graph
- Portfolio Events
- Deterministic Serialization

### Tests

- Portfolio Engine
- Position Lifecycle
- Exposure and Allocation
- Capital and Margin
- PnL and Equity
- Risk Limits
- Rebalancing
- History and Graph
- Serialization

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 97%

## EPIP-014

### Added

- Execution Engine
- ExecutionSnapshot
- Order Manager
- Fill Manager
- Broker Adapter Protocol
- Paper Trading Adapter
- MT5 Adapter Stub
- Order State Machine
- Retry Manager
- Slippage Manager
- Commission Manager
- Execution History
- Execution Graph
- Execution Events
- Deterministic Serialization

### Tests

- Order Lifecycle
- State Machine
- Paper Adapter
- Broker Adapter Protocol
- Retry
- Slippage
- Commission
- Serialization
- History
- Graph
- PositionPlan Integration
- Illegal State Transitions

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 97%

## EPIP-013

### Added

- Risk Engine
- PositionPlan
- Position Sizing Engine
- Fixed Risk Sizing
- Fixed Amount Sizing
- Kelly Criterion
- Fractional Kelly
- ATR Position Sizing
- Volatility Position Sizing
- Exposure Management
- Drawdown Management
- Margin Calculation
- Leverage Calculation
- Portfolio Limits
- Stop Loss Management
- Take Profit Management
- Position Graph
- Position History
- Risk Events
- Deterministic Serialization

### Tests

- Position Sizing
- Kelly
- ATR Sizing
- Volatility Sizing
- Exposure
- Drawdown
- Margin
- Leverage
- Stop Management
- Take Profit
- Serialization
- History
- Graph
- Decision Integration

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 96%

## EPIP-008

### Added

- Liquidity Engine
- Liquidity Pools
- Liquidity Sweeps
- Equal High Detection
- Equal Low Detection
- Internal Liquidity
- External Liquidity
- Liquidity Graph
- Liquidity History
- Liquidity State Machine
- Liquidity Strength
- Liquidity Ranking
- Fair Value Gap domain
- Liquidity Void domain
- Liquidity Cluster
- Multi-TimeFrame Liquidity Tree
- Confluence Score
- Deterministic Serialization

### Tests

- Engine
- Pools
- Sweeps
- Equal Levels
- History
- Graph
- State Machine
- Hardening

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 95%

## EPIP-007

### Added

- Market Structure Engine
- Structure State Machine
- BOS Detector
- CHOCH Detector
- Trend Detector
- Range Detector
- StructureGraph
- StructureHistory
- Serialization
- Observer support
- Versioning
- Domain metadata
- Deterministic snapshots

### Tests

- Engine tests
- Detector tests
- State machine tests
- Observer tests
- Serialization tests
- Benchmark tests

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 95%

## EPIP-006

### Added

- Swing Detection Engine
- Pivot Window Strategy
- Swing Models
- Swing Validators
- Swing Filters
- Swing Events
- Swing Statistics
- Swing Metrics

### Tests

- Swing Engine tests
- Strategy tests
- Filters tests
- Validator tests

### Quality

- Black OK
- Ruff OK
- MyPy OK
- Pytest OK
- Coverage >=95%

## EPIP-005

### Added

- Replay Engine
- Replay Scheduler
- Replay Iterator
- Replay Clock
- Replay Session
- Replay Statistics
- Replay Metrics
- Replay Controller
- Replay Events
- Replay Config

### Tests

- Replay Engine tests
- Replay Scheduler tests
- Replay Iterator tests
- Replay Session tests

### Quality

- Black OK
- Ruff OK
- MyPy OK
- Pytest OK
- Coverage 96%

## EPIP-004

### Added

- Market Data Layer
- DataSource Protocol
- DataSource Factory
- Registry
- Cache
- CSV Provider
- Fake Provider
- TwelveData Adapter
- MT5 Adapter

### Tests

- Provider tests
- Cache tests
- Registry tests

### Quality

- Black OK
- Ruff OK
- MyPy OK
- Pytest OK
- Coverage 96%

## EPIP-003

### Added

- Feature
- FeatureSet
- FeatureStore
- FeatureRegistry
- FeaturePipeline
- OHLC Provider
- Provider Interfaces

### Tests

- Feature tests
- Pipeline tests
- Store tests

### Quality

- Black OK
- Ruff OK
- MyPy OK
- Pytest OK
- Coverage 95%

## EPIP-002

### Added

- EventBus
- Plugin Registry
- Kernel
- Plugin Protocol
- Plugin Context
- Plugin Result

### Tests

- Runtime tests
- EventBus tests
- Kernel tests

### Quality

- Black OK
- Ruff OK
- MyPy OK
- Pytest OK
- Coverage 96%
## EPIP-009

### Added

- Fibonacci Engine
- Fibonacci Levels
- Retracements
- Extensions
- Premium / Discount
- OTE
- Golden Zone
- Confluence
- Fibonacci Graph
- Fibonacci History
- Fibonacci Strength
- Fibonacci Cluster
- Institutional Entry Zone
- Projection Targets
- Multi-TimeFrame Alignment
- Probability Score
- Deterministic Serialization

### Tests

- Engine
- Retracements
- Extensions
- OTE
- Premium / Discount
- Confluence
- Graph
- History
- Hardening

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 95%
## EPIP-010

### Added

- Market Context Engine
- Market Context Snapshot
- Market Context Builder
- Market Context Aggregator
- Market Context Graph
- Market Context History
- Market Phase
- Institutional Bias
- Confluence Context
- Immutable Snapshots
- Deterministic Serialization
- Versioned Context
- EventBus Integration

### Tests

- Engine
- Builder
- Aggregator
- Snapshot
- Graph
- History
- Serialization
- Confluence
- Phase
- Bias

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 96%
## EPIP-011

### Added

- Elliott Wave Engine
- Wave Detection
- Wave Validation
- Wave Counter
- Alternate Wave Counter
- Wave Degrees
- Wave Rules
- Wave Projections
- Wave Targets
- Wave Graph
- Wave History
- Wave Serialization
- Elliott Events
- Confidence / Probability / Quality scoring
- Market Context integration

### Tests

- Engine
- Wave Rules
- Alternate Counts
- Degrees
- Projections
- Serialization
- History
- Graph
- Market Context integration

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 96%
## EPIP-012

### Added

- Decision Engine
- TradeDecision
- Decision Snapshot
- Decision Graph
- Decision History
- Rule Engine
- Decision Matrix
- Decision Scoring
- Confidence
- Probability
- Execution Priority
- Decision Quality
- Risk Profile
- Entry / Exit Suggestions
- Decision Events
- Deterministic Serialization

### Tests

- Decision Engine
- Rule Engine
- Decision Matrix
- Decision Scoring
- Confidence
- Probability
- Priority
- Risk Profile
- Serialization
- History
- Graph
- Market Context Integration
- Elliott Integration

### Quality

- Black PASS
- Ruff PASS
- MyPy PASS
- Pytest PASS
- Coverage 96%
