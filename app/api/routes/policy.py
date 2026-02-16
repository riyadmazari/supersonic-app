from fastapi import APIRouter

router = APIRouter(tags=["policy"])

POLICY = {
    "data_handling": (
        "All data submitted to this system is stored in the application database "
        "and used solely for project-planning purposes within the authenticated "
        "user's scope. Data is not shared with third parties."
    ),
    "ai_limitations": (
        "AI-generated outputs (summaries, suggestions) are produced by a language "
        "model and may contain inaccuracies, omissions, or hallucinations. Users "
        "must verify all AI recommendations before making decisions. The system "
        "provides no guarantees of correctness."
    ),
    "legal_and_ethics": (
        "This tool is provided as-is for project-planning assistance. Users are "
        "responsible for ensuring that their use complies with applicable laws and "
        "institutional policies. Content that may trigger mandatory reporting "
        "obligations (e.g., safety concerns) should be directed to the appropriate "
        "authorities, not entered into this system."
    ),
    "security": (
        "Authentication is enforced on all data-access endpoints. Passwords are "
        "hashed with bcrypt and never stored in plaintext. The database is "
        "accessed through a dedicated non-root service account."
    ),
}


@router.get("/policy")
async def get_policy():
    return POLICY
