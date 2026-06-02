from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Member, Trip, User
from app.schemas import TripCreate, TripJoin, TripResponse
from app.services.invite_codes import generate_invite_code

router = APIRouter(prefix="/trips", tags=["trips"])


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


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)) -> TripResponse:
    user = find_user(db, payload.created_by_user_id)
    invite_code = generate_invite_code()
    while db.query(Trip).filter(Trip.invite_code == invite_code).first() is not None:
        invite_code = generate_invite_code()
    trip = Trip(name=payload.name.strip(), invite_code=invite_code, created_by_user_id=user.id)
    db.add(trip)
    db.flush()
    db.add(Member(trip_id=trip.id, user_id=user.id, name=user.username))
    db.commit()
    db.refresh(trip)
    return serialize_trip(trip)


@router.post("/join", response_model=TripResponse)
def join_trip(payload: TripJoin, db: Session = Depends(get_db)) -> TripResponse:
    user = find_user(db, payload.user_id)
    trip = db.query(Trip).filter(Trip.invite_code == payload.invite_code.upper()).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="invite code not found")
    existing_user_member = db.query(Member).filter(Member.trip_id == trip.id, Member.user_id == user.id).first()
    if existing_user_member is not None:
        return serialize_trip(trip)
    existing_name_member = db.query(Member).filter(Member.trip_id == trip.id, Member.name == user.username).first()
    if existing_name_member is not None:
        raise HTTPException(status_code=409, detail="username already exists in this trip")
    trip.version += 1
    db.add(Member(trip_id=trip.id, user_id=user.id, name=user.username))
    db.commit()
    db.refresh(trip)
    return serialize_trip(trip)
