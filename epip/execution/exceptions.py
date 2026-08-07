"""Execution domain exceptions."""


class ExecutionError(Exception):
    """Base execution error."""


class IllegalOrderTransitionError(ExecutionError):
    """Raised for an invalid state transition."""


class InvalidExecutionInputError(ExecutionError):
    """Raised for invalid position plans or orders."""


class ExecutionVersionError(ExecutionError):
    """Raised for non-sequential execution versions."""


class BrokerUnavailableError(ExecutionError):
    """Raised when a broker adapter is unavailable."""
