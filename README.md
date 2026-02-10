# Supersonic — AI-Assisted Project Planner

An AI-assisted project planning tool that lets teams import project plans from Excel/CSV, manage tasks and milestones through a REST API, and interact with an AI assistant for summaries, risk analysis, and schedule suggestions.

Built with **FastAPI**, **PostgreSQL**, and **Docker**.

## Features

- **Project plan import** — Upload `.csv` or `.xlsx` files to create a project with tasks in one step
- **Project & task management** — Full CRUD with filtering by status, priority, and date range
- **AI assistant** — Endpoints for project summaries and schedule/priority suggestions (pluggable LLM backend, stub included)
- **Email/note linking** — Message objects that can be linked to projects or individual tasks (designed for future Outlook/Graph API integration)
- **Authentication** — JWT Bearer token auth with bcrypt password hashing
- **Ethics & policy** — Built-in endpoint documenting data handling, AI limitations, and legal disclaimers

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Docker Network                     │
│                                                      │
│  ┌──────────────────────┐   ┌─────────────────────┐ │
│  │  backend (port 8000) │   │  db (port 5432)     │ │
│  │                      │   │                     │ │
│  │  FastAPI app         │──▶│  PostgreSQL 16      │ │
│  │  - REST/JSON API     │   │  - supersonic_db    │ │
│  │  - JWT auth          │   │  - non-root user    │ │
│  │  - AI service stub   │   │                     │ │
│  │  - File import       │   └─────────────────────┘ │
│  └──────────┬───────────┘                            │
│             │                                        │
│        port 8000                                     │
│        exposed                                       │
└─────────────┼───────────────────────────────────────┘
              │
         HTTP/JSON
              │
     ┌────────▼────────┐
     │  Client / User  │
     │  (curl, browser, │
     │   Postman, etc.) │
     └─────────────────┘
```

| Component | Technology | Role |
|---|---|---|
| Backend API | FastAPI + Uvicorn | REST/JSON endpoints, auth, file parsing, AI orchestration |
| Database | PostgreSQL 16 | Persistent storage for users, projects, tasks, messages |
| ORM | SQLAlchemy 2.0 (async) | Data models, async DB access via asyncpg |
| Auth | python-jose + passlib | JWT token issuance/verification, bcrypt password hashing |
| File import | pandas + openpyxl | Parses CSV and Excel uploads into structured project data |
| AI service | Pluggable `ai_client` | Stub included; swap in OpenAI/Anthropic/local LLM later |
| Deployment | Docker Compose | Two-container setup (backend + postgres) on a shared network |

## Data Model

```
User ──1:N──▶ Project ──1:N──▶ Task ◀──N:M──▶ Tag
                 │                │
                 └──1:N──▶ Message (optionally linked to a Task)
```

- **User** — username, hashed password, full name
- **Project** — name, description, owner
- **Task** — title, status, priority, assignee, start/end dates
- **Message** — subject, body, sender, date (email/note-like, linked to project and optionally to a task)
- **Tag** — labels for tasks (many-to-many)

## API Endpoints

| Group | Endpoints | Auth |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | public (register/login) |
| Projects | `POST /projects`, `GET /projects`, `GET/PUT/DELETE /projects/{id}` | Bearer token |
| Import | `POST /projects/import` (multipart file upload) | Bearer token |
| Tasks | `POST/GET /projects/{id}/tasks`, `GET/PUT/DELETE /tasks/{id}` | Bearer token |
| Messages | `POST/GET /projects/{id}/messages` | Bearer token |
| AI | `POST /ai/summary`, `POST /ai/suggestions` | Bearer token |
| Policy | `GET /policy` | public |
| Health | `GET /health` | public |

Full interactive docs available at `/docs` (Swagger UI) when the server is running.

## Project Structure

```
app/
├── main.py                  # FastAPI app, router registration, DB init
├── api/
│   ├── deps.py              # get_db, get_current_user dependencies
│   └── routes/
│       ├── auth.py           # register, login, me
│       ├── projects.py       # CRUD + import
│       ├── tasks.py          # CRUD with filtering
│       ├── messages.py       # create, list
│       ├── ai.py             # summary, suggestions
│       └── policy.py         # ethics/security policy
├── core/
│   ├── config.py            # pydantic Settings (reads .env)
│   └── security.py          # password hashing, JWT
├── db/
│   ├── base.py              # SQLAlchemy declarative base
│   ├── models.py            # User, Project, Task, Tag, Message
│   └── session.py           # async engine + session factory
├── schemas/                 # Pydantic request/response models
└── services/
    ├── ai_client.py         # pluggable AI interface (stub)
    └── project_importer.py  # Excel/CSV parser
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/em-ech/supersonic.git
cd supersonic

# 2. Create your environment file
cp .env.example .env

# 3. Build and run
docker compose up --build

# 4. Open the API docs
# http://localhost:8000/docs
```

## Environment Variables

See `.env.example` for all available configuration:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://supersonic_user:supersonic_pass@db:5432/supersonic_db` |
| `SECRET_KEY` | JWT signing key (change in production) | `change-me-to-a-random-secret` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `AI_API_BASE_URL` | AI provider base URL (for future use) | `http://localhost:8000/ai` |
| `AI_API_KEY` | AI provider API key (for future use) | `not-needed-for-stub` |

## Security

- Passwords hashed with **bcrypt** (never stored in plaintext)
- All data endpoints require **JWT Bearer token** authentication
- PostgreSQL accessed via a **dedicated non-root user** (`supersonic_user`)
- AI responses include a **disclaimer** about potential hallucinations
