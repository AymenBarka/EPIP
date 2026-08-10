# Exception Hierarchy

```text
EPIPError
├── FrameworkError
│   ├── ConfigurationError
│   ├── ValidationError
│   ├── RuntimeError
│   ├── ReplayError
│   ├── KernelError
│   ├── ExecutionError
│   ├── PortfolioError
│   └── RiskError
├── InfrastructureError
│   ├── ConcurrencyError
│   ├── MemoryError
│   ├── ReliabilityError
│   │   └── BoundaryViolationError
│   ├── EventBusError
│   ├── SerializationError
│   ├── TimeoutError
│   ├── CancellationError
│   └── InterruptedError
├── ExternalSystemError
│   ├── ProviderError
│   └── AdapterError
├── PluginError
├── RetryableError
├── NonRetryableError
├── FatalError
└── RecoverableError
```

The hierarchy uses single inheritance exclusively. The registry validates one
direct parent per canonical exception; the abstract hierarchy auditor detects
cycles and missing parents in machine-readable declarations.
