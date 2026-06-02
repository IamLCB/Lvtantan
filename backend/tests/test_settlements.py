from decimal import Decimal

import pytest

from app.services.settlements import ExpenseInput, MemberInput, calculate_settlement


def test_all_active_members_split_all_expenses_including_late_joiners():
    members = [
        MemberInput(id="m1", name="小王"),
        MemberInput(id="m2", name="小李"),
        MemberInput(id="m3", name="小张"),
    ]
    expenses = [
        ExpenseInput(amount=Decimal("90.00"), paid_by_member_id="m1"),
    ]

    result = calculate_settlement(members, expenses)

    assert result.member_summaries["m1"].paid == Decimal("90.00")
    assert result.member_summaries["m1"].owed == Decimal("30.00")
    assert result.member_summaries["m1"].balance == Decimal("60.00")
    assert result.member_summaries["m2"].balance == Decimal("-30.00")
    assert result.member_summaries["m3"].balance == Decimal("-30.00")
    assert [(t.from_member_id, t.to_member_id, t.amount) for t in result.transfers] == [
        ("m2", "m1", Decimal("30.00")),
        ("m3", "m1", Decimal("30.00")),
    ]


def test_rounding_preserves_total_amount():
    members = [
        MemberInput(id="m1", name="A"),
        MemberInput(id="m2", name="B"),
        MemberInput(id="m3", name="C"),
    ]
    expenses = [ExpenseInput(amount=Decimal("100.00"), paid_by_member_id="m1")]

    result = calculate_settlement(members, expenses)

    total_owed = sum(summary.owed for summary in result.member_summaries.values())
    assert total_owed == Decimal("100.00")


def test_empty_members_without_expenses_returns_empty_result():
    result = calculate_settlement([], [])

    assert result.member_summaries == {}
    assert result.transfers == []


def test_expense_paid_by_unknown_member_raises_value_error():
    members = [MemberInput(id="m1", name="A")]
    expenses = [ExpenseInput(amount=Decimal("12.00"), paid_by_member_id="missing")]

    with pytest.raises(ValueError, match="unknown paid_by_member_id"):
        calculate_settlement(members, expenses)
