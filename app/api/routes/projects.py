import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Project, User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.project_importer import import_file

router = APIRouter(prefix="/projects", tags=["projects"])


# ---- helpers ----

async def _get_project_or_404(
    project_id: uuid.UUID, db: AsyncSession, user: User
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---- CRUD ----

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = Project(**body.model_dump(), owner_id=user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _get_project_or_404(project_id, db, user)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await _get_project_or_404(project_id, db, user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await _get_project_or_404(project_id, db, user)
    await db.delete(project)
    await db.commit()


# ---- Import ----

@router.post("/import", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def import_project(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed = (".csv", ".xlsx", ".xls")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail=f"File must be one of: {', '.join(allowed)}")

    try:
        project = await import_file(file.file, file.filename, user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return project
