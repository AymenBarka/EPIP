"""Internal transaction boundary for one Kernel pipeline execution."""

from __future__ import annotations

from enum import StrEnum

from epip.core.evidence import Evidence
from epip.core.plugin_result import PluginResult


class PipelinePhase(StrEnum):
    """Ordered phases of the internal Kernel transaction."""

    BEGIN = "begin"
    VALIDATION = "validation"
    BUILD_CONTEXT = "build_context"
    EXECUTE_PLUGIN = "execute_plugin"
    VALIDATE_RESULT = "validate_result"
    STORE_TEMP_RESULT = "store_temp_result"
    COMMIT = "commit"
    EVENTS = "events"
    COMPLETE = "complete"
    ROLLED_BACK = "rolled_back"


class KernelPipelineBusyError(RuntimeError):
    """Raised when a Kernel instance is already executing a pipeline."""


class KernelPipelineTransaction:
    """Own temporary results and events until the pipeline commits."""

    def __init__(self) -> None:
        self.phase = PipelinePhase.BEGIN
        self._plugin_results: list[PluginResult] = []
        self._evidence: list[Evidence] = []
        self._events: list[object] = []
        self._committed = False

    @property
    def plugin_results(self) -> tuple[PluginResult, ...]:
        """Return the current private result snapshot."""
        return tuple(self._plugin_results)

    @property
    def evidence(self) -> tuple[Evidence, ...]:
        """Return the current private evidence snapshot."""
        return tuple(self._evidence)

    @property
    def events(self) -> tuple[object, ...]:
        """Return the events made publishable by commit."""
        return tuple(self._events) if self._committed else ()

    def advance(self, phase: PipelinePhase) -> None:
        """Record the current formal pipeline phase."""
        self.phase = phase

    def stage_result(self, result: PluginResult) -> None:
        """Store one validated result and its evidence privately."""
        self._plugin_results.append(result)
        self._evidence.extend(result.generated_evidence)

    def stage_events(self, events: tuple[object, ...]) -> None:
        """Store isolated plugin or Kernel events privately."""
        self._events.extend(events)

    def commit(self) -> None:
        """Make staged events available to the post-commit publisher."""
        self.phase = PipelinePhase.COMMIT
        self._committed = True

    def rollback(self) -> None:
        """Discard every temporary pipeline artifact."""
        self._plugin_results.clear()
        self._evidence.clear()
        self._events.clear()
        self._committed = False
        self.phase = PipelinePhase.ROLLED_BACK

    def complete(self) -> None:
        """Mark successful post-commit event publication."""
        self.phase = PipelinePhase.COMPLETE
