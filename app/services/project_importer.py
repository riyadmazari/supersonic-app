"""
Import a project plan from an uploaded Excel (.xlsx) or CSV file.

Expected columns (case-insensitive, leading/trailing spaces stripped):
    Project Name  – used for the project name (taken from the first row)
    Task Name     – required
    Owner         – optional, maps to Task.assignee
    Start Date    – optional, ISO or common date formats
    End Date      – optional
    Status        – optional (not_started | in_progress | completed | blocked)
    Priority      – optional (low | medium | high | critical)
    Description   – optional
"""

from __future__ import annotations

import io
import uuid
from typing import BinaryIO

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Task

VALID_STATUSES = {"not_started", "in_progress", "completed", "blocked"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip column names so matching is forgiving."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _parse_status(raw: str | None) -> str:
    if raw and str(raw).strip().lower().replace(" ", "_") in VALID_STATUSES:
        return str(raw).strip().lower().replace(" ", "_")
    return "not_started"


def _parse_priority(raw: str | None) -> str:
    if raw and str(raw).strip().lower() in VALID_PRIORITIES:
        return str(raw).strip().lower()
    return "medium"


async def import_file(
    file: BinaryIO,
    filename: str,
    owner_id: uuid.UUID,
    db: AsyncSession,
) -> Project:
    """Parse the uploaded file and persist a Project with its Tasks."""

    content = file.read()
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))

    df = _normalise_columns(df)

    if "task_name" not in df.columns:
        raise ValueError("File must contain a 'Task Name' column.")

    # Derive project name from a 'project_name' column or from the filename
    project_name = "Imported Project"
    if "project_name" in df.columns:
        first_val = df["project_name"].dropna()
        if not first_val.empty:
            project_name = str(first_val.iloc[0]).strip()
    else:
        project_name = filename.rsplit(".", 1)[0]

    project = Project(id=uuid.uuid4(), name=project_name, owner_id=owner_id)
    db.add(project)

    for _, row in df.iterrows():
        task_title = str(row.get("task_name", "")).strip()
        if not task_title:
            continue

        task = Task(
            id=uuid.uuid4(),
            project_id=project.id,
            title=task_title,
            description=str(row["description"]).strip() if pd.notna(row.get("description")) else None,
            assignee=str(row["owner"]).strip() if pd.notna(row.get("owner")) else None,
            status=_parse_status(row.get("status")),
            priority=_parse_priority(row.get("priority")),
            start_date=pd.to_datetime(row.get("start_date"), errors="coerce"),
            end_date=pd.to_datetime(row.get("end_date"), errors="coerce"),
        )
        db.add(task)

    await db.commit()
    await db.refresh(project)
    return project
