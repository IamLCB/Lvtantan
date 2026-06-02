import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    username: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    memberships: Mapped[list["Member"]] = relationship(back_populates="user")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    invite_code: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    currency_code: Mapped[str] = mapped_column(String, nullable=False, default="CNY")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    members: Mapped[list["Member"]] = relationship(back_populates="trip")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="trip")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("trip_id", "name", name="uq_member_trip_name"),
        UniqueConstraint("trip_id", "user_id", name="uq_member_trip_user"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    trip_id: Mapped[str] = mapped_column(String, ForeignKey("trips.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    color_hex: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    trip: Mapped[Trip] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    icon_name: Mapped[str | None] = mapped_column(String, nullable=True)
    color_hex: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    trip_id: Mapped[str] = mapped_column(String, ForeignKey("trips.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    expression_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_member_id: Mapped[str] = mapped_column(String, ForeignKey("members.id"), nullable=False)
    paid_by_member_id: Mapped[str] = mapped_column(String, ForeignKey("members.id"), nullable=False)
    category_id: Mapped[str] = mapped_column(String, ForeignKey("categories.id"), nullable=False)
    spent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    trip: Mapped[Trip] = relationship(back_populates="expenses")


class RealtimeEvent(Base):
    __tablename__ = "realtime_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    trip_id: Mapped[str] = mapped_column(String, ForeignKey("trips.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
