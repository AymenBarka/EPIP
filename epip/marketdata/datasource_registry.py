"""Thread-safe registry for market data providers."""

from __future__ import annotations

from threading import RLock

from epip.marketdata.datasource_protocol import DataSourceProtocol


class DataSourceRegistry:
    """Provider registry with default-provider support."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._providers: dict[str, DataSourceProtocol] = {}
        self._default_name: str | None = None

    def register(
        self, name: str, provider: DataSourceProtocol, *, as_default: bool = False
    ) -> None:
        with self._lock:
            self._providers[name] = provider
            if as_default or self._default_name is None:
                self._default_name = name

    def unregister(self, name: str) -> None:
        with self._lock:
            self._providers.pop(name, None)
            if self._default_name == name:
                self._default_name = next(iter(self._providers), None)

    def exists(self, name: str) -> bool:
        with self._lock:
            return name in self._providers

    def default(self) -> DataSourceProtocol | None:
        with self._lock:
            if self._default_name is None:
                return None
            return self._providers.get(self._default_name)

    def providers(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._providers.keys())
