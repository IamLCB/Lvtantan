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
