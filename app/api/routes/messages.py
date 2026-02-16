import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Message, Project, User
from app.schemas.message import MessageCreate, MessageOut

router = APIRouter(tags=["messages"])


async def _verify_project_access(
    project_id: uuid.UUID, db: AsyncSession, user: User
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post(
    "/projects/{project_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    project_id: uuid.UUID,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _verify_project_access(project_id, db, user)
    message = Message(**body.model_dump(), project_id=project_id)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get("/projects/{project_id}/messages", response_model=list[MessageOut])
async def list_messages(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _verify_project_access(project_id, db, user)
    result = await db.execute(
        select(Message)
        .where(Message.project_id == project_id)
        .order_by(Message.date.desc())
    )
    return result.scalars().all()
