from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Member, Trip, User
from app.schemas import TripCreate, TripJoin, TripResponse
from app.services.invite_codes import generate_invite_code

router = APIRouter(prefix="/trips", tags=["trips"])
MAX_INVITE_CODE_ATTEMPTS = 5


def find_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


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


def find_trip_by_invite_code(db: Session, invite_code: str) -> Trip | None:
    return db.query(Trip).filter(Trip.invite_code == invite_code.upper()).first()


def find_existing_member(db: Session, trip: Trip, user: User) -> Member | None:
    return db.query(Member).filter(Member.trip_id == trip.id, Member.user_id == user.id).first()


def reject_duplicate_member_name(db: Session, trip: Trip, user: User) -> None:
    existing_name_member = db.query(Member).filter(Member.trip_id == trip.id, Member.name == user.username).first()
    if existing_name_member is not None:
        raise HTTPException(status_code=409, detail="username already exists in this trip")


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
