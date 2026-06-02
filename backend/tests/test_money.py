from decimal import Decimal

import pytest

from app.services.money import normalize_amount


def test_normalize_amount_accepts_two_decimals():
    assert normalize_amount("128.50") == Decimal("128.50")


def test_normalize_amount_rounds_to_two_decimals():
    assert normalize_amount("10.005") == Decimal("10.01")


def test_normalize_amount_rejects_zero():
    with pytest.raises(ValueError):
        normalize_amount("0")


def test_normalize_amount_rejects_negative():
    with pytest.raises(ValueError):
        normalize_amount("-1.00")
