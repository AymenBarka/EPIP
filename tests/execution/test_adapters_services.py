import pytest

from epip.execution import BrokerAdapterProtocol, MT5Adapter, PaperTradingAdapter
from epip.execution.commission import calculate_commission
from epip.execution.config import ExecutionConfig
from epip.execution.exceptions import BrokerUnavailableError
from epip.execution.fill_manager import FillManager
from epip.execution.models import CommissionMode, OrderSide, OrderState, SlippageMode
from epip.execution.order_manager import OrderManager
from epip.execution.slippage import apply_slippage
from tests.execution.helpers import position_plan


def test_paper_adapter_and_protocol() -> None:
    adapter = PaperTradingAdapter(ExecutionConfig(slippage_value=0.1, commission_value=2))
    order = OrderManager().create(position_plan(), ExecutionConfig())
    response = adapter.submit(order)
    assert isinstance(adapter, BrokerAdapterProtocol) and response.accepted
    filled = FillManager().apply(order, response.fills)
    assert filled.state == OrderState.FILLED and FillManager().average_price(filled) == 100.1
    assert adapter.cancel(order).accepted


def test_mt5_stub() -> None:
    adapter = MT5Adapter()
    order = OrderManager().create(position_plan(), ExecutionConfig())
    with pytest.raises(BrokerUnavailableError):
        adapter.submit(order)
    with pytest.raises(BrokerUnavailableError):
        adapter.cancel(order)


@pytest.mark.parametrize(
    "mode,expected",
    [(CommissionMode.FIXED, 2), (CommissionMode.PERCENTAGE, 20), (CommissionMode.PER_LOT, 20)],
)
def test_commission(mode: CommissionMode, expected: float) -> None:
    assert (
        calculate_commission(mode, 2 if mode != CommissionMode.PERCENTAGE else 0.02, 10, 100)
        == expected
    )


@pytest.mark.parametrize(
    "mode,value,expected",
    [
        (SlippageMode.FIXED, 1, 101),
        (SlippageMode.PERCENTAGE, 0.01, 101),
        (SlippageMode.DYNAMIC, 0.01, 102),
    ],
)
def test_slippage(mode: SlippageMode, value: float, expected: float) -> None:
    assert apply_slippage(100, OrderSide.BUY, mode, value, volatility=1) == expected
    assert apply_slippage(100, OrderSide.SELL, mode, value, volatility=1) < 100
