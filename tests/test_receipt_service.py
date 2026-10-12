from src.receipt_service import Payment, make_receipt


def test_receipt_records_amount_and_tenant() -> None:
    receipt = make_receipt(
        Payment("Maya Chen", "18 Willow Lane", 185000, "2026-09-01", "pay-123")
    )

    assert receipt.payment_id == "pay-123"
    assert "Maya Chen" in receipt.markdown
    assert "$1,850.00" in receipt.markdown


def test_receipt_rejects_non_positive_amount() -> None:
    try:
        make_receipt(Payment("Maya Chen", "18 Willow Lane", 0, "2026-09-01", "pay-123"))
    except ValueError as error:
        assert str(error) == "amount_cents must be positive"
    else:
        raise AssertionError("expected a positive payment amount")
