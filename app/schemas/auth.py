import uuid
import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6)
    full_name: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
