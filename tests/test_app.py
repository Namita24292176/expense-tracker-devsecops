from app import validate_expense

def test_validate_expense_valid():
    errors, exp = validate_expense("Coffee", "3.50", "2025-11-10")
    assert errors == []
    assert exp["description"] == "Coffee"
    assert exp["amount"] == 3.50
    assert exp["date"] == "2025-11-10"


def test_validate_expense_negative_amount():
    errors, _ = validate_expense("Coffee", "-5", "2025-11-10")
    assert "Amount must be positive." in errors


def test_validate_expense_bad_amount():
    errors, _ = validate_expense("Coffee", "abc", "2025-11-10")
    assert "Amount must be a number." in errors


def test_validate_expense_bad_date():
    errors, _ = validate_expense("Coffee", "3.50", "10-11-2025")
    assert "Date must be in YYYY-MM-DD format." in errors
