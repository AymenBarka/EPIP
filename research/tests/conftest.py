"""Research test configuration: the network is forbidden for every test."""

from __future__ import annotations

import socket
from collections.abc import Iterator

import pytest


class NetworkForbiddenError(RuntimeError):
    pass


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise NetworkForbiddenError("research tests must not use the network")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(socket.socket, "connect", _forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", _forbidden)
    yield
