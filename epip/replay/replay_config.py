"""Immutable configuration for replay sessions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReplayConfig:
    """Configuration required to build a replay session."""

    symbol: str | None = None
    symbols: tuple[str, ...] = ()
    timeframe: str | None = None
    timeframes: tuple[str, ...] = ()
    start_date: str | None = None
    end_date: str | None = None
    warmup_bars: int = 0
    replay_speed: float = 1.0
    stream_mode: str = "history"
    max_memory: int | None = None
    page_size: int = 500

    def __post_init__(self) -> None:
        normalized_symbols = self.symbols or (() if self.symbol is None else (self.symbol,))
        normalized_timeframes = self.timeframes or (
            () if self.timeframe is None else (self.timeframe,)
        )
        object.__setattr__(self, "symbols", tuple(item for item in normalized_symbols if item))
        object.__setattr__(
            self, "timeframes", tuple(item for item in normalized_timeframes if item)
        )

        if not self.symbols:
            raise ValueError("at least one symbol must be provided")
        if not self.timeframes:
            raise ValueError("at least one timeframe must be provided")
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars must be non-negative")
        if self.replay_speed <= 0:
            raise ValueError("replay_speed must be greater than zero")
        if self.page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        if self.max_memory is not None and self.max_memory <= 0:
            raise ValueError("max_memory must be greater than zero when provided")
