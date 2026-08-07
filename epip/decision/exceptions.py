"""EPIP-012 exceptions."""


class DecisionError(Exception):
    pass


class InvalidDecisionInputError(DecisionError):
    pass


class DecisionVersionError(DecisionError):
    pass
