from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")


@dataclass(frozen=True)
class MemberInput:
    id: str
    name: str


@dataclass(frozen=True)
class ExpenseInput:
    amount: Decimal
    paid_by_member_id: str


@dataclass(frozen=True)
class MemberSummary:
    member_id: str
    name: str
    paid: Decimal
    owed: Decimal
    balance: Decimal


@dataclass(frozen=True)
class Transfer:
    from_member_id: str
    to_member_id: str
    amount: Decimal


@dataclass(frozen=True)
class SettlementResult:
    member_summaries: dict[str, MemberSummary]
    transfers: list[Transfer]


def split_amount(amount: Decimal, count: int) -> list[Decimal]:
    if count <= 0:
        raise ValueError("count must be positive")

    amount = amount.quantize(CENTS, rounding=ROUND_HALF_UP)
    base_share = (amount / count).quantize(CENTS, rounding=ROUND_HALF_UP)
    shares = [base_share for _ in range(count)]

    difference = (amount - sum(shares)).quantize(CENTS, rounding=ROUND_HALF_UP)
    cents_to_adjust = int(difference / CENTS)
    adjustment = CENTS if cents_to_adjust > 0 else -CENTS

    for index in range(abs(cents_to_adjust)):
        shares[index] += adjustment

    return shares


def calculate_settlement(
    members: list[MemberInput], expenses: list[ExpenseInput]
) -> SettlementResult:
    if not members:
        if expenses:
            raise ValueError("cannot calculate settlement with expenses and no members")
        return SettlementResult(member_summaries={}, transfers=[])

    member_ids = {member.id for member in members}
    paid_by_member_id = {member.id: Decimal("0.00") for member in members}
    owed_by_member_id = {member.id: Decimal("0.00") for member in members}

    for expense in expenses:
        if expense.paid_by_member_id not in member_ids:
            raise ValueError(f"unknown paid_by_member_id: {expense.paid_by_member_id}")

        amount = expense.amount.quantize(CENTS, rounding=ROUND_HALF_UP)
        paid_by_member_id[expense.paid_by_member_id] += amount
        shares = split_amount(amount, len(members))
        for member, share in zip(members, shares, strict=True):
            owed_by_member_id[member.id] += share

    member_summaries = {}
    debtors: list[tuple[str, Decimal]] = []
    creditors: list[tuple[str, Decimal]] = []

    for member in members:
        paid = paid_by_member_id[member.id].quantize(CENTS, rounding=ROUND_HALF_UP)
        owed = owed_by_member_id[member.id].quantize(CENTS, rounding=ROUND_HALF_UP)
        balance = (paid - owed).quantize(CENTS, rounding=ROUND_HALF_UP)
        member_summaries[member.id] = MemberSummary(
            member_id=member.id,
            name=member.name,
            paid=paid,
            owed=owed,
            balance=balance,
        )
        if balance < 0:
            debtors.append((member.id, -balance))
        elif balance > 0:
            creditors.append((member.id, balance))

    transfers = _generate_transfers(debtors, creditors)
    return SettlementResult(member_summaries=member_summaries, transfers=transfers)


def _generate_transfers(
    debtors: list[tuple[str, Decimal]], creditors: list[tuple[str, Decimal]]
) -> list[Transfer]:
    transfers = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, debt_amount = debtors[debtor_index]
        creditor_id, credit_amount = creditors[creditor_index]
        amount = min(debt_amount, credit_amount).quantize(CENTS, rounding=ROUND_HALF_UP)

        if amount > 0:
            transfers.append(
                Transfer(
                    from_member_id=debtor_id,
                    to_member_id=creditor_id,
                    amount=amount,
                )
            )

        debt_amount = (debt_amount - amount).quantize(CENTS, rounding=ROUND_HALF_UP)
        credit_amount = (credit_amount - amount).quantize(CENTS, rounding=ROUND_HALF_UP)

        if debt_amount == 0:
            debtor_index += 1
        else:
            debtors[debtor_index] = (debtor_id, debt_amount)

        if credit_amount == 0:
            creditor_index += 1
        else:
            creditors[creditor_index] = (creditor_id, credit_amount)

    return transfers
