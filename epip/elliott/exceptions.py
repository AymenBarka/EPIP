"""EPIP-011 exceptions."""


class ElliottError(Exception):
    pass


class InvalidElliottInputError(ElliottError):
    pass


class WaveVersionError(ElliottError):
    pass
