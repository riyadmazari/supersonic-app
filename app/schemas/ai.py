import uuid
from pydantic import BaseModel, Field


class AISummaryRequest(BaseModel):
    project_id: uuid.UUID
    focus: str | None = Field(None, description="Optional focus area: 'risks', 'timeline', 'workload'")


class AISuggestionsRequest(BaseModel):
    project_id: uuid.UUID
    prompt: str | None = Field(None, description="Optional user prompt, e.g. 'optimize schedule for next month'")


class AIChatRequest(BaseModel):
    project_id: uuid.UUID
    message: str


class AIResponse(BaseModel):
    result: str
    disclaimer: str = (
        "This output is AI-generated and may contain inaccuracies. "
        "Always verify critical recommendations with your team before acting on them."
    )
