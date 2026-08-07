"""EPIP-010 Market Context exceptions."""


class MarketContextError(Exception):
    pass


class InvalidMarketContextInputError(MarketContextError):
    pass


class MarketContextVersionError(MarketContextError):
    pass
