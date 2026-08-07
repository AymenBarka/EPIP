"""Portfolio domain exceptions."""


class PortfolioError(Exception):
    """Base portfolio error."""


class InvalidPortfolioInputError(PortfolioError):
    """Raised for invalid execution input or configuration."""


class PortfolioVersionError(PortfolioError):
    """Raised for non-sequential history versions."""
