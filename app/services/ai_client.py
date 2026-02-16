"""
Pluggable AI client.

The public functions `generate_summary` and `generate_suggestions` accept
project context (serialised task data) and return natural-language text.

Currently backed by intelligent logic-based analysis. To integrate a real LLM later,
replace the body of `_call_llm` — no changes needed in routes or schemas.
"""

import datetime
import os
import re
from typing import Any

import google.generativeai as genai

from app.core.config import settings

# Initialize Gemini Client
genai.configure(api_key=settings.GEMINI_API_KEY)
# We choose gemini-2.0-flash for speed and project efficiency
model_base = genai.GenerativeModel('gemini-2.0-flash')


# ---- internal helper (intelligent analysis) ----

def _analyze_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze tasks and return useful metrics."""
    if not tasks:
        return {
            "total": 0,
            "by_status": {},
            "by_priority": {},
            "overdue": [],
            "completion_rate": 0,
            "unassigned": [],
            "risk_score": 0,
            "high_risk_tasks": [],
            "project_health": "N/A"
        }
    
    by_status = {}
    by_priority = {}
    overdue = []
    looming = []
    unassigned = []
    missing_dates = []
    sparse_descriptions = []
    
    total_risk = 0
    high_risk_tasks = []
    urgent_keywords = ["urgent", "fix", "critical", "broken", "hotfix", "important", "emergency"]
    
    today = datetime.datetime.now(datetime.timezone.utc)
    two_days_later = today + datetime.timedelta(days=2)
    
    for task in tasks:
        status = task.get('status', 'not_started')
        priority = task.get('priority', 'medium')
        
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Risk profiling
        task_risk = 0
        prio_weight = {'critical': 10, 'high': 7, 'medium': 4, 'low': 2}.get(priority, 4)
        task_risk += prio_weight
        
        end_date = task.get('end_date')
        if end_date and isinstance(end_date, datetime.datetime):
            days_left = (end_date - today).days
            if status != 'completed':
                if days_left < 0:
                    task_risk += 15
                    overdue.append(task)
                elif days_left < 2:
                    task_risk += 10
                    looming.append(task)
                elif days_left < 7:
                    task_risk += 5
        elif status == 'in_progress' and status != 'completed':
            missing_dates.append(task)
            task_risk += 3
        
        # Keyword sensitivity
        title_lower = str(task.get('title', '')).lower()
        if any(kw in title_lower for kw in urgent_keywords):
            task_risk += 5
            
        if not task.get('assignee'):
            unassigned.append(task)
            task_risk += 2

        desc = task.get('description', '') or ''
        if len(desc.strip()) < 10 and status != 'completed':
            sparse_descriptions.append(task)
            task_risk += 1

        if status == 'completed':
            task_risk = 0 # Completed tasks carry no risk
            
        if task_risk >= 15:
            high_risk_tasks.append({**task, 'risk_score': task_risk})
            
        total_risk += task_risk
    
    completion_rate = (by_status.get('completed', 0) / len(tasks) * 100)
    avg_risk = total_risk / len(tasks)
    
    return {
        "total": len(tasks),
        "by_status": by_status,
        "by_priority": by_priority,
        "overdue": overdue,
        "looming": looming,
        "completion_rate": completion_rate,
        "unassigned": unassigned,
        "missing_dates": missing_dates,
        "sparse_descriptions": sparse_descriptions,
        "risk_score": total_risk,
        "avg_risk": avg_risk,
        "high_risk_tasks": high_risk_tasks,
        "project_health": _get_risk_level(avg_risk)
    }


def _get_risk_level(score: float) -> str:
    """Return a unified risk label based on score."""
    if score < 5: return "Excellent"
    if score < 10: return "Good"
    if score < 15: return "Fair"
    if score < 20: return "Concern"
    return "Critical"


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


def _get_risk_legend() -> str:
    """Return a legend explaining the risk scoring system."""
    return (
        "## ℹ️ Risk Scoring Legend\n"
        "Your project health is calculated using a weighted risk score per task:\n"
        "- **Base Priority:** Critical (+10), High (+7), Medium (+4), Low (+2)\n"
        "- **Deadlines:** Overdue (+15), Due < 48h (+10), Due < 7 days (+5)\n"
        "- **Keywords:** 'Urgent', 'Fix', 'Broken' in title (+5)\n"
        "- **Maintenance:** Missing dates (+3), Unassigned (+2), Short description (+1)\n"
        "\n"
        "**Health Ranges (Avg Score):**\n"
        "🟢 0-5: Excellent | 🟡 5-10: Good | 🟠 10-15: Fair | 🔴 15-20: Concern | 💀 20+: Critical"
    )


# ---- Gemini Integration helper ----

async def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Central helper to call the Google Gemini API."""
    try:
        # Create a model instance with system instructions
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_prompt
        )
        response = await model.generate_content_async(user_prompt)
        return response.text or "No response from AI."
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"Error: Unable to reach the Gemini assistant. (Details: {str(e)})"


# ---- public API ----

async def generate_summary(
    project_name: str,
    tasks: list[dict[str, Any]],
    focus: str | None = None,
) -> str:
    """Generate an intelligent project summary with metrics and insights using OpenAI."""
    
    analysis = _analyze_tasks(tasks)
    
    # We combine structured data with LLM narrative
    prompt = f"""
    Analyze the project '{project_name}' based on the following task data and metrics:
    Metrics: {analysis}
    Tasks Overview:
    {_tasks_to_text(tasks)}
    
    Focus Area: {focus or 'General project health and risk assessment'}
    
    Requirements:
    1. Provide a professional, concise summary.
    2. Use the following metrics in your analysis: Project Health is '{analysis['project_health']}', Completion Rate is {analysis['completion_rate']:.1f}%.
    3. Specifically mention the top high-risk tasks if any.
    4. Format the output with clear Markdown headers and bullet points.
    5. Be actionable and supportive.
    6. Always end with the Risk Scoring Legend provided in context.
    
    Scoring Legend Context:
    {_get_risk_legend()}
    """
    
    system_prompt = "You are an expert Project Management assistant. You provide high-level summaries and risk assessments."
    return await _call_gemini(system_prompt, prompt)


async def generate_suggestions(
    project_name: str,
    tasks: list[dict[str, Any]],
    user_prompt_extra: str | None = None,
) -> str:
    """Generate actionable suggestions for project improvement."""
    
    analysis = _analyze_tasks(tasks)
    
    prompt = f"""
    Provide 3-5 actionable suggestions to improve the project '{project_name}'.
    Metrics: {analysis}
    Task List Context:
    {_tasks_to_text(tasks)}
    
    Additional User Prompt: {user_prompt_extra or 'None'}
    
    Requirements:
    1. Be specific. Reference actual task titles.
    2. Focus on risk mitigation, resource allocation (unassigned tasks), and deadline management.
    3. Use a helpful, encouraging tone.
    4. Format as a numbered list with bold headings.
    """
    
    system_prompt = "You are a senior project advisor. You provide tactical advice to keep projects on track."
    return await _call_gemini(system_prompt, prompt)


async def handle_chat_query(
    project_name: str,
    tasks: list[dict[str, Any]],
    query: str,
) -> str:
    """Handle a user chat query based on project context."""
    analysis = _analyze_tasks(tasks)
    
    prompt = f"""
    The user is asking: "{query}" 
    
    Project Context for '{project_name}':
    - Health: {analysis['project_health']}
    - Completion Rate: {analysis['completion_rate']:.1f}%
    - Total Tasks: {analysis['total']}
    - Overdue: {len(analysis['overdue'])}
    - Unassigned: {len(analysis['unassigned'])}
    
    Detailed Analysis: {analysis}
    Full Task List:
    {_tasks_to_text(tasks)}
    
    Requirements:
    1. Answer the user's query directly based on the provided project data.
    2. Be conversational but concise.
    3. Use Markdown (bolding, lists) to emphasize important details.
    4. If the user asks for a 'roadmap' or 'plan', provide a clear sequence of next steps based on high priority and overdue tasks.
    5. Always use the risk levels (Excellent, Good, Fair, Concern, Critical) when discussing project health.
    """
    
    system_prompt = f"You are the 'Supersonic Project Assistant' for the project '{project_name}'. You have full visibility into the project's tasks and health metrics. Always refer to yourself as the project assistant."
    return await _call_gemini(system_prompt, prompt)
