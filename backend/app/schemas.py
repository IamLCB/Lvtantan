from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=24)

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


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

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


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
