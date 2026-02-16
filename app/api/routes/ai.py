import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Project, Task, User
from app.schemas.ai import AIChatRequest, AIResponse, AISuggestionsRequest, AISummaryRequest
from app.services.ai_client import (
    generate_suggestions,
    generate_summary,
    handle_chat_query,
)

router = APIRouter(prefix="/ai", tags=["ai"])


async def _project_tasks_context(
    project_id: uuid.UUID, db: AsyncSession, user: User
) -> tuple[str, list[dict]]:
    """Fetch project + tasks and return (project_name, serialised_tasks)."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rows = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = [
        {
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "assignee": t.assignee,
            "start_date": t.start_date,
            "end_date": t.end_date,
        }
        for t in rows.scalars().all()
    ]
    return project.name, tasks


@router.post("/summary", response_model=AIResponse)
async def summary(
    body: AISummaryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project_name, tasks = await _project_tasks_context(body.project_id, db, user)
    result = await generate_summary(project_name, tasks, focus=body.focus)
    return AIResponse(result=result)


@router.post("/suggestions", response_model=AIResponse)
async def suggestions(
    body: AISuggestionsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project_name, tasks = await _project_tasks_context(body.project_id, db, user)
    result = await generate_suggestions(project_name, tasks, user_prompt_extra=body.prompt)
    return AIResponse(result=result)


@router.post("/chat", response_model=AIResponse)
async def chat(
    body: AIChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project_name, tasks = await _project_tasks_context(body.project_id, db, user)
    result = await handle_chat_query(project_name, tasks, query=body.message)
    return AIResponse(result=result)
