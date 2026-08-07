"""Risk domain exceptions."""


class RiskError(Exception):
    """Base risk error."""


class InvalidRiskInputError(RiskError):
    """Raised for invalid planning input."""


class RiskVersionError(RiskError):
    """Raised for non-sequential history."""


class RiskConstraintError(RiskError):
    """Raised when a risk constraint cannot be evaluated."""
