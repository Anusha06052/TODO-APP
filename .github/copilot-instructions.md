# Copilot Workspace Instructions — Todo AI Monorepo
# Always-on. Applies to every file in this workspace before any suggestion.

## Project Overview

Full-stack Todo application. Monorepo with `/api` (FastAPI backend) and `/web`
(React TypeScript frontend). Single-user app — no authentication required.

---

## Backend Architecture — 3-Layer (strictly enforced)

```
HTTP Request
    ↓
Layer 1 — Routes       (app/routes/)       HTTP only. No business logic.
    ↓
Layer 2 — Services     (app/services/)     Business rules only. No SQL.
    ↓
Layer 3 — Repositories (app/repositories/) SQLAlchemy queries only.
    ↓
Database (SQL Server via aioodbc, localhost:1433)
```

### Layer Rules — Non-Negotiable

**Routes (`app/routes/`)**
- Receive HTTP requests, validate via Pydantic schemas, delegate to Service.
- No business logic. No direct DB access. No repository calls.
- Return HTTP responses with correct status codes.

**Services (`app/services/`)**
- All business rules live here. Call Repository layer only.
- Raise `HTTPException` for rule violations (404, 409, etc.).
- Call `session.commit()` after successful write operations.
- No SQLAlchemy queries. No HTTP knowledge beyond `HTTPException`.

**Repositories (`app/repositories/`)**
- All SQLAlchemy queries. Accept `AsyncSession` injected via `Depends()`.
- Return ORM model objects or `None`. Return `list[Model]` for collections.
- No business logic. No `HTTPException`. Raise plain Python exceptions only.

### Dependency Injection Chain

```python
# get_db() yields AsyncSession (db/session.py)
# Repository receives AsyncSession via Depends(get_db)
# Service receives Repository via Depends(get_repository)
# Route receives Service via Depends(get_service)

async def create_todo(
    payload: TodoCreate,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    return await service.create(payload)
```

### Backend Conventions

- **Async everywhere**: `AsyncSession`, `async_sessionmaker`, `create_async_engine`.
- **Dependency injection**: Always `Annotated[Type, Depends()]` — never instantiate manually.
- **Pydantic v2**: `model_config = ConfigDict(from_attributes=True)`. Separate
  schemas for Create, Update, Response. Use `Field()` for validation constraints.
- **SQLAlchemy 2.x**: `DeclarativeBase`, `Mapped[type]`, `mapped_column()`.
  Use `select()` / `update()` / `delete()` — never the legacy Query API.
- **Logging**: `logger = logging.getLogger(__name__)` at module top. Never `print()`.
- **HTTP status codes**: 200 (ok), 201 (created), 204 (deleted), 404 (not found),
  409 (conflict), 422 (validation — auto by FastAPI).
- **Type hints**: Every function parameter and return value. No untyped code.
- **Docstrings**: Google style on all public functions. Include Args, Returns, Raises.
- **Imports**: stdlib → third-party → local. Blank line between groups.
- **Secrets**: Never in code. Always `python-dotenv` + `.env` file.
- **Connection string pattern**:
  `mssql+aioodbc://sa:<password>@localhost:1433/<dbname>?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes`

---

## Frontend Architecture — Layered

```
Pages (src/pages/)          Route-level composition. No inline data fetching.
    ↓
Components (src/components/) Reusable UI. Accept typed props, emit events.
    ↓
Hooks (src/hooks/)           React Query logic. One file per domain.
    ↓
Services (src/services/)     Axios functions. One file per domain.
    ↓
Types (src/types/)           All TypeScript interfaces. One file per domain.
Utils (src/utils/)           Pure helper functions.
```

### Frontend Layer Rules

- Components **never** call Axios directly — always via hooks.
- Hooks **never** import Axios directly — always via service functions.
- Types **never** defined inline in components — always in `src/types/`.
- `src/services/api.ts` — single Axios instance with `baseURL` from env.

### Frontend Conventions

- **Components**: Functional arrow functions only. No class components. No `React.FC`.
- **Props**: Named interfaces in `src/types/`. No inline type definitions.
- **Server state**: React Query (TanStack) for all API data. No `useState + useEffect` for fetching.
- **Mutations**: Always call `queryClient.invalidateQueries()` on success.
- **Query keys**: Arrays, descriptive: `['todos']`, `['todos', todoId]`, `['categories']`.
- **Error/loading**: Every component using `useQuery` must handle `isLoading` and `isError`.
- **Types**: No `any`. Use `unknown` + type narrowing if type is truly dynamic.
- **Exports**: Named exports preferred. Default exports only for page files if router requires.
- **Env vars**: Always `import.meta.env.VITE_*` — never hardcoded base URLs.
- **Styling**: CSS Modules or Tailwind only. No inline `style={{ }}` props.
- **Validation**: Zod for runtime API response validation where data shape is uncertain.

---

## Testing Standards

**Backend (pytest)**
- One test file per module: `test_todo_service.py`, `test_todo_repository.py`.
- Test service and repository layers independently with mocked dependencies.
- Cover: happy path, 404 not found, 409 conflict, empty list, invalid input.
- Use `httpx.AsyncClient` for route/integration tests.
- Naming: `test_<action>_<condition>_<expected_outcome>`.

**Frontend (Vitest + RTL)**
- One test file per component/hook, co-located or in `__tests__/`.
- Mock service functions — never mock React Query internals directly.
- Test user interactions via `userEvent`, not implementation details.
- Use `getByRole`, `getByText` — not test IDs where avoidable.

**General**
- Never modify tests to make them pass — fix the source code instead.
- Every new public function must have at least one test.

---

## Git & Commit Standards

- Feature branches: `feature/<name>`, bug fixes: `fix/<name>`.
- All features merged via Pull Request — never commit directly to `main`.
- Conventional Commits: `feat(api): ...`, `fix(web): ...`, `test(api): ...`,
  `chore(repo): ...`, `docs: ...`, `refactor(api): ...`.
- Run code review prompt before every PR merge.

---

## General Rules

- No secrets or connection strings in any source file. Use environment variables.
- No `# type: ignore` in Python without a written justification comment.
- No `@ts-ignore` in TypeScript without a written justification comment.
- No bare `except:` in Python — always catch specific exceptions.
- No `console.log()` left in TypeScript (except intentional debug with a comment).
- No commented-out code committed to the repo.
- Error handling on every async operation — never silently swallow exceptions.
- No `create_all()` — always use Alembic for all schema changes.
