from epip.core.types import FRAMEWORK_NAME, Direction, Price


def test_framework_metadata_and_type_aliases() -> None:
    assert FRAMEWORK_NAME == "EPIP"
    assert Direction.BUY.value == "BUY"
    assert Price is float
