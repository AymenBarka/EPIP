"""Core domain exports for EPIP."""

from epip.core.candle import Candle
from epip.core.context import MarketContext
from epip.core.contracts import DecisionConsumer, EvidenceProducer, ScenarioBuilder
from epip.core.decision import Decision
from epip.core.event_bus import EventBus
from epip.core.events import (
    BaseEvent,
    DecisionCreated,
    DecisionRejected,
    EvidenceCreated,
    EvidenceRejected,
    ScenarioCreated,
    ScenarioRejected,
)
from epip.core.evidence import Evidence
from epip.core.hypothesis import Hypothesis
from epip.core.identity import (
    ClockProtocol,
    DeterministicClock,
    DeterministicIdGenerator,
    IdGeneratorProtocol,
    SystemClock,
    SystemIdGenerator,
)
from epip.core.integrity import (
    DataIntegrityError,
    EventIntegrityError,
    IntegrityContractError,
    IntegrityValidatable,
    MissingFieldError,
    NumericIntegrityError,
    RelationshipIntegrityError,
    SerializationIntegrityError,
    VersionIntegrityError,
)
from epip.core.kernel import Kernel, KernelResult
from epip.core.plugin_context import PluginContext
from epip.core.plugin_protocol import PluginProtocol
from epip.core.plugin_result import PluginResult
from epip.core.registry import Registry
from epip.core.scenario import Scenario
from epip.core.value_objects import Confidence, Price, Probability, RiskScore

__all__ = [
    "BaseEvent",
    "Candle",
    "ClockProtocol",
    "Confidence",
    "DataIntegrityError",
    "Decision",
    "DecisionConsumer",
    "DecisionCreated",
    "DecisionRejected",
    "DeterministicClock",
    "DeterministicIdGenerator",
    "EventBus",
    "EventIntegrityError",
    "Evidence",
    "EvidenceCreated",
    "EvidenceProducer",
    "EvidenceRejected",
    "Hypothesis",
    "IdGeneratorProtocol",
    "IntegrityContractError",
    "IntegrityValidatable",
    "Kernel",
    "KernelResult",
    "MarketContext",
    "MissingFieldError",
    "NumericIntegrityError",
    "PluginContext",
    "PluginProtocol",
    "PluginResult",
    "Price",
    "Probability",
    "Registry",
    "RelationshipIntegrityError",
    "RiskScore",
    "Scenario",
    "ScenarioBuilder",
    "ScenarioCreated",
    "ScenarioRejected",
    "SerializationIntegrityError",
    "SystemClock",
    "SystemIdGenerator",
    "VersionIntegrityError",
]
