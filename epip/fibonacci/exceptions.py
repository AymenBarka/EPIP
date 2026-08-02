"""Fibonacci domain errors."""


class FibonacciError(Exception):
    pass


class InvalidFibonacciInputError(FibonacciError):
    pass


class FibonacciVersionError(FibonacciError):
    pass
