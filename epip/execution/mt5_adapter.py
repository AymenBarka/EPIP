"""Dependency-free MT5 adapter placeholder."""

from epip.execution.exceptions import BrokerUnavailableError
from epip.execution.models import BrokerResponse, Order


class MT5Adapter:
    def submit(self, order: Order) -> BrokerResponse:
        raise BrokerUnavailableError("MT5 adapter is a stub; no MT5 dependency is installed")

    def cancel(self, order: Order) -> BrokerResponse:
        raise BrokerUnavailableError("MT5 adapter is a stub; no MT5 dependency is installed")
