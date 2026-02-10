from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import ai, auth, messages, policy, projects, tasks
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (replace with Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Supersonic – AI Project Planner",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(messages.router)
app.include_router(ai.router)
app.include_router(policy.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
