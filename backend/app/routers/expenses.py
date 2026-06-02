from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Expense, Member, RealtimeEvent, Trip, utc_now
from app.schemas import ExpenseCreate, ExpenseDelete, ExpenseResponse
from app.services.money import normalize_amount

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["expenses"])


def find_trip(db: Session, trip_id: str) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    return trip


def find_member(db: Session, trip_id: str, user_id: str) -> Member:
    member = (
        db.query(Member)
        .filter(Member.trip_id == trip_id, Member.user_id == user_id, Member.status == "active")
        .first()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    return member


def get_or_create_category(db: Session, category_name: str) -> Category:
    category = db.query(Category).filter(Category.name == category_name).first()
    if category is not None:
        return category
    category = Category(name=category_name)
    db.add(category)
    db.flush()
    return category


def to_expense_response(db: Session, expense: Expense) -> ExpenseResponse:
    category = db.get(Category, expense.category_id)
    return ExpenseResponse(
        id=expense.id,
        trip_id=expense.trip_id,
        amount=f"{expense.amount:.2f}",
        expression_text=expense.expression_text,
        created_by_member_id=expense.created_by_member_id,
        paid_by_member_id=expense.paid_by_member_id,
        category_name=category.name if category is not None else "",
        spent_at=expense.spent_at,
        note=expense.note,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


def record_event(db: Session, trip: Trip, expense: Expense, action: str) -> None:
    db.add(
        RealtimeEvent(
            trip_id=trip.id,
            entity_type="expense",
            entity_id=expense.id,
            action=action,
            version=trip.version,
        )
    )


def find_expense(db: Session, trip_id: str, expense_id: str) -> Expense:
    expense = db.query(Expense).filter(Expense.trip_id == trip_id, Expense.id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="expense not found")
    return expense


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    trip_id: str,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    trip = find_trip(db, trip_id)
    member = find_member(db, trip.id, payload.user_id)
    category = get_or_create_category(db, payload.category_name)
    try:
        amount = normalize_amount(payload.amount)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    expense = Expense(
        trip_id=trip.id,
        amount=amount,
        expression_text=payload.expression_text,
        created_by_member_id=member.id,
        paid_by_member_id=member.id,
        category_id=category.id,
        spent_at=payload.spent_at,
        note=payload.note,
    )
    trip.version += 1
    trip.updated_at = utc_now()
    db.add(expense)
    db.flush()
    record_event(db, trip, expense, "created")
    db.commit()
    db.refresh(expense)
    return to_expense_response(db, expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    trip_id: str,
    expense_id: str,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    trip = find_trip(db, trip_id)
    find_member(db, trip.id, payload.user_id)
    expense = find_expense(db, trip.id, expense_id)
    category = get_or_create_category(db, payload.category_name)
    try:
        amount = normalize_amount(payload.amount)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    expense.amount = amount
    expense.expression_text = payload.expression_text
    expense.category_id = category.id
    expense.spent_at = payload.spent_at
    expense.note = payload.note
    expense.updated_at = utc_now()
    trip.version += 1
    trip.updated_at = utc_now()
    record_event(db, trip, expense, "updated")
    db.commit()
    db.refresh(expense)
    return to_expense_response(db, expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    trip_id: str,
    expense_id: str,
    payload: ExpenseDelete = Body(...),
    db: Session = Depends(get_db),
) -> Response:
    trip = find_trip(db, trip_id)
    find_member(db, trip.id, payload.user_id)
    expense = find_expense(db, trip.id, expense_id)

    trip.version += 1
    trip.updated_at = utc_now()
    record_event(db, trip, expense, "deleted")
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
