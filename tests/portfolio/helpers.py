from epip.execution.models import (
    ExecutionReason,
    ExecutionReport,
    ExecutionSnapshot,
    Order,
    OrderFill,
    OrderSide,
    OrderState,
    OrderType,
)


def execution(
    *,
    symbol: str = "EURUSD",
    side: OrderSide = OrderSide.LONG,
    quantity: float = 10,
    price: float = 100,
    version: int = 1,
    commission: float = 1,
    completed: bool = True,
) -> ExecutionSnapshot:
    fill = OrderFill(f"fill-{version}", quantity, price, commission, f"t{version}")
    order = Order(
        f"o-{version}",
        f"p-{version}",
        symbol,
        side,
        OrderType.MARKET,
        quantity,
        price,
        None,
        None,
        OrderState.FILLED if completed else OrderState.REJECTED,
        (fill,) if completed else (),
    )
    report = ExecutionReport(
        order,
        quantity,
        quantity if completed else 0,
        price if completed else None,
        0,
        commission if completed else 0,
        completed,
        (ExecutionReason("OK", "filled", completed),),
    )
    return ExecutionSnapshot(f"t{version}", symbol, version, f"p-{version}", report)
