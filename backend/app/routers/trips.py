from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Expense, Member, RealtimeEvent, Trip, User
from app.schemas import (
    ChangesResponse,
    ExpenseResponse,
    RealtimeEventResponse,
    SettlementMemberResponse,
    SettlementResponse,
    SettlementTransferResponse,
    TripCreate,
    TripDetailResponse,
    TripJoin,
    TripResponse,
)
from app.services.invite_codes import generate_invite_code
from app.services.settlements import ExpenseInput, MemberInput, calculate_settlement

router = APIRouter(prefix="/trips", tags=["trips"])
MAX_INVITE_CODE_ATTEMPTS = 5


def find_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


def find_trip(db: Session, trip_id: str) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    return trip


def serialize_trip(trip: Trip) -> TripResponse:
    active_members = [member for member in trip.members if member.status == "active"]
    active_members.sort(key=lambda member: member.joined_at)
    return TripResponse.model_validate({
        "id": trip.id,
        "name": trip.name,
        "invite_code": trip.invite_code,
        "currency_code": trip.currency_code,
        "status": trip.status,
        "version": trip.version,
        "members": active_members,
        "created_at": trip.created_at,
        "updated_at": trip.updated_at,
    })


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


def serialize_trip_detail(db: Session, trip: Trip) -> TripDetailResponse:
    trip_response = serialize_trip(trip)
    expenses = sorted(trip.expenses, key=lambda expense: expense.spent_at, reverse=True)
    return TripDetailResponse(
        **trip_response.model_dump(),
        expenses=[to_expense_response(db, expense) for expense in expenses],
    )


def format_money(value) -> str:
    return f"{value:.2f}"


def find_trip_by_invite_code(db: Session, invite_code: str) -> Trip | None:
    return db.query(Trip).filter(Trip.invite_code == invite_code.upper()).first()


def find_existing_member(db: Session, trip: Trip, user: User) -> Member | None:
    return db.query(Member).filter(Member.trip_id == trip.id, Member.user_id == user.id).first()


def reject_duplicate_member_name(db: Session, trip: Trip, user: User) -> None:
    existing_name_member = db.query(Member).filter(Member.trip_id == trip.id, Member.name == user.username).first()
    if existing_name_member is not None:
        raise HTTPException(status_code=409, detail="username already exists in this trip")


@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip(trip_id: str, db: Session = Depends(get_db)) -> TripDetailResponse:
    trip = find_trip(db, trip_id)
    return serialize_trip_detail(db, trip)


@router.get("/{trip_id}/settlement", response_model=SettlementResponse)
def get_settlement(trip_id: str, db: Session = Depends(get_db)) -> SettlementResponse:
    trip = find_trip(db, trip_id)
    active_members = [member for member in trip.members if member.status == "active"]
    active_members.sort(key=lambda member: member.joined_at)
    result = calculate_settlement(
        members=[MemberInput(id=member.id, name=member.name) for member in active_members],
        expenses=[
            ExpenseInput(amount=expense.amount, paid_by_member_id=expense.paid_by_member_id)
            for expense in trip.expenses
        ],
    )
    member_names = {member.id: member.name for member in active_members}
    members = []
    for member in active_members:
        summary = result.member_summaries[member.id]
        members.append(
            SettlementMemberResponse(
                member_id=summary.member_id,
                name=summary.name,
                paid=format_money(summary.paid),
                owed=format_money(summary.owed),
                balance=format_money(summary.balance),
            )
        )
    transfers = [
        SettlementTransferResponse(
            from_member_id=transfer.from_member_id,
            from_member_name=member_names[transfer.from_member_id],
            to_member_id=transfer.to_member_id,
            to_member_name=member_names[transfer.to_member_id],
            amount=format_money(transfer.amount),
        )
        for transfer in result.transfers
    ]
    return SettlementResponse(members=members, transfers=transfers)


@router.get("/{trip_id}/changes", response_model=ChangesResponse)
def get_changes(
    trip_id: str,
    since_version: int = 0,
    db: Session = Depends(get_db),
) -> ChangesResponse:
    trip = find_trip(db, trip_id)
    events = (
        db.query(RealtimeEvent)
        .filter(RealtimeEvent.trip_id == trip.id, RealtimeEvent.version > since_version)
        .order_by(RealtimeEvent.version.asc(), RealtimeEvent.created_at.asc())
        .all()
    )
    return ChangesResponse(
        current_version=trip.version,
        events=[
            RealtimeEventResponse(
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
                version=event.version,
                created_at=event.created_at,
            )
            for event in events
        ],
    )


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)) -> TripResponse:
    user = find_user(db, payload.created_by_user_id)
    for _ in range(MAX_INVITE_CODE_ATTEMPTS):
        invite_code = generate_invite_code()
        if db.query(Trip).filter(Trip.invite_code == invite_code).first() is not None:
            continue
        trip = Trip(name=payload.name, invite_code=invite_code, created_by_user_id=user.id)
        try:
            db.add(trip)
            db.flush()
            db.add(Member(trip_id=trip.id, user_id=user.id, name=user.username))
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(trip)
        return serialize_trip(trip)
    raise HTTPException(status_code=503, detail="could not generate invite code")


@router.post("/join", response_model=TripResponse)
def join_trip(payload: TripJoin, db: Session = Depends(get_db)) -> TripResponse:
    user = find_user(db, payload.user_id)
    trip = find_trip_by_invite_code(db, payload.invite_code)
    if trip is None:
        raise HTTPException(status_code=404, detail="invite code not found")
    if find_existing_member(db, trip, user) is not None:
        return serialize_trip(trip)
    reject_duplicate_member_name(db, trip, user)
    trip.version += 1
    db.add(Member(trip_id=trip.id, user_id=user.id, name=user.username))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        trip = find_trip_by_invite_code(db, payload.invite_code)
        if trip is None:
            raise HTTPException(status_code=404, detail="invite code not found") from None
        if find_existing_member(db, trip, user) is not None:
            return serialize_trip(trip)
        reject_duplicate_member_name(db, trip, user)
        raise HTTPException(status_code=409, detail="username already exists in this trip") from None
    db.refresh(trip)
    return serialize_trip(trip)
