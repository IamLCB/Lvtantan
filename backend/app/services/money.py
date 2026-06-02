from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal("0.01")


def normalize_amount(raw: str) -> Decimal:
    try:
        parsed = Decimal(raw)
        if not parsed.is_finite():
            raise ValueError("amount must be a decimal string")
        amount = parsed.quantize(CENTS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be a decimal string") from exc
    if amount <= 0:
        raise ValueError("amount must be positive")
    return amount
