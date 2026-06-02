# 旅摊摊 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable version of 旅摊摊: a SwiftUI iOS app backed by a Python FastAPI service where users enter a username, create or join a trip by invite code, collaboratively record expenses, and view settlement results.

**Architecture:** The FastAPI backend is the source of truth for users, trips, members, expenses, categories, and settlement calculations. The iOS app uses SwiftUI for screens, a small API client for server calls, local storage for the current user session, and polling for near-real-time trip updates. Amount math is handled with decimal-safe logic on both backend and iOS input validation, with the backend owning final settlement.

**Tech Stack:** SwiftUI, iOS 17, Swift Foundation Decimal, Python FastAPI, SQLAlchemy, SQLite for local development, pytest, uvicorn, JSON REST API, polling-based sync.

---

## File Structure

Create this project layout:

```text
backend/
  app/
    __init__.py
    main.py
    database.py
    models.py
    schemas.py
    seed.py
    services/
      __init__.py
      invite_codes.py
      money.py
      settlements.py
    routers/
      __init__.py
      users.py
      trips.py
      expenses.py
  tests/
    conftest.py
    test_invite_codes.py
    test_money.py
    test_settlements.py
    test_users.py
    test_trips.py
    test_expenses.py
  requirements.txt
  README.md

ios/
  Lvtantan/
    LvtantanApp.swift
    Models/
      APIModels.swift
      AppState.swift
      MoneyExpression.swift
      SettlementModels.swift
    Services/
      APIClient.swift
      SessionStore.swift
      TripPoller.swift
    Views/
      RootView.swift
      UsernameView.swift
      TripListView.swift
      TripFormView.swift
      TripHomeView.swift
      ExpenseFormView.swift
      ExpenseListView.swift
      SettlementView.swift
      MemberListView.swift
      SettingsView.swift
  LvtantanTests/
    MoneyExpressionTests.swift
    SettlementFormattingTests.swift
```

Responsibilities:

- `backend/app/models.py`: SQLAlchemy database tables.
- `backend/app/schemas.py`: request and response DTOs.
- `backend/app/services/money.py`: Decimal parsing, rounding, and amount normalization.
- `backend/app/services/invite_codes.py`: 6-character alphanumeric invite code generation.
- `backend/app/services/settlements.py`: member balances and minimal transfer suggestions.
- `backend/app/routers/*.py`: REST endpoints grouped by domain.
- `ios/Lvtantan/Models/APIModels.swift`: Swift Codable API models.
- `ios/Lvtantan/Services/APIClient.swift`: network boundary.
- `ios/Lvtantan/Services/SessionStore.swift`: local user ID and username persistence.
- `ios/Lvtantan/Services/TripPoller.swift`: polling loop for the active trip.
- `ios/Lvtantan/Models/MoneyExpression.swift`: client-side expression parsing for `+ - * /`, decimals, and parentheses.
- `ios/Lvtantan/Views/*.swift`: focused SwiftUI screens.

## API Contract

Use JSON. UUIDs are strings. Money amounts are decimal strings, not floats.

Core endpoints:

```text
POST   /users
GET    /users/{user_id}/trips
POST   /trips
POST   /trips/join
GET    /trips/{trip_id}
GET    /trips/{trip_id}/changes?since_version=0
POST   /trips/{trip_id}/expenses
PUT    /trips/{trip_id}/expenses/{expense_id}
DELETE /trips/{trip_id}/expenses/{expense_id}
GET    /trips/{trip_id}/settlement
```

Representative payloads:

```json
{
  "username": "小李"
}
```

```json
{
  "name": "青岛周末旅行",
  "created_by_user_id": "USER_UUID"
}
```

```json
{
  "invite_code": "A7K2Q9",
  "user_id": "USER_UUID"
}
```

```json
{
  "user_id": "USER_UUID",
  "amount": "128.50",
  "expression_text": "100+57/2",
  "category_name": "餐饮",
  "spent_at": "2026-06-02T12:00:00Z",
  "note": "第一天晚饭"
}
```

---

### Task 1: Backend Project Skeleton

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/README.md`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/database.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Add backend dependencies**

Create `backend/requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.4
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: Add database setup**

Create `backend/app/database.py`:

```python
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./lvtantan.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Add FastAPI app**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Lvtantan API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Add pytest smoke test**

Create `backend/tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)
```

Create `backend/tests/test_health.py`:

```python
def test_health_returns_ok(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 5: Run backend smoke test**

Run:

```bash
cd backend
pytest tests/test_health.py -v
```

Expected: `1 passed`.

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "chore: add FastAPI backend skeleton"
```

### Task 2: Backend Models and Database Creation

**Files:**
- Create: `backend/app/models.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write model test**

Create `backend/tests/test_models.py`:

```python
from app.database import Base
from app import models


def test_expected_tables_are_declared():
    table_names = set(Base.metadata.tables.keys())
    assert {
        "users",
        "trips",
        "members",
        "categories",
        "expenses",
        "realtime_events",
    }.issubset(table_names)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend
pytest tests/test_models.py -v
```

Expected: FAIL because `app.models` does not exist.

- [ ] **Step 3: Implement SQLAlchemy models**

Create `backend/app/models.py`:

```python
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
```

- [ ] **Step 4: Create tables at startup**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.database import Base, engine
from app import models

app = FastAPI(title="Lvtantan API")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run model tests**

Run:

```bash
cd backend
pytest tests/test_models.py tests/test_health.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: add backend data models"
```

### Task 3: Backend Money and Invite Code Services

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/money.py`
- Create: `backend/app/services/invite_codes.py`
- Test: `backend/tests/test_money.py`
- Test: `backend/tests/test_invite_codes.py`

- [ ] **Step 1: Write money tests**

Create `backend/tests/test_money.py`:

```python
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
```

- [ ] **Step 2: Write invite code tests**

Create `backend/tests/test_invite_codes.py`:

```python
import re
from app.services.invite_codes import generate_invite_code


def test_invite_code_has_six_alphanumeric_uppercase_chars():
    code = generate_invite_code()
    assert re.fullmatch(r"[A-Z0-9]{6}", code)
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd backend
pytest tests/test_money.py tests/test_invite_codes.py -v
```

Expected: FAIL because services do not exist.

- [ ] **Step 4: Implement services**

Create `backend/app/services/money.py`:

```python
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

CENTS = Decimal("0.01")


def normalize_amount(raw: str) -> Decimal:
    try:
        amount = Decimal(raw).quantize(CENTS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be a decimal string") from exc
    if amount <= 0:
        raise ValueError("amount must be positive")
    return amount
```

Create `backend/app/services/invite_codes.py`:

```python
import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits


def generate_invite_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))
```

Create `backend/app/services/__init__.py`:

```python
```

- [ ] **Step 5: Run service tests**

Run:

```bash
cd backend
pytest tests/test_money.py tests/test_invite_codes.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services backend/tests/test_money.py backend/tests/test_invite_codes.py
git commit -m "feat: add money and invite code services"
```

### Task 4: Backend Settlement Service

**Files:**
- Create: `backend/app/services/settlements.py`
- Test: `backend/tests/test_settlements.py`

- [ ] **Step 1: Write settlement tests**

Create `backend/tests/test_settlements.py`:

```python
from decimal import Decimal
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend
pytest tests/test_settlements.py -v
```

Expected: FAIL because settlement service does not exist.

- [ ] **Step 3: Implement settlement service**

Create `backend/app/services/settlements.py`:

```python
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


@dataclass
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


@dataclass
class SettlementResult:
    member_summaries: dict[str, MemberSummary]
    transfers: list[Transfer]


def split_amount(amount: Decimal, count: int) -> list[Decimal]:
    base = (amount / count).quantize(CENTS, rounding=ROUND_HALF_UP)
    shares = [base for _ in range(count)]
    delta = amount - sum(shares)
    index = 0
    while delta != Decimal("0.00"):
        adjustment = CENTS if delta > 0 else -CENTS
        shares[index] += adjustment
        delta -= adjustment
        index = (index + 1) % count
    return shares


def calculate_settlement(members: list[MemberInput], expenses: list[ExpenseInput]) -> SettlementResult:
    if not members:
        return SettlementResult(member_summaries={}, transfers=[])

    summaries = {
        member.id: MemberSummary(
            member_id=member.id,
            name=member.name,
            paid=Decimal("0.00"),
            owed=Decimal("0.00"),
            balance=Decimal("0.00"),
        )
        for member in members
    }

    member_ids = [member.id for member in members]
    for expense in expenses:
        summaries[expense.paid_by_member_id].paid += expense.amount
        shares = split_amount(expense.amount, len(member_ids))
        for member_id, share in zip(member_ids, shares):
            summaries[member_id].owed += share

    for summary in summaries.values():
        summary.balance = (summary.paid - summary.owed).quantize(CENTS)

    creditors = [
        [summary.member_id, summary.balance]
        for summary in summaries.values()
        if summary.balance > 0
    ]
    debtors = [
        [summary.member_id, -summary.balance]
        for summary in summaries.values()
        if summary.balance < 0
    ]

    transfers: list[Transfer] = []
    i = 0
    j = 0
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        amount = min(debt, credit).quantize(CENTS)
        if amount > 0:
            transfers.append(Transfer(from_member_id=debtor_id, to_member_id=creditor_id, amount=amount))
        debtors[i][1] -= amount
        creditors[j][1] -= amount
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return SettlementResult(member_summaries=summaries, transfers=transfers)
```

- [ ] **Step 4: Run settlement tests**

Run:

```bash
cd backend
pytest tests/test_settlements.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/settlements.py backend/tests/test_settlements.py
git commit -m "feat: add settlement calculation"
```

### Task 5: Backend Schemas and User API

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/users.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_users.py`

- [ ] **Step 1: Write user API test**

Create `backend/tests/test_users.py`:

```python
def test_create_user_returns_user_id(test_client):
    response = test_client.post("/users", json={"username": "小李"})

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "小李"
    assert isinstance(body["id"], str)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd backend
pytest tests/test_users.py -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Implement schemas and user router**

Create `backend/app/schemas.py`:

```python
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=24)


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}
```

Create `backend/app/routers/__init__.py`:

```python
```

Create `backend/app/routers/users.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(username=payload.username.strip())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import users

app = FastAPI(title="Lvtantan API")
app.include_router(users.router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run user tests**

Run:

```bash
cd backend
pytest tests/test_users.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas.py backend/app/routers backend/app/main.py backend/tests/test_users.py
git commit -m "feat: add user registration API"
```

### Task 6: Backend Trip and Invite APIs

**Files:**
- Modify: `backend/app/schemas.py`
- Create: `backend/app/routers/trips.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_trips.py`

- [ ] **Step 1: Write trip API tests**

Create `backend/tests/test_trips.py`:

```python
def create_user(test_client, username="小李"):
    return test_client.post("/users", json={"username": username}).json()


def test_create_trip_generates_invite_code_and_membership(test_client):
    user = create_user(test_client)
    response = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": user["id"],
    })

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "青岛周末旅行"
    assert len(body["invite_code"]) == 6
    assert body["currency_code"] == "CNY"
    assert body["members"][0]["name"] == "小李"


def test_join_trip_rejects_duplicate_member_name(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    duplicate = create_user(test_client, "小李")

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": duplicate["id"],
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "username already exists in this trip"


def test_join_trip_adds_member(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    friend = create_user(test_client, "小王")

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": friend["id"],
    })

    assert response.status_code == 200
    member_names = [member["name"] for member in response.json()["members"]]
    assert member_names == ["小李", "小王"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend
pytest tests/test_trips.py -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Add schemas**

Append to `backend/app/schemas.py`:

```python
class MemberResponse(BaseModel):
    id: str
    user_id: str
    name: str
    color_hex: str | None
    status: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class TripCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    created_by_user_id: str


class TripJoin(BaseModel):
    invite_code: str = Field(min_length=6, max_length=6)
    user_id: str


class TripResponse(BaseModel):
    id: str
    name: str
    invite_code: str
    currency_code: str
    status: str
    version: int
    members: list[MemberResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Implement trip router**

Create `backend/app/routers/trips.py`:

```python
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
```

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import trips, users

app = FastAPI(title="Lvtantan API")
app.include_router(users.router)
app.include_router(trips.router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run trip tests**

Run:

```bash
cd backend
pytest tests/test_trips.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app backend/tests/test_trips.py
git commit -m "feat: add trip invite APIs"
```

### Task 7: Backend Expense, Trip Detail, Changes, and Settlement APIs

**Files:**
- Modify: `backend/app/schemas.py`
- Create: `backend/app/routers/expenses.py`
- Modify: `backend/app/routers/trips.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_expenses.py`

- [ ] **Step 1: Write expense API tests**

Create `backend/tests/test_expenses.py`:

```python
def create_user(test_client, username):
    return test_client.post("/users", json={"username": username}).json()


def create_trip_with_two_members(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    friend = create_user(test_client, "小王")
    trip = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": friend["id"],
    }).json()
    return creator, friend, trip


def test_create_expense_defaults_payer_to_registering_member(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)

    response = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "128.50",
        "expression_text": "100+28.5",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "第一天晚饭",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "128.50"
    assert body["created_by_member_id"] == body["paid_by_member_id"]


def test_get_settlement_splits_across_all_active_members(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    })

    response = test_client.get(f"/trips/{trip['id']}/settlement")

    assert response.status_code == 200
    body = response.json()
    balances = {member["name"]: member["balance"] for member in body["members"]}
    assert balances["小李"] == "50.00"
    assert balances["小王"] == "-50.00"
    assert body["transfers"] == [{
        "from_member_id": body["members"][1]["member_id"],
        "from_member_name": "小王",
        "to_member_id": body["members"][0]["member_id"],
        "to_member_name": "小李",
        "amount": "50.00",
    }]


def test_update_expense_allows_any_member_and_increments_version(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    created = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    }).json()

    response = test_client.put(f"/trips/{trip['id']}/expenses/{created['id']}", json={
        "user_id": friend["id"],
        "amount": "120.00",
        "expression_text": "(100+20)",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:30:00Z",
        "note": "改成含饮料",
    })

    assert response.status_code == 200
    assert response.json()["amount"] == "120.00"
    assert response.json()["note"] == "改成含饮料"


def test_delete_expense_records_change_event(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    created = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    }).json()

    response = test_client.delete(f"/trips/{trip['id']}/expenses/{created['id']}", json={
        "user_id": friend["id"],
    })

    assert response.status_code == 204
    detail = test_client.get(f"/trips/{trip['id']}").json()
    assert detail["expenses"] == []


def test_changes_returns_events_since_version(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    })

    response = test_client.get(f"/trips/{trip['id']}/changes?since_version=0")

    assert response.status_code == 200
    body = response.json()
    assert body["current_version"] >= 3
    assert any(event["action"] == "created" for event in body["events"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd backend
pytest tests/test_expenses.py -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Add schemas**

Append to `backend/app/schemas.py`:

```python
class ExpenseCreate(BaseModel):
    user_id: str
    amount: str
    expression_text: str | None = None
    category_name: str = Field(min_length=1, max_length=24)
    spent_at: datetime
    note: str | None = Field(default=None, max_length=120)


class ExpenseDelete(BaseModel):
    user_id: str


class ExpenseResponse(BaseModel):
    id: str
    trip_id: str
    amount: str
    expression_text: str | None
    created_by_member_id: str
    paid_by_member_id: str
    category_name: str
    spent_at: datetime
    note: str | None
    created_at: datetime
    updated_at: datetime


class TripDetailResponse(TripResponse):
    expenses: list[ExpenseResponse]


class SettlementMemberResponse(BaseModel):
    member_id: str
    name: str
    paid: str
    owed: str
    balance: str


class SettlementTransferResponse(BaseModel):
    from_member_id: str
    from_member_name: str
    to_member_id: str
    to_member_name: str
    amount: str


class SettlementResponse(BaseModel):
    members: list[SettlementMemberResponse]
    transfers: list[SettlementTransferResponse]


class RealtimeEventResponse(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    version: int
    created_at: datetime


class ChangesResponse(BaseModel):
    current_version: int
    events: list[RealtimeEventResponse]
```

- [ ] **Step 4: Implement expense router**

Create `backend/app/routers/expenses.py`:

```python
from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, Expense, Member, RealtimeEvent, Trip
from app.schemas import ExpenseCreate, ExpenseDelete, ExpenseResponse
from app.services.money import normalize_amount

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["expenses"])


def find_trip(db: Session, trip_id: str) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    return trip


def find_member(db: Session, trip_id: str, user_id: str) -> Member:
    member = db.query(Member).filter(
        Member.trip_id == trip_id,
        Member.user_id == user_id,
        Member.status == "active",
    ).first()
    if member is None:
        raise HTTPException(status_code=403, detail="user is not an active trip member")
    return member


def get_or_create_category(db: Session, name: str) -> Category:
    category = db.query(Category).filter(Category.name == name).first()
    if category is not None:
        return category
    category = Category(name=name, sort_order=999)
    db.add(category)
    db.flush()
    return category


def to_expense_response(expense: Expense, category_name: str) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense.id,
        trip_id=expense.trip_id,
        amount=f"{Decimal(expense.amount):.2f}",
        expression_text=expense.expression_text,
        created_by_member_id=expense.created_by_member_id,
        paid_by_member_id=expense.paid_by_member_id,
        category_name=category_name,
        spent_at=expense.spent_at,
        note=expense.note,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(trip_id: str, payload: ExpenseCreate, db: Session = Depends(get_db)) -> ExpenseResponse:
    trip = find_trip(db, trip_id)
    member = find_member(db, trip_id, payload.user_id)
    category = get_or_create_category(db, payload.category_name)
    amount = normalize_amount(payload.amount)
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
    db.add(expense)
    db.flush()
    db.add(RealtimeEvent(trip_id=trip.id, entity_type="expense", entity_id=expense.id, action="created", version=trip.version))
    db.commit()
    db.refresh(expense)
    return to_expense_response(expense, category.name)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(trip_id: str, expense_id: str, payload: ExpenseCreate, db: Session = Depends(get_db)) -> ExpenseResponse:
    trip = find_trip(db, trip_id)
    find_member(db, trip_id, payload.user_id)
    expense = db.get(Expense, expense_id)
    if expense is None or expense.trip_id != trip.id:
        raise HTTPException(status_code=404, detail="expense not found")
    category = get_or_create_category(db, payload.category_name)
    expense.amount = normalize_amount(payload.amount)
    expense.expression_text = payload.expression_text
    expense.category_id = category.id
    expense.spent_at = payload.spent_at
    expense.note = payload.note
    expense.updated_at = datetime.now(timezone.utc)
    trip.version += 1
    db.add(RealtimeEvent(trip_id=trip.id, entity_type="expense", entity_id=expense.id, action="updated", version=trip.version))
    db.commit()
    db.refresh(expense)
    return to_expense_response(expense, category.name)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(trip_id: str, expense_id: str, payload: ExpenseDelete, db: Session = Depends(get_db)) -> Response:
    trip = find_trip(db, trip_id)
    find_member(db, trip_id, payload.user_id)
    expense = db.get(Expense, expense_id)
    if expense is None or expense.trip_id != trip.id:
        raise HTTPException(status_code=404, detail="expense not found")
    trip.version += 1
    db.delete(expense)
    db.add(RealtimeEvent(trip_id=trip.id, entity_type="expense", entity_id=expense.id, action="deleted", version=trip.version))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 5: Extend trip router for detail and settlement**

Append to `backend/app/routers/trips.py`:

```python
from decimal import Decimal
from app.models import Category, Expense
from app.schemas import (
    ChangesResponse,
    ExpenseResponse,
    RealtimeEventResponse,
    SettlementMemberResponse,
    SettlementResponse,
    SettlementTransferResponse,
    TripDetailResponse,
)
from app.services.settlements import ExpenseInput, MemberInput, calculate_settlement


def expense_response(db: Session, expense: Expense) -> ExpenseResponse:
    category = db.get(Category, expense.category_id)
    return ExpenseResponse(
        id=expense.id,
        trip_id=expense.trip_id,
        amount=f"{Decimal(expense.amount):.2f}",
        expression_text=expense.expression_text,
        created_by_member_id=expense.created_by_member_id,
        paid_by_member_id=expense.paid_by_member_id,
        category_name=category.name if category else "其他",
        spent_at=expense.spent_at,
        note=expense.note,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip(trip_id: str, db: Session = Depends(get_db)) -> TripDetailResponse:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    base = serialize_trip(trip).model_dump()
    expenses = sorted(trip.expenses, key=lambda expense: expense.spent_at, reverse=True)
    base["expenses"] = [expense_response(db, expense) for expense in expenses]
    return TripDetailResponse.model_validate(base)


@router.get("/{trip_id}/settlement", response_model=SettlementResponse)
def get_settlement(trip_id: str, db: Session = Depends(get_db)) -> SettlementResponse:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    active_members = sorted([m for m in trip.members if m.status == "active"], key=lambda m: m.joined_at)
    member_inputs = [MemberInput(id=member.id, name=member.name) for member in active_members]
    expense_inputs = [
        ExpenseInput(amount=Decimal(expense.amount), paid_by_member_id=expense.paid_by_member_id)
        for expense in trip.expenses
    ]
    result = calculate_settlement(member_inputs, expense_inputs)
    member_name_by_id = {member.id: member.name for member in active_members}
    members = [
        SettlementMemberResponse(
            member_id=summary.member_id,
            name=summary.name,
            paid=f"{summary.paid:.2f}",
            owed=f"{summary.owed:.2f}",
            balance=f"{summary.balance:.2f}",
        )
        for summary in result.member_summaries.values()
    ]
    transfers = [
        SettlementTransferResponse(
            from_member_id=transfer.from_member_id,
            from_member_name=member_name_by_id[transfer.from_member_id],
            to_member_id=transfer.to_member_id,
            to_member_name=member_name_by_id[transfer.to_member_id],
            amount=f"{transfer.amount:.2f}",
        )
        for transfer in result.transfers
    ]
    return SettlementResponse(members=members, transfers=transfers)


@router.get("/{trip_id}/changes", response_model=ChangesResponse)
def get_changes(trip_id: str, since_version: int = 0, db: Session = Depends(get_db)) -> ChangesResponse:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    events = db.query(RealtimeEvent).filter(
        RealtimeEvent.trip_id == trip.id,
        RealtimeEvent.version > since_version,
    ).order_by(RealtimeEvent.version.asc()).all()
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
```

Modify `backend/app/main.py` to include the expense router:

```python
from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import expenses, trips, users

app = FastAPI(title="Lvtantan API")
app.include_router(users.router)
app.include_router(trips.router)
app.include_router(expenses.router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 6: Run expense tests**

Run:

```bash
cd backend
pytest tests/test_expenses.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app backend/tests/test_expenses.py
git commit -m "feat: add expense and settlement APIs"
```

### Task 8: iOS Project Skeleton

**Files:**
- Create the iOS project in Xcode under `ios/Lvtantan`.
- Create: `ios/Lvtantan/LvtantanApp.swift`
- Create: `ios/Lvtantan/Models/AppState.swift`
- Create: `ios/Lvtantan/Views/RootView.swift`
- Create: `ios/Lvtantan/Views/TripListView.swift`
- Create: `ios/Lvtantan/Views/TripHomeView.swift`
- Create: `ios/Lvtantan/Views/SettlementView.swift`

- [ ] **Step 1: Create Xcode project**

In Xcode:

```text
File -> New -> Project -> iOS App
Product Name: Lvtantan
Interface: SwiftUI
Language: Swift
Minimum Deployment: iOS 17.0
Bundle Identifier: com.iamnotlcb.lvtantan
```

Save it under:

```text
ios/Lvtantan
```

- [ ] **Step 2: Add app state**

Create `ios/Lvtantan/Models/AppState.swift`:

```swift
import Foundation

@MainActor
final class AppState: ObservableObject {
    @Published var currentUser: APIUser?
    @Published var trips: [APITripSummary] = []
    @Published var activeTrip: APITripDetail?
    @Published var errorMessage: String?
}
```

- [ ] **Step 3: Add initial API models**

Create `ios/Lvtantan/Models/APIModels.swift`:

```swift
import Foundation

struct APIUser: Codable, Identifiable, Equatable {
    let id: String
    let username: String
}

struct APITripSummary: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
}

struct APITripDetail: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
}
```

- [ ] **Step 4: Add root view**

Create `ios/Lvtantan/Views/RootView.swift`:

```swift
import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Group {
            if appState.currentUser == nil {
                Text("旅摊摊")
                    .font(.largeTitle.bold())
            } else {
                Text("账本列表")
                    .font(.title)
            }
        }
    }
}
```

- [ ] **Step 5: Add base views used by early navigation**

Create `ios/Lvtantan/Views/TripListView.swift`:

```swift
import SwiftUI

struct TripListView: View {
    var body: some View {
        NavigationStack {
            Text("账本列表")
                .navigationTitle("旅摊摊")
        }
    }
}
```

Create `ios/Lvtantan/Views/TripHomeView.swift`:

```swift
import SwiftUI

struct TripHomeView: View {
    let tripId: String

    var body: some View {
        Text("账本详情")
            .navigationTitle("账本")
    }
}
```

Create `ios/Lvtantan/Views/SettlementView.swift`:

```swift
import SwiftUI

struct SettlementView: View {
    let tripId: String

    var body: some View {
        Text("结算")
            .navigationTitle("结算")
    }
}
```

- [ ] **Step 6: Wire app entry**

Update `ios/Lvtantan/LvtantanApp.swift`:

```swift
import SwiftUI

@main
struct LvtantanApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
        }
    }
}
```

- [ ] **Step 7: Build in Xcode**

Run the app in an iPhone simulator.

Expected: app launches and displays `旅摊摊`.

- [ ] **Step 8: Commit**

```bash
git add ios
git commit -m "chore: add iOS project skeleton"
```

### Task 9: iOS Money Expression Parser

**Files:**
- Create: `ios/Lvtantan/Models/MoneyExpression.swift`
- Test: `ios/LvtantanTests/MoneyExpressionTests.swift`

- [ ] **Step 1: Write parser tests**

Create `ios/LvtantanTests/MoneyExpressionTests.swift`:

```swift
import XCTest
@testable import Lvtantan

final class MoneyExpressionTests: XCTestCase {
    func testAddsAndDivides() throws {
        XCTAssertEqual(try MoneyExpression.evaluate("100+20/2"), Decimal(110))
    }

    func testSupportsParentheses() throws {
        XCTAssertEqual(try MoneyExpression.evaluate("(100+20)/2"), Decimal(60))
    }

    func testRejectsNegativeResult() throws {
        XCTAssertThrowsError(try MoneyExpression.evaluate("1-2"))
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run in Xcode:

```text
Product -> Test
```

Expected: FAIL because `MoneyExpression` does not exist.

- [ ] **Step 3: Implement parser**

Create `ios/Lvtantan/Models/MoneyExpression.swift`:

```swift
import Foundation

enum MoneyExpressionError: Error {
    case invalidExpression
    case nonPositiveAmount
}

enum MoneyExpression {
    static func evaluate(_ input: String) throws -> Decimal {
        let sanitized = input.replacingOccurrences(of: " ", with: "")
        guard sanitized.range(of: #"^[0-9+\-*/().]+$"#, options: .regularExpression) != nil else {
            throw MoneyExpressionError.invalidExpression
        }
        let expression = NSExpression(format: sanitized)
        guard let number = expression.expressionValue(with: nil, context: nil) as? NSNumber else {
            throw MoneyExpressionError.invalidExpression
        }
        var decimal = number.decimalValue
        var rounded = Decimal()
        NSDecimalRound(&rounded, &decimal, 2, .plain)
        guard rounded > 0 else {
            throw MoneyExpressionError.nonPositiveAmount
        }
        return rounded
    }
}
```

- [ ] **Step 4: Run parser tests**

Run in Xcode:

```text
Product -> Test
```

Expected: `MoneyExpressionTests` pass.

- [ ] **Step 5: Commit**

```bash
git add ios/Lvtantan/Models/MoneyExpression.swift ios/LvtantanTests/MoneyExpressionTests.swift
git commit -m "feat: add iOS money expression parser"
```

### Task 10: iOS API Models and API Client

**Files:**
- Modify: `ios/Lvtantan/Models/APIModels.swift`
- Create: `ios/Lvtantan/Services/APIClient.swift`

- [ ] **Step 1: Replace API models**

Update `ios/Lvtantan/Models/APIModels.swift`:

```swift
import Foundation

struct APIUser: Codable, Identifiable, Equatable {
    let id: String
    let username: String
}

struct APIMember: Codable, Identifiable, Equatable {
    let id: String
    let userId: String
    let name: String
    let status: String
}

struct APIExpense: Codable, Identifiable, Equatable {
    let id: String
    let tripId: String
    let amount: String
    let expressionText: String?
    let createdByMemberId: String
    let paidByMemberId: String
    let categoryName: String
    let spentAt: Date
    let note: String?
}

struct APITripSummary: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
    let currencyCode: String
    let status: String
    let version: Int
    let members: [APIMember]
}

struct APITripDetail: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
    let currencyCode: String
    let status: String
    let version: Int
    let members: [APIMember]
    let expenses: [APIExpense]
}

struct APISettlement: Codable, Equatable {
    let members: [APISettlementMember]
    let transfers: [APISettlementTransfer]
}

struct APISettlementMember: Codable, Equatable {
    let memberId: String
    let name: String
    let paid: String
    let owed: String
    let balance: String
}

struct APISettlementTransfer: Codable, Equatable {
    let fromMemberId: String
    let fromMemberName: String
    let toMemberId: String
    let toMemberName: String
    let amount: String
}
```

- [ ] **Step 2: Add API client**

Create `ios/Lvtantan/Services/APIClient.swift`:

```swift
import Foundation

final class APIClient {
    let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(baseURL: URL = URL(string: "http://127.0.0.1:8000")!, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601
        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
        self.encoder.dateEncodingStrategy = .iso8601
    }

    func createUser(username: String) async throws -> APIUser {
        try await request("users", method: "POST", body: ["username": username])
    }

    func createTrip(name: String, userId: String) async throws -> APITripSummary {
        try await request("trips", method: "POST", body: ["name": name, "created_by_user_id": userId])
    }

    func joinTrip(inviteCode: String, userId: String) async throws -> APITripSummary {
        try await request("trips/join", method: "POST", body: ["invite_code": inviteCode, "user_id": userId])
    }

    func getTrip(id: String) async throws -> APITripDetail {
        try await request("trips/\(id)", method: "GET", body: Optional<String>.none)
    }

    func createExpense(tripId: String, payload: [String: String]) async throws -> APIExpense {
        try await request("trips/\(tripId)/expenses", method: "POST", body: payload)
    }

    func getSettlement(tripId: String) async throws -> APISettlement {
        try await request("trips/\(tripId)/settlement", method: "GET", body: Optional<String>.none)
    }

    private func request<Response: Decodable, Body: Encodable>(_ path: String, method: String, body: Body?) async throws -> Response {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body {
            request.httpBody = try encoder.encode(body)
        }
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, (200..<300).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try decoder.decode(Response.self, from: data)
    }
}
```

- [ ] **Step 3: Build**

Run in Xcode:

```text
Product -> Build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add ios/Lvtantan/Models/APIModels.swift ios/Lvtantan/Services/APIClient.swift
git commit -m "feat: add iOS API client"
```

### Task 11: iOS Session and Username Flow

**Files:**
- Create: `ios/Lvtantan/Services/SessionStore.swift`
- Create: `ios/Lvtantan/Views/UsernameView.swift`
- Modify: `ios/Lvtantan/Views/RootView.swift`

- [ ] **Step 1: Add session store**

Create `ios/Lvtantan/Services/SessionStore.swift`:

```swift
import Foundation

struct SessionStore {
    private let userIdKey = "lvtantan.userId"
    private let usernameKey = "lvtantan.username"

    func loadUser() -> APIUser? {
        guard let id = UserDefaults.standard.string(forKey: userIdKey),
              let username = UserDefaults.standard.string(forKey: usernameKey) else {
            return nil
        }
        return APIUser(id: id, username: username)
    }

    func save(user: APIUser) {
        UserDefaults.standard.set(user.id, forKey: userIdKey)
        UserDefaults.standard.set(user.username, forKey: usernameKey)
    }
}
```

- [ ] **Step 2: Add username view**

Create `ios/Lvtantan/Views/UsernameView.swift`:

```swift
import SwiftUI

struct UsernameView: View {
    @EnvironmentObject private var appState: AppState
    @State private var username = ""
    @State private var isSubmitting = false
    private let apiClient = APIClient()
    private let sessionStore = SessionStore()

    var body: some View {
        VStack(spacing: 20) {
            Text("旅摊摊")
                .font(.largeTitle.bold())
            TextField("输入用户名", text: $username)
                .textFieldStyle(.roundedBorder)
                .textInputAutocapitalization(.never)
            Button(isSubmitting ? "创建中..." : "进入") {
                Task { await submit() }
            }
            .buttonStyle(.borderedProminent)
            .disabled(username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSubmitting)
        }
        .padding()
    }

    private func submit() async {
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            let user = try await apiClient.createUser(username: username.trimmingCharacters(in: .whitespacesAndNewlines))
            sessionStore.save(user: user)
            appState.currentUser = user
        } catch {
            appState.errorMessage = "创建用户失败，请稍后再试"
        }
    }
}
```

- [ ] **Step 3: Update root view**

Update `ios/Lvtantan/Views/RootView.swift`:

```swift
import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState
    private let sessionStore = SessionStore()

    var body: some View {
        Group {
            if appState.currentUser == nil {
                UsernameView()
            } else {
                TripListView()
            }
        }
        .onAppear {
            appState.currentUser = sessionStore.loadUser()
        }
        .alert("提示", isPresented: .constant(appState.errorMessage != nil)) {
            Button("好") { appState.errorMessage = nil }
        } message: {
            Text(appState.errorMessage ?? "")
        }
    }
}
```

- [ ] **Step 4: Build**

Run in Xcode:

```text
Product -> Build
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add ios/Lvtantan/Services/SessionStore.swift ios/Lvtantan/Views/UsernameView.swift ios/Lvtantan/Views/RootView.swift
git commit -m "feat: add username session flow"
```

### Task 12: iOS Trip List, Create, and Join Flow

**Files:**
- Modify: `ios/Lvtantan/Views/TripListView.swift`
- Create: `ios/Lvtantan/Views/TripFormView.swift`
- Modify: `ios/Lvtantan/Views/RootView.swift`

- [ ] **Step 1: Add trip list view**

Replace `ios/Lvtantan/Views/TripListView.swift`:

```swift
import SwiftUI

struct TripListView: View {
    @EnvironmentObject private var appState: AppState
    @State private var showingCreate = false
    @State private var showingJoin = false

    var body: some View {
        NavigationStack {
            List(appState.trips) { trip in
                NavigationLink(trip.name) {
                    TripHomeView(tripId: trip.id)
                }
            }
            .navigationTitle("旅摊摊")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("加入") { showingJoin = true }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("创建") { showingCreate = true }
                }
            }
            .sheet(isPresented: $showingCreate) {
                TripFormView(mode: .create)
            }
            .sheet(isPresented: $showingJoin) {
                TripFormView(mode: .join)
            }
        }
    }
}
```

- [ ] **Step 2: Add trip form**

Create `ios/Lvtantan/Views/TripFormView.swift`:

```swift
import SwiftUI

enum TripFormMode {
    case create
    case join
}

struct TripFormView: View {
    let mode: TripFormMode
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var text = ""
    private let apiClient = APIClient()

    var body: some View {
        NavigationStack {
            Form {
                TextField(mode == .create ? "旅行名称" : "邀请码", text: $text)
                    .textInputAutocapitalization(.characters)
                Button(mode == .create ? "创建账本" : "加入账本") {
                    Task { await submit() }
                }
                .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .navigationTitle(mode == .create ? "创建账本" : "加入账本")
        }
    }

    private func submit() async {
        guard let user = appState.currentUser else { return }
        do {
            let trip: APITripSummary
            if mode == .create {
                trip = try await apiClient.createTrip(name: text, userId: user.id)
            } else {
                trip = try await apiClient.joinTrip(inviteCode: text.uppercased(), userId: user.id)
            }
            if !appState.trips.contains(where: { $0.id == trip.id }) {
                appState.trips.append(trip)
            }
            dismiss()
        } catch {
            appState.errorMessage = mode == .create ? "创建账本失败" : "加入账本失败"
        }
    }
}
```

- [ ] **Step 3: Build**

Run in Xcode:

```text
Product -> Build
```

Expected: build succeeds because `TripHomeView` base view already exists from Task 8.

- [ ] **Step 4: Commit**

```bash
git add ios/Lvtantan/Views/TripListView.swift ios/Lvtantan/Views/TripFormView.swift
git commit -m "feat: add trip create and join flow"
```

### Task 13: iOS Trip Home, Polling, and Expense Form

**Files:**
- Create: `ios/Lvtantan/Services/TripPoller.swift`
- Modify: `ios/Lvtantan/Views/TripHomeView.swift`
- Create: `ios/Lvtantan/Views/ExpenseFormView.swift`
- Create: `ios/Lvtantan/Views/ExpenseListView.swift`

- [ ] **Step 1: Add trip poller**

Create `ios/Lvtantan/Services/TripPoller.swift`:

```swift
import Foundation

@MainActor
final class TripPoller: ObservableObject {
    private let apiClient = APIClient()
    private var task: Task<Void, Never>?

    func start(tripId: String, appState: AppState) {
        stop()
        task = Task {
            while !Task.isCancelled {
                do {
                    appState.activeTrip = try await apiClient.getTrip(id: tripId)
                } catch {
                    appState.errorMessage = "刷新账本失败"
                }
                try? await Task.sleep(nanoseconds: 4_000_000_000)
            }
        }
    }

    func stop() {
        task?.cancel()
        task = nil
    }
}
```

- [ ] **Step 2: Add trip home view**

Replace `ios/Lvtantan/Views/TripHomeView.swift`:

```swift
import SwiftUI

struct TripHomeView: View {
    let tripId: String
    @EnvironmentObject private var appState: AppState
    @StateObject private var poller = TripPoller()
    @State private var showingExpenseForm = false

    var body: some View {
        VStack {
            if let trip = appState.activeTrip {
                List {
                    Section {
                        Text("邀请码：\(trip.inviteCode)")
                        Text("成员：\(trip.members.map(\.name).joined(separator: "、"))")
                    }
                    Section("最近支出") {
                        ForEach(trip.expenses) { expense in
                            HStack {
                                VStack(alignment: .leading) {
                                    Text(expense.note ?? expense.categoryName)
                                    Text(expense.categoryName)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Text("¥\(expense.amount)")
                            }
                        }
                    }
                }
                .navigationTitle(trip.name)
            } else {
                ProgressView()
            }
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("记一笔") { showingExpenseForm = true }
            }
            ToolbarItem(placement: .bottomBar) {
                NavigationLink("结算") {
                    SettlementView(tripId: tripId)
                }
            }
        }
        .sheet(isPresented: $showingExpenseForm) {
            ExpenseFormView(tripId: tripId)
        }
        .onAppear { poller.start(tripId: tripId, appState: appState) }
        .onDisappear { poller.stop() }
    }
}
```

- [ ] **Step 3: Add expense form**

Create `ios/Lvtantan/Views/ExpenseFormView.swift`:

```swift
import SwiftUI

struct ExpenseFormView: View {
    let tripId: String
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var amountExpression = ""
    @State private var categoryName = "餐饮"
    @State private var note = ""
    private let apiClient = APIClient()

    var body: some View {
        NavigationStack {
            Form {
                TextField("金额，例如 100+20/2", text: $amountExpression)
                    .keyboardType(.numbersAndPunctuation)
                Picker("分类", selection: $categoryName) {
                    ForEach(["餐饮", "交通", "住宿", "门票", "购物", "娱乐", "其他"], id: \.self) { category in
                        Text(category)
                    }
                }
                TextField("备注", text: $note)
                Text("付款人：我")
                Text("分摊：账本内所有成员")
                Button("保存") {
                    Task { await submit() }
                }
            }
            .navigationTitle("记一笔")
        }
    }

    private func submit() async {
        guard let user = appState.currentUser else { return }
        do {
            let amount = try MoneyExpression.evaluate(amountExpression)
            let payload = [
                "user_id": user.id,
                "amount": NSDecimalNumber(decimal: amount).stringValue,
                "expression_text": amountExpression,
                "category_name": categoryName,
                "spent_at": ISO8601DateFormatter().string(from: Date()),
                "note": note,
            ]
            _ = try await apiClient.createExpense(tripId: tripId, payload: payload)
            appState.activeTrip = try await apiClient.getTrip(id: tripId)
            dismiss()
        } catch {
            appState.errorMessage = "保存支出失败，请检查金额"
        }
    }
}
```

- [ ] **Step 4: Add expense list view**

Create `ios/Lvtantan/Views/ExpenseListView.swift`:

```swift
import SwiftUI

struct ExpenseListView: View {
    let expenses: [APIExpense]

    var body: some View {
        List(expenses) { expense in
            HStack {
                Text(expense.note ?? expense.categoryName)
                Spacer()
                Text("¥\(expense.amount)")
            }
        }
        .navigationTitle("全部支出")
    }
}
```

- [ ] **Step 5: Build**

Run in Xcode:

```text
Product -> Build
```

Expected: build succeeds because `SettlementView` base view already exists from Task 8.

- [ ] **Step 6: Commit**

```bash
git add ios/Lvtantan/Services/TripPoller.swift ios/Lvtantan/Views/TripHomeView.swift ios/Lvtantan/Views/ExpenseFormView.swift ios/Lvtantan/Views/ExpenseListView.swift
git commit -m "feat: add trip home and expense flow"
```

### Task 14: iOS Settlement and Member Views

**Files:**
- Modify: `ios/Lvtantan/Views/SettlementView.swift`
- Create: `ios/Lvtantan/Views/MemberListView.swift`
- Create: `ios/Lvtantan/Views/SettingsView.swift`
- Test: `ios/LvtantanTests/SettlementFormattingTests.swift`

- [ ] **Step 1: Add settlement formatting test**

Create `ios/LvtantanTests/SettlementFormattingTests.swift`:

```swift
import XCTest
@testable import Lvtantan

final class SettlementFormattingTests: XCTestCase {
    func testTransferText() {
        let transfer = APISettlementTransfer(
            fromMemberId: "m1",
            fromMemberName: "小李",
            toMemberId: "m2",
            toMemberName: "小王",
            amount: "50.00"
        )
        XCTAssertEqual(SettlementView.transferText(transfer), "小李 转给 小王 50.00 元")
    }
}
```

- [ ] **Step 2: Add settlement view**

Replace `ios/Lvtantan/Views/SettlementView.swift`:

```swift
import SwiftUI

struct SettlementView: View {
    let tripId: String
    @State private var settlement: APISettlement?
    @EnvironmentObject private var appState: AppState
    private let apiClient = APIClient()

    var body: some View {
        List {
            if let settlement {
                Section("成员") {
                    ForEach(settlement.members, id: \.memberId) { member in
                        HStack {
                            Text(member.name)
                            Spacer()
                            Text(member.balance)
                        }
                    }
                }
                Section("建议转账") {
                    ForEach(settlement.transfers, id: \.fromMemberId) { transfer in
                        Text(Self.transferText(transfer))
                    }
                }
                Button("复制结算结果") {
                    UIPasteboard.general.string = settlement.transfers.map(Self.transferText).joined(separator: "\n")
                }
            } else {
                ProgressView()
            }
        }
        .navigationTitle("结算")
        .task {
            do {
                settlement = try await apiClient.getSettlement(tripId: tripId)
            } catch {
                appState.errorMessage = "获取结算失败"
            }
        }
    }

    static func transferText(_ transfer: APISettlementTransfer) -> String {
        "\(transfer.fromMemberName) 转给 \(transfer.toMemberName) \(transfer.amount) 元"
    }
}
```

- [ ] **Step 3: Add member and settings views**

Create `ios/Lvtantan/Views/MemberListView.swift`:

```swift
import SwiftUI

struct MemberListView: View {
    let members: [APIMember]

    var body: some View {
        List(members) { member in
            Text(member.name)
        }
        .navigationTitle("成员")
    }
}
```

Create `ios/Lvtantan/Views/SettingsView.swift`:

```swift
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Form {
            Section("当前用户") {
                Text(appState.currentUser?.username ?? "未登录")
            }
            Section("数据说明") {
                Text("账本数据保存在服务端，用于多人实时共享。")
            }
        }
        .navigationTitle("设置")
    }
}
```

- [ ] **Step 4: Run tests**

Run in Xcode:

```text
Product -> Test
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add ios/Lvtantan/Views/SettlementView.swift ios/Lvtantan/Views/MemberListView.swift ios/Lvtantan/Views/SettingsView.swift ios/LvtantanTests/SettlementFormattingTests.swift
git commit -m "feat: add settlement and member views"
```

### Task 15: End-to-End Local Verification

**Files:**
- Modify: `backend/README.md`
- Modify: `docs/prd.md` only if verification reveals a necessary product clarification.

- [ ] **Step 1: Add backend README**

Create or update `backend/README.md`:

```markdown
# Lvtantan Backend

## Run locally

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## Test

```sh
.venv/bin/pytest -v
```
```

- [ ] **Step 2: Run backend test suite**

Run:

```bash
cd backend
pytest -v
```

Expected: all backend tests pass.

- [ ] **Step 3: Start backend**

Run:

```bash
cd backend
uvicorn app.main:app --reload
```

Expected: server starts at `http://127.0.0.1:8000`.

- [ ] **Step 4: Verify API manually**

Run:

```bash
curl -s http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

- [ ] **Step 5: Run iOS app in simulator**

In Xcode:

```text
Product -> Run
```

Expected:

- App opens.
- User can enter username.
- User can create trip.
- Invite code appears.
- User can add expense with expression `(100+20)/2`.
- Settlement page shows member balance.

- [ ] **Step 6: Two-user manual test**

In API or app, create two users and join the same trip.

Expected:

- Same trip contains both members.
- Same-name join returns conflict.
- Expense by one member is split across both members.
- Settlement suggests one transfer.

- [ ] **Step 7: Commit**

```bash
git add backend/README.md docs
git commit -m "docs: add local verification steps"
```

## Self-Review

Spec coverage:

- Username light registration: Task 5 backend, Task 11 iOS.
- 6-character invite code and joining: Task 3 service, Task 6 API, Task 12 iOS.
- Same-trip username uniqueness: Task 6 test and router.
- FastAPI backend: Tasks 1-7 and 15.
- Realtime collaborative editing: Task 7 backend version/events/create/update/delete/changes APIs, Task 13 iOS polling.
- Expense entry with registrar as payer: Task 7 backend and Task 13 iOS.
- Amount expression with `+ - * /`, decimals, parentheses: Task 9 iOS, Task 7 backend stores evaluated amount and expression text.
- All active members split all expenses, including later joiners: Task 4 settlement tests and Task 7 API.
- CNY-only: Trip model default and Task 6 tests.
- Settlement suggestions: Task 4 backend, Task 7 API, Task 14 iOS.

Execution note:

- iOS base views are created in Task 8, then replaced with feature-complete versions in later tasks so every iOS task can build before commit.
