import uuid
import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    body: str | None = None
    sender: str | None = None
    task_id: uuid.UUID | None = None
    date: datetime.datetime | None = None


class MessageOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    subject: str
    body: str | None
    sender: str | None
    date: datetime.datetime

    model_config = {"from_attributes": True}
