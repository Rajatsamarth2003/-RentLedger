from services.calculator import calculate_bill


def test_bill_calculation():
    result = calculate_bill(4700, 12, 59)

    assert result["electricity"] == 708
    assert result["total"] == 5408
