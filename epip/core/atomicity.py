"""Internal in-memory transaction primitive for engine state replacement."""

from __future__ import annotations

from typing import Any


class EngineTransaction:
    """Stage engine attributes and replace them as one guarded commit.

    Calculations and immutable aggregate construction happen before ``commit``.
    The rollback path is defensive: ordinary engine attributes do not define
    fallible setters, but restoring the prior references keeps the boundary
    atomic if a future implementation introduces one.
    """

    __slots__ = ("_owner", "_staged")

    def __init__(self, owner: object) -> None:
        self._owner = owner
        self._staged: dict[str, Any] = {}

    def stage(self, attribute: str, value: Any) -> None:
        """Stage one complete replacement without mutating the owner."""
        self._staged[attribute] = value

    def commit(self) -> None:
        """Replace every staged reference, restoring all old values on failure."""
        previous = {name: getattr(self._owner, name) for name in self._staged}
        try:
            for name, value in self._staged.items():
                setattr(self._owner, name, value)
        except BaseException:
            for name, value in previous.items():
                setattr(self._owner, name, value)
            raise
