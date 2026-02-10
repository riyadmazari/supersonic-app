"""
Pluggable AI client.

The public functions `generate_summary` and `generate_suggestions` accept
project context (serialised task data) and return natural-language text.

Currently backed by a deterministic stub.  To integrate a real LLM later,
replace the body of `_call_llm` — no changes needed in routes or schemas.
"""

from __future__ import annotations

import datetime
from typing import Any


# ---- internal helper (swap this for a real API call) ----

async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Stub: returns a canned response.  Replace with an HTTP call to
    OpenAI / Anthropic / a local model when ready."""
    return (
        f"[AI stub response]\n\n"
        f"System context: {system_prompt[:120]}...\n"
        f"User query: {user_prompt[:120]}...\n\n"
        "This is a placeholder.  Connect a real LLM provider in "
        "app/services/ai_client.py to get actual suggestions."
    )


# ---- helpers to build context from task data ----

def _tasks_to_text(tasks: list[dict[str, Any]]) -> str:
    if not tasks:
        return "No tasks found for this project."
    lines: list[str] = []
    for t in tasks:
        end = t.get("end_date")
        end_str = end.isoformat() if isinstance(end, datetime.datetime) else str(end) if end else "no deadline"
        lines.append(
            f"- {t['title']} | status={t['status']} priority={t['priority']} "
            f"assignee={t.get('assignee', 'unassigned')} due={end_str}"
        )
    return "\n".join(lines)


# ---- public API ----

async def generate_summary(
    project_name: str,
    tasks: list[dict[str, Any]],
    focus: str | None = None,
) -> str:
    system_prompt = (
        "You are a project-management assistant.  Summarise the project "
        "status, upcoming deadlines, and potential risks."
    )
    focus_text = f"  Focus on: {focus}." if focus else ""
    user_prompt = (
        f"Project: {project_name}\n"
        f"Tasks:\n{_tasks_to_text(tasks)}\n\n"
        f"Provide a concise summary.{focus_text}"
    )
    return await _call_llm(system_prompt, user_prompt)


async def generate_suggestions(
    project_name: str,
    tasks: list[dict[str, Any]],
    user_prompt_extra: str | None = None,
) -> str:
    system_prompt = (
        "You are a project-management assistant.  Suggest concrete "
        "improvements to the schedule, priorities, or workload distribution."
    )
    extra = f"\nUser request: {user_prompt_extra}" if user_prompt_extra else ""
    user_prompt = (
        f"Project: {project_name}\n"
        f"Tasks:\n{_tasks_to_text(tasks)}\n\n"
        f"Suggest improvements.{extra}"
    )
    return await _call_llm(system_prompt, user_prompt)
