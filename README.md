# Todo AI — Enterprise Monorepo

A full-stack Todo application built with FastAPI and React, using GitHub Copilot
Agent mode as the primary development tool.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11+, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.x (async), Alembic |
| Database | SQL Server Express (localhost:1433, aioodbc driver) |
| Validation | Pydantic v2 |
| Frontend | React 18, TypeScript (strict), Vite |
| Server State | TanStack React Query v5 |
| HTTP Client | Axios |
| Backend Tests | pytest, pytest-asyncio, httpx |
| Frontend Tests | Vitest, React Testing Library |

## Project Structure

```
Todo_AI/
├── api/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py               # App factory, CORS, router registration
│   │   ├── db/
│   │   │   └── session.py        # Async engine, get_db dependency
│   │   ├── models/
│   │   │   ├── base.py           # DeclarativeBase
│   │   │   ├── todo.py           # Todo ORM model
│   │   │   └── category.py       # Category ORM model
│   │   ├── schemas/
│   │   │   ├── todo.py           # TodoCreate, TodoUpdate, TodoResponse
│   │   │   └── category.py       # CategoryCreate, CategoryUpdate, CategoryResponse
│   │   ├── repositories/         # Layer 3 — SQLAlchemy queries only
│   │   │   ├── todo_repository.py
│   │   │   └── category_repository.py
│   │   ├── services/             # Layer 2 — Business logic only
│   │   │   ├── todo_service.py
│   │   │   └── category_service.py
│   │   └── routes/               # Layer 1 — HTTP only
│   │       ├── todo_router.py
│   │       └── category_router.py
│   ├── alembic/
│   │   ├── versions/             # Migration files
│   │   └── env.py                # Async migration runner
│   ├── tests/
│   │   ├── conftest.py           # Shared fixtures
│   │   ├── test_todo_routes.py
│   │   ├── test_todo_service.py
│   │   ├── test_todo_repository.py
│   │   ├── test_category_routes.py
│   │   ├── test_category_service.py
│   │   └── test_category_repository.py
│   ├── alembic.ini
│   ├── .env.example
│   └── requirements.txt
│
├── web/                          # React TypeScript frontend
│   ├── src/
│   │   ├── pages/                # Route-level composition
│   │   │   └── HomePage.tsx
│   │   ├── components/           # Reusable UI components
│   │   │   ├── TodoItem.tsx
│   │   │   ├── TodoItem.test.tsx
│   │   │   ├── TodoForm.tsx
│   │   │   ├── TodoForm.test.tsx
│   │   │   ├── TodoList.tsx
│   │   │   ├── TodoList.test.tsx
│   │   │   ├── CategoryBadge.tsx
│   │   │   └── CategorySelect.tsx
│   │   ├── hooks/                # React Query hooks (one per domain)
│   │   │   ├── useTodos.ts
│   │   │   └── useCategories.ts
│   │   ├── services/             # Axios API client (one per domain)
│   │   │   ├── api.ts            # Axios instance
│   │   │   ├── todoService.ts
│   │   │   └── categoryService.ts
│   │   ├── types/                # TypeScript interfaces (one per domain)
│   │   │   ├── todo.ts
│   │   │   ├── category.ts
│   │   │   └── index.ts          # Barrel export
│   │   ├── utils/                # Pure helper functions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── .env.example
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── .github/
│   ├── copilot-instructions.md   # Workspace-wide always-on rules
│   ├── copilot/
│   │   ├── api-agent.agent.yml   # @api — backend expert agent
│   │   └── web-agent.agent.yml   # @web — frontend expert agent
│   ├── instructions/
│   │   ├── api.instructions.md   # Auto-scoped to api/**/*.py
│   │   └── web.instructions.md   # Auto-scoped to web/src/**/*.{ts,tsx}
│   ├── prompts/
│   │   ├── generate-prd.prompt.md    # #generate-prd
│   │   ├── generate-trd.prompt.md    # #generate-trd
│   │   ├── commit-message.prompt.md  # #commit-message
│   │   ├── pr-review.prompt.md       # #pr-review
│   │   └── db-migration.prompt.md    # #db-migration
│   └── skills/
│       ├── test-generator.skill.yml        # Auto: generate tests
│       ├── test-runner.skill.yml           # Auto: run tests
│       ├── security-review.skill.yml       # Auto: security audit
│       ├── performance-review.skill.yml    # Auto: perf audit
│       ├── db-migration.skill.yml          # Auto: alembic migration
│       └── api-endpoint-generation.skill.yml # Auto: generate endpoints
│
└── docs/
    └── COPILOT_SETUP.md          # Copilot customization reference guide
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (LTS)
- SQL Server Express on localhost:1433
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- VS Code with GitHub Copilot extension (Individual/Pro plan)

## Backend Setup

```bash
cd api

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env: set DATABASE_URL with your SA password

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --host localhost --port 8000
# Swagger: http://localhost:8000/docs
```

## Frontend Setup

```bash
cd web
npm install
cp .env.example .env
# Edit .env: VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev
# App: http://localhost:5173
```

## Running Tests

```bash
# Backend
cd api && python -m pytest -v --tb=short
cd api && python -m pytest --cov=app --cov-report=term-missing

# Frontend
cd web && npx vitest run
cd web && npx vitest run --coverage
```

## Backend Commands

| Command | Description |
|---|---|
| `uvicorn app.main:app --reload` | Start dev server |
| `alembic revision --autogenerate -m "msg"` | Generate migration |
| `alembic upgrade head` | Apply migrations |
| `alembic downgrade -1` | Roll back one migration |
| `alembic current` | Show current migration |
| `pytest tests/ -v` | Run tests |

## Frontend Commands

| Command | Description |
|---|---|
| `npm run dev` | Start dev server (HMR) |
| `npm run build` | Type-check + build |
| `npm run lint` | Run ESLint |
| `npx vitest run` | Run tests |
| `npx vitest --ui` | Test UI dashboard |

## Environment Variables

### Backend (`api/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | `mssql+aioodbc://sa:<pw>@localhost:1433/tododb?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes` |

### Frontend (`web/.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` |

## Copilot Customization Reference

| Artifact | Path | Type | Activation |
|---|---|---|---|
| Workspace instructions | `.github/copilot-instructions.md` | Instructions | Always-on |
| Python rules | `.github/instructions/api.instructions.md` | Language instructions | Auto on `api/**/*.py` |
| TypeScript rules | `.github/instructions/web.instructions.md` | Language instructions | Auto on `web/src/**/*.{ts,tsx}` |
| API agent | `.github/copilot/api-agent.agent.yml` | Custom agent | `@api` in chat |
| Web agent | `.github/copilot/web-agent.agent.yml` | Custom agent | `@web` in chat |
| PRD generator | `.github/prompts/generate-prd.prompt.md` | Prompt file | `#generate-prd` |
| TRD generator | `.github/prompts/generate-trd.prompt.md` | Prompt file | `#generate-trd` |
| Commit message | `.github/prompts/commit-message.prompt.md` | Prompt file | `#commit-message` |
| PR review | `.github/prompts/pr-review.prompt.md` | Prompt file | `#pr-review` |
| DB migration | `.github/prompts/db-migration.prompt.md` | Prompt file | `#db-migration` |
| Test generator | `.github/skills/test-generator.skill.yml` | Skill | Auto on "generate tests" |
| Test runner | `.github/skills/test-runner.skill.yml` | Skill | Auto on "run tests" |
| Security review | `.github/skills/security-review.skill.yml` | Skill | Auto on "security review" |
| Performance review | `.github/skills/performance-review.skill.yml` | Skill | Auto on "performance review" |
| DB migration | `.github/skills/db-migration.skill.yml` | Skill | Auto on "create migration" |
| Endpoint generation | `.github/skills/api-endpoint-generation.skill.yml` | Skill | Auto on "generate endpoint" |

## Branch Strategy

- `main` — stable, production-ready
- `feature/<n>` — feature development, merged via PR
- `fix/<n>` — bug fixes, merged via PR
- Never commit directly to `main`

## License

For educational and personal use.
