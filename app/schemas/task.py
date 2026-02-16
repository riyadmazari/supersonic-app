import uuid
import datetime
from typing import Literal
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: Literal["not_started", "in_progress", "completed", "blocked"] = "not_started"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    assignee: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: Literal["not_started", "in_progress", "completed", "blocked"] | None = None
    priority: Literal["low", "medium", "high", "critical"] | None = None
    assignee: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str
    assignee: str | None
    start_date: datetime.datetime | None
    end_date: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
