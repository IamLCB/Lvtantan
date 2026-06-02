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
