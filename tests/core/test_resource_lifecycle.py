"""Tests for the official H005 resource lifecycle infrastructure."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epip.core.resource_lifecycle import (
    InvalidLifecycleTransitionError,
    LifecycleManager,
    LifecycleState,
    ResourceCleanupError,
    ResourceClosedError,
    ResourceHandle,
    ResourceOwnership,
    ResourceOwnershipError,
    resource_managed_components,
)


class _Resource:
    def __init__(self, *, fail_closes: int = 0) -> None:
        self.close_count = 0
        self.fail_closes = fail_closes

    def close(self) -> None:
        self.close_count += 1
        if self.close_count <= self.fail_closes:
            raise RuntimeError("cleanup failed")


def test_nominal_lifecycle_and_immutable_snapshot() -> None:
    resource = _Resource()
    handle = ResourceHandle(resource, name="provider", owner_id="kernel")

    handle.initialize()
    handle.activate()
    assert handle.use() is resource
    handle.idle()
    snapshot = handle.lifecycle
    assert snapshot.state is LifecycleState.IDLE
    with pytest.raises(FrozenInstanceError):
        snapshot.owner_id = "other"  # type: ignore[misc]
    handle.close()

    closed_state: LifecycleState = handle.state
    assert closed_state == LifecycleState.CLOSED
    assert resource.close_count == 1


def test_invalid_transitions_and_use_before_initialization_are_audited() -> None:
    handle = ResourceHandle(_Resource(), name="cache", owner_id="store")

    with pytest.raises(InvalidLifecycleTransitionError):
        handle.activate()
    with pytest.raises(InvalidLifecycleTransitionError):
        handle.use()

    assert handle.audit_counters() == (0, 0, 2, 0)


def test_close_is_idempotent_and_use_after_close_is_rejected() -> None:
    resource = _Resource()
    handle = ResourceHandle(resource, name="adapter", owner_id="execution")
    handle.initialize()
    handle.close()
    handle.close()

    with pytest.raises(ResourceClosedError):
        handle.use()

    assert resource.close_count == 1
    assert handle.audit_counters() == (1, 1, 0, 0)


def test_failed_cleanup_has_coherent_state_and_can_be_retried() -> None:
    resource = _Resource(fail_closes=1)
    handle = ResourceHandle(resource, name="session", owner_id="replay")

    with pytest.raises(ResourceCleanupError):
        handle.close()
    assert handle.state is LifecycleState.FAILED

    handle.close()
    assert handle.lifecycle.state.value == "closed"
    assert resource.close_count == 2


def test_context_manager_guarantees_cleanup_after_exception() -> None:
    resource = _Resource()
    handle = ResourceHandle(resource, name="provider", owner_id="market-data")

    with pytest.raises(ValueError, match="operation failed"), handle as managed:
        assert managed is resource
        raise ValueError("operation failed")

    assert handle.state is LifecycleState.CLOSED
    assert resource.close_count == 1


def test_ownership_transfer_is_explicit_and_borrower_cannot_close() -> None:
    owner = ResourceHandle(_Resource(), name="owned", owner_id="first")
    owner.transfer_ownership("second")
    assert owner.lifecycle.ownership is ResourceOwnership.TRANSFERRED_OWNER
    assert owner.owner_id == "second"

    borrower = ResourceHandle(
        _Resource(),
        name="borrowed",
        owner_id="external",
        ownership=ResourceOwnership.BORROWER,
    )
    with pytest.raises(ResourceOwnershipError):
        borrower.close()
    with pytest.raises(ResourceOwnershipError):
        borrower.transfer_ownership("other")
    assert borrower.audit_counters() == (0, 0, 0, 2)


def test_manager_closes_every_resource_even_when_one_cleanup_fails() -> None:
    good = _Resource()
    failing = _Resource(fail_closes=1)
    manager = LifecycleManager("kernel")
    manager.acquire("a-failing", failing)
    manager.acquire("b-good", good)

    with pytest.raises(ResourceCleanupError):
        manager.close_all()

    assert failing.close_count == 1
    assert good.close_count == 1
    assert manager["a-failing"].state is LifecycleState.FAILED
    assert manager["b-good"].state is LifecycleState.CLOSED


def test_manager_audit_detects_abandoned_and_never_closed_resources() -> None:
    manager = LifecycleManager("kernel")
    abandoned = manager.acquire("abandoned", _Resource())
    manager.acquire("active", _Resource())
    abandoned.abort()

    audit = manager.audit()
    assert audit.abandoned == ("abandoned",)
    assert audit.never_closed == ("abandoned", "active")
    with pytest.raises(TypeError):
        audit.double_close_attempts["active"] = 1  # type: ignore[index]


def test_manager_context_closes_registered_resources() -> None:
    resource = _Resource()
    with LifecycleManager("execution") as manager:
        manager.acquire("adapter", resource)

    assert manager["adapter"].state is LifecycleState.CLOSED
    assert manager.audit().never_closed == ()


def test_resource_managed_contracts_are_discoverable() -> None:
    components = resource_managed_components()
    assert components == tuple(sorted(components))
    assert "epip.marketdata.providers.mt5_provider.MT5Provider" in components
    assert "epip.marketdata.providers.twelvedata_provider.TwelveDataProvider" in components
    assert "epip.execution.mt5_adapter.MT5Adapter" in components
