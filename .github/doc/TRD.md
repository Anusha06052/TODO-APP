# TRD 

**Status:** Draft  
**Date:** 2026-04-01  
**Author:** GitHub Copilot (generated via generate-trd.prompt.md)  
**PRD Reference:** [PRD-ai-task-suggestions.md](./PRD-ai-task-suggestions.md)

---

## Feature Summary

Add an AI-powered suggestion flow that accepts a plain-text goal from the user, calls
an external AI provider (OpenAI), and returns a structured list of tasks and subtasks
with priorities. The user reviews, optionally edits, selects, and saves chosen suggestions
as real Todo records. The suggestion session lives only for the duration of the review
interaction and is soft-deleted on accept or dismiss.

**Tech stack additions:**
- Backend: `openai` Python SDK, `python-dotenv` (already in use), new DB tables.
- Frontend: new page, new components, new hook, new service module.

---

## Database Changes

### New Tables

#### `suggestion_sessions`

| Column | Type | Constraints |
|---|---|---|
| `id` | INT IDENTITY | PK |
| `goal_text` | NVARCHAR(500) | NOT NULL |
| `status` | NVARCHAR(20) | NOT NULL, DEFAULT `'pending'` — values: `pending`, `completed`, `failed` |
| `created_at` | DATETIME2 | NOT NULL, DEFAULT `GETUTCDATE()` |

#### `suggested_tasks`

| Column | Type | Constraints |
|---|---|---|
| `id` | INT IDENTITY | PK |
| `session_id` | INT | FK → `suggestion_sessions.id` ON DELETE CASCADE, NOT NULL |
| `title` | NVARCHAR(255) | NOT NULL |
| `description` | NVARCHAR(1000) | NULL |
| `priority` | NVARCHAR(10) | NOT NULL, DEFAULT `'medium'` — values: `high`, `medium`, `low` |
| `parent_task_id` | INT | FK → `suggested_tasks.id`, NULL (top-level if NULL) |
| `position` | INT | NOT NULL, DEFAULT `0` |
| `is_selected` | BIT | NOT NULL, DEFAULT `1` |

### Existing Tables Modified

None. The existing `todos` table is unchanged at the schema level.  
> **Note:** If the `todos` table does not yet have a `priority` column, add one.
> Coordinate with the team before combining this migration with the
> `ai-task-suggestions` migration.

### Alembic Migration

```bash
# From /api directory
alembic revision --autogenerate -m "add_suggestion_session_and_suggested_task_tables"
alembic upgrade head
```

---

## API Contract

| Method | Path | Request Body | Response Body | Status Codes |
|---|---|---|---|---|
| POST | `/api/v1/suggestions` | `SuggestionCreate` | `SuggestionSessionResponse` | 201, 422 |
| GET | `/api/v1/suggestions/{session_id}` | — | `SuggestionSessionResponse` | 200, 404 |
| PATCH | `/api/v1/suggestions/{session_id}/tasks/{task_id}` | `SuggestedTaskUpdate` | `SuggestedTaskResponse` | 200, 404 |
| POST | `/api/v1/suggestions/{session_id}/accept` | — | `list[TodoResponse]` | 201, 404, 409 |
| DELETE | `/api/v1/suggestions/{session_id}` | — | — | 204, 404 |

### Schema Definitions

```
SuggestionCreate       { goal: str (5–500) }
SuggestionSessionResponse {
  id, goal_text, status, created_at,
  tasks: list[SuggestedTaskResponse]
}
SuggestedTaskResponse  { id, session_id, title, description, priority, parent_task_id, position, is_selected }
SuggestedTaskUpdate    { title?, description?, priority?, is_selected? }
```

---

## Backend Implementation

### Generation Order: Models → Schemas → AI Client → Repository → Service → Routes

---

### 1. Models — `api/app/models/suggestion.py` *(create)*

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from app.db.base import Base  # shared DeclarativeBase

class SuggestionSession(Base):
    __tablename__ = "suggestion_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    goal_text: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tasks: Mapped[list["SuggestedTask"]] = relationship(
        "SuggestedTask",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SuggestedTask.position",
    )

class SuggestedTask(Base):
    __tablename__ = "suggested_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("suggestion_sessions.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    parent_task_id: Mapped[int | None] = mapped_column(ForeignKey("suggested_tasks.id"), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    session: Mapped["SuggestionSession"] = relationship("SuggestionSession", back_populates="tasks")
    subtasks: Mapped[list["SuggestedTask"]] = relationship(
        "SuggestedTask", foreign_keys=[parent_task_id]
    )
```

*Register in `api/app/models/__init__.py` so Alembic detects the models.*

---

### 2. Schemas — `api/app/schemas/suggestion.py` *(create)*

```python
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Literal

PriorityLiteral = Literal["high", "medium", "low"]

class SuggestionCreate(BaseModel):
    goal: str = Field(..., min_length=5, max_length=500)

class SuggestedTaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    priority: PriorityLiteral | None = None
    is_selected: bool | None = None

class SuggestedTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    title: str
    description: str | None
    priority: str
    parent_task_id: int | None
    position: int
    is_selected: bool

class SuggestionSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    goal_text: str
    status: str
    created_at: datetime
    tasks: list[SuggestedTaskResponse]
```

---

### 3. AI Client — `api/app/services/ai_client.py` *(create)*

Wraps the OpenAI SDK. Isolated so the provider can be swapped without touching
business logic.

```python
# Dependencies: openai>=1.0.0 — add to api/requirements.txt
import json
import logging
from openai import AsyncOpenAI
from app.core.config import settings  # reads OPENAI_API_KEY from env

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = (
    "You are a productivity assistant. Given a user's goal, return ONLY a JSON array "
    "of task objects. Each object must have: title (string), description (string or null), "
    "priority ('high'|'medium'|'low'), subtasks (array of the same shape, max 1 level deep). "
    "Return between 2 and 10 top-level tasks. No commentary, only JSON."
)

async def generate_task_suggestions(goal: str) -> list[dict]:
    """Call OpenAI to get structured task suggestions for a goal.

    Args:
        goal: Plain-text user goal, 5–500 characters.

    Returns:
        List of raw task dicts from the AI response.

    Raises:
        RuntimeError: If the AI returns an unparseable response.
    """
    response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Goal: {goal}"},
        ],
        max_tokens=1500,
        temperature=0.7,
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else data.get("tasks", [])
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.error("AI response parse failure: %s", raw)
        raise RuntimeError("AI returned an unstructured response.") from exc
```

*Add `OPENAI_API_KEY=` to `api/.env` and `api/.env.example`.*

---

### 4. Repository — `api/app/repositories/suggestion_repository.py` *(create)*

```python
class SuggestionRepository:
    def __init__(self, session: AsyncSession) -> None: ...

    async def create_session(self, goal_text: str) -> SuggestionSession: ...
    async def get_session_by_id(self, session_id: int) -> SuggestionSession | None: ...
    async def update_session_status(self, session: SuggestionSession, status: str) -> SuggestionSession: ...
    async def bulk_create_tasks(self, tasks: list[SuggestedTask]) -> list[SuggestedTask]: ...
    async def get_task_by_id(self, task_id: int) -> SuggestedTask | None: ...
    async def update_task(self, task: SuggestedTask, data: dict) -> SuggestedTask: ...
    async def delete_session(self, session: SuggestionSession) -> None: ...
    async def get_selected_tasks(self, session_id: int) -> list[SuggestedTask]: ...
```

All methods use `select()` / `update()` / `delete()` — no legacy Query API.
No `session.commit()` here — that belongs in the service layer.

---

### 5. Service — `api/app/services/suggestion_service.py` *(create)*

```python
class SuggestionService:
    def __init__(self, repository: SuggestionRepository) -> None: ...

    async def generate(self, payload: SuggestionCreate, db_session: AsyncSession) -> SuggestionSession:
        """Call AI, persist results, return session with tasks.
        Raises HTTPException 502 if AI call fails.
        """

    async def get_session(self, session_id: int) -> SuggestionSession:
        """Return session or raise 404."""

    async def update_task(self, session_id: int, task_id: int, data: SuggestedTaskUpdate) -> SuggestedTask:
        """Validate task belongs to session; apply patch; commit.
        Raises 404 if session or task not found.
        """

    async def accept(self, session_id: int, todo_repository: TodoRepository, db_session: AsyncSession) -> list[Todo]:
        """Convert all is_selected=True tasks to real Todos, delete session.
        Raises 404 if session not found.
        Raises 409 if no tasks are selected.
        """

    async def dismiss(self, session_id: int) -> None:
        """Delete session record. Raises 404 if not found."""
```

Key rule: `session.commit()` is called here after every write. AI client is called
via `await generate_task_suggestions(goal)`.

---

### 6. Routes — `api/app/routes/suggestions.py` *(create)*

```python
router = APIRouter(prefix="/api/v1/suggestions", tags=["suggestions"])

@router.post("", response_model=SuggestionSessionResponse, status_code=201)
async def create_suggestion_session(
    payload: SuggestionCreate,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
) -> SuggestionSessionResponse: ...

@router.get("/{session_id}", response_model=SuggestionSessionResponse)
async def get_suggestion_session(...): ...

@router.patch("/{session_id}/tasks/{task_id}", response_model=SuggestedTaskResponse)
async def update_suggested_task(...): ...

@router.post("/{session_id}/accept", response_model=list[TodoResponse], status_code=201)
async def accept_suggestions(...): ...

@router.delete("/{session_id}", status_code=204)
async def dismiss_suggestions(...): ...
```

Register in `api/app/main.py`:

```python
from app.routes.suggestions import router as suggestions_router
app.include_router(suggestions_router)
```

---

### 7. Dependencies — `api/app/dependencies/suggestion.py` *(create)*

```python
async def get_suggestion_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuggestionRepository:
    return SuggestionRepository(session)

async def get_suggestion_service(
    repository: Annotated[SuggestionRepository, Depends(get_suggestion_repository)],
) -> SuggestionService:
    return SuggestionService(repository)
```

---

### 8. Config — `api/app/core/config.py` *(modify)*

Add:

```python
openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
```

---

## Error Handling Strategy

| Scenario | HTTP Code | Error Detail Message |
|---|---|---|
| Goal text < 5 or > 500 chars | 422 | Auto-generated by Pydantic |
| AI provider network error | 502 | `"AI service is currently unavailable. Please try again."` |
| AI returns unparseable JSON | 502 | `"AI returned an unexpected response format."` |
| Session ID not found | 404 | `"Suggestion session {id} not found."` |
| Task ID not found or belongs to different session | 404 | `"Suggested task {id} not found."` |
| Accept called with zero selected tasks | 409 | `"No tasks are selected. Select at least one task before accepting."` |
| `priority` value not in allowed set | 422 | Auto-generated by Pydantic (`Literal` constraint) |

---

## Frontend Implementation

### Generation Order: Types → Services → Hooks → Components → Pages

---

### 1. Types — `web/src/types/suggestion.ts` *(create)*

```typescript
export type Priority = 'high' | 'medium' | 'low';

export interface SuggestedTask {
  id: number;
  sessionId: number;
  title: string;
  description: string | null;
  priority: Priority;
  parentTaskId: number | null;
  position: number;
  isSelected: boolean;
}

export interface SuggestionSession {
  id: number;
  goalText: string;
  status: 'pending' | 'completed' | 'failed';
  createdAt: string;
  tasks: SuggestedTask[];
}

export interface SuggestionCreate {
  goal: string;
}

export interface SuggestedTaskUpdate {
  title?: string;
  description?: string;
  priority?: Priority;
  isSelected?: boolean;
}
```

Export from `web/src/types/index.ts` barrel file.

---

### 2. Services — `web/src/services/suggestionService.ts` *(create)*

```typescript
import { api } from './api';
import type { SuggestionCreate, SuggestionSession, SuggestedTask, SuggestedTaskUpdate } from '@/types';

export const suggestionService = {
  generate: (data: SuggestionCreate): Promise<SuggestionSession> =>
    api.post('/api/v1/suggestions', data).then(r => r.data),

  getById: (sessionId: number): Promise<SuggestionSession> =>
    api.get(`/api/v1/suggestions/${sessionId}`).then(r => r.data),

  updateTask: (sessionId: number, taskId: number, data: SuggestedTaskUpdate): Promise<SuggestedTask> =>
    api.patch(`/api/v1/suggestions/${sessionId}/tasks/${taskId}`, data).then(r => r.data),

  accept: (sessionId: number): Promise<Todo[]> =>
    api.post(`/api/v1/suggestions/${sessionId}/accept`).then(r => r.data),

  dismiss: (sessionId: number): Promise<void> =>
    api.delete(`/api/v1/suggestions/${sessionId}`).then(() => undefined),
};
```

---

### 3. Hooks — `web/src/hooks/useSuggestions.ts` *(create)*

```typescript
export const useGenerateSuggestions = () => { /* useMutation → suggestionService.generate */ }
export const useSuggestionSession = (sessionId: number | null) => { /* useQuery, enabled: !!sessionId */ }
export const useUpdateSuggestedTask = (sessionId: number) => { /* useMutation + invalidate ['suggestions', sessionId] */ }
export const useAcceptSuggestions = () => { /* useMutation → service.accept + invalidate ['todos'] */ }
export const useDismissSuggestions = () => { /* useMutation → service.dismiss */ }
```

Query keys:
- `['suggestions', sessionId]` — single session
- Invalidate `['todos']` on accept.

---

### 4. Components

#### `web/src/components/SuggestionPanel/GoalInput.tsx` *(create)*

- Controlled `<textarea>` with character count (5–500).
- Calls `onSubmit(goal)` prop.
- Disables input + shows spinner while `isPending` prop is true.
- Renders inline validation error from `error` prop.

#### `web/src/components/SuggestionPanel/SuggestedTaskCard.tsx` *(create)*

- Displays a single `SuggestedTask`.
- Checkbox for `isSelected` → calls `onToggle(taskId, !isSelected)`.
- Inline edit for `title` (click-to-edit pattern).
- Inline edit for `description`.
- Priority badge (colour-coded: red=high, amber=medium, green=low).
- Accepts `onUpdate(taskId, patch)` prop.

#### `web/src/components/SuggestionPanel/SuggestionPanel.tsx` *(create)*

Orchestrates the full suggestion flow:
1. If no active session → renders `<GoalInput>`.
2. On submit → calls `useGenerateSuggestions`, sets `sessionId`.
3. Renders list of `<SuggestedTaskCard>` grouped by parent (subtasks indented).
4. "Add to My Tasks" button — disabled if no tasks are selected; calls `useAcceptSuggestions`.
5. "Dismiss" link — calls `useDismissSuggestions`, resets `sessionId`.
6. Error banner when mutation fails.
7. Loading skeleton while query is in-flight.

#### `web/src/components/SuggestionPanel/SuggestionPanel.module.css` *(create)*

CSS Modules only — no inline styles.

---

### 5. Pages — `web/src/pages/SuggestionsPage.tsx` *(create)*

```tsx
export default function SuggestionsPage() {
  return (
    <main>
      <h1>AI Task Suggestions</h1>
      <SuggestionPanel />
    </main>
  );
}
```

Add route in the router config (e.g., `/suggestions`).

---

## Copilot Agent Mode Prompts

Ordered execution. Run each prompt in sequence; verify the code compiles before proceeding.

1. `@api Create the SQLAlchemy ORM models SuggestionSession and SuggestedTask in api/app/models/suggestion.py following the TRD schema. Use DeclarativeBase from app/db/base.py, Mapped/mapped_column (SQLAlchemy 2.x), and include the cascade delete-orphan relationship from session to tasks and the self-referential subtask relationship.`

2. `@api Create the Pydantic v2 schemas SuggestionCreate, SuggestedTaskUpdate, SuggestedTaskResponse, and SuggestionSessionResponse in api/app/schemas/suggestion.py. Use ConfigDict(from_attributes=True), Field() validation, and a Literal type for priority ('high'|'medium'|'low').`

3. `@api Create the async OpenAI AI client wrapper in api/app/services/ai_client.py. It must expose a single async function generate_task_suggestions(goal: str) -> list[dict] that calls the gpt-4o-mini model with response_format json_object, parses the response, and raises RuntimeError on parse failure. Read the API key from app.core.config.settings.openai_api_key.`

4. `@api Create SuggestionRepository in api/app/repositories/suggestion_repository.py with async methods: create_session, get_session_by_id, update_session_status, bulk_create_tasks, get_task_by_id, update_task, delete_session, get_selected_tasks. Use SQLAlchemy 2.x select/update/delete statements — no Query API. No commit() in the repository.`

5. `@api Create SuggestionService in api/app/services/suggestion_service.py. Implement: generate (calls ai_client, persists session+tasks, commits, returns session), get_session (404 guard), update_task (validate task belongs to session, commit), accept (convert selected tasks to Todo records via TodoRepository, delete session, commit, return todos), dismiss (delete session, commit). Raise HTTPException 502 for AI failures, 404 for not found, 409 if no tasks selected.`

6. `@api Create the FastAPI router in api/app/routes/suggestions.py with five endpoints as defined in the TRD API contract. Use Annotated[SuggestionService, Depends(get_suggestion_service)] for DI. Register the router in api/app/main.py.`

7. `@api Create the DI provider functions get_suggestion_repository and get_suggestion_service in api/app/dependencies/suggestion.py following the same pattern as existing todo dependencies.`

8. `@api Generate and apply an Alembic migration for the suggestion_sessions and suggested_tasks tables: alembic revision --autogenerate -m "add_suggestion_session_and_suggested_task_tables" then alembic upgrade head.`

9. `@web Create the TypeScript types for the suggestion feature in web/src/types/suggestion.ts — interfaces SuggestedTask, SuggestionSession, SuggestionCreate, SuggestedTaskUpdate; type Priority. Export all from web/src/types/index.ts.`

10. `@web Create web/src/services/suggestionService.ts with five Axios functions (generate, getById, updateTask, accept, dismiss) that call the backend API endpoints defined in the TRD. Import the shared Axios instance from @/services/api.ts.`

11. `@web Create web/src/hooks/useSuggestions.ts with five React Query hooks: useGenerateSuggestions (mutation), useSuggestionSession (query, enabled only when sessionId is non-null), useUpdateSuggestedTask (mutation), useAcceptSuggestions (mutation, invalidates ['todos'] on success), useDismissSuggestions (mutation). Query key for a session is ['suggestions', sessionId].`

12. `@web Create the GoalInput component at web/src/components/SuggestionPanel/GoalInput.tsx. It must: render a textarea with 5–500 character validation and a live character counter; accept onSubmit, isPending, and error props; disable the textarea and show a loading spinner when isPending is true; show an error message below the input when error is set. Use CSS Modules only.`

13. `@web Create the SuggestedTaskCard component at web/src/components/SuggestionPanel/SuggestedTaskCard.tsx. It must: show a checkbox that toggles isSelected via onUpdate; support click-to-edit for title and description; show a colour-coded priority badge (high=red, medium=amber, low=green); accept onUpdate(taskId, patch: SuggestedTaskUpdate) as a prop. Use CSS Modules only.`

14. `@web Create the SuggestionPanel orchestration component at web/src/components/SuggestionPanel/SuggestionPanel.tsx. It must: show GoalInput when no active session; render a list of SuggestedTaskCard components (subtasks indented under parent) when a session is active; show "Add to My Tasks" button (disabled when 0 tasks selected); show "Dismiss" link; display an error banner on mutation failure; show a loading skeleton while AI is processing. Use useGenerateSuggestions, useSuggestionSession, useUpdateSuggestedTask, useAcceptSuggestions, and useDismissSuggestions hooks.`

15. `@web Create web/src/pages/SuggestionsPage.tsx as the page-level component that renders SuggestionPanel. Register the route /suggestions in the app router config.`

---

## Testing Plan

### Backend (pytest)

**`api/tests/test_suggestion_repository.py`**
- `test_create_session_returns_session_with_correct_goal_text`
- `test_get_session_by_id_returns_session_when_found`
- `test_get_session_by_id_returns_none_when_not_found`
- `test_bulk_create_tasks_persists_all_tasks_with_correct_session_id`
- `test_get_selected_tasks_returns_only_is_selected_true`
- `test_delete_session_cascades_to_tasks`

**`api/tests/test_suggestion_service.py`**
- `test_generate_creates_session_and_tasks_on_success`
- `test_generate_raises_502_when_ai_client_raises_runtime_error`
- `test_get_session_raises_404_when_session_not_found`
- `test_update_task_raises_404_when_task_not_in_session`
- `test_update_task_patches_fields_and_commits`
- `test_accept_creates_todos_from_selected_tasks_and_deletes_session`
- `test_accept_raises_409_when_no_tasks_selected`
- `test_dismiss_deletes_session`

**`api/tests/test_suggestion_routes.py`** (integration via `httpx.AsyncClient`)
- `test_post_suggestions_returns_201_with_tasks`
- `test_post_suggestions_returns_422_for_short_goal`
- `test_get_suggestion_session_returns_200`
- `test_get_suggestion_session_returns_404_for_unknown_id`
- `test_patch_suggested_task_returns_200`
- `test_post_accept_returns_201_with_todos`
- `test_post_accept_returns_409_when_no_selected_tasks`
- `test_delete_suggestion_session_returns_204`

### Frontend (Vitest + RTL)

**`web/src/components/SuggestionPanel/__tests__/GoalInput.test.tsx`**
- renders textarea and submit button
- disables submit when input is fewer than 5 characters
- shows character count
- shows spinner and disables textarea when isPending is true
- displays error message when error prop is set
- calls onSubmit with trimmed goal on submit

**`web/src/components/SuggestionPanel/__tests__/SuggestedTaskCard.test.tsx`**
- renders title, description, and priority badge
- calls onUpdate with `{ isSelected: false }` when checkbox is unchecked
- enters edit mode when title is clicked
- calls onUpdate with new title on blur
- renders correct badge colour for each priority level

**`web/src/hooks/__tests__/useSuggestions.test.ts`**
- useGenerateSuggestions calls suggestionService.generate and returns session data on success
- useAcceptSuggestions invalidates ['todos'] query on success
- useSuggestionSession is disabled when sessionId is null

---

## Breaking Changes

None. All changes are additive:
- New DB tables only — no existing table modifications.
- New API routes only — no existing endpoint changes.
- New frontend files only — no existing component modifications.

> If the `todos` table does not yet have a `priority` column and one is added to store
> accepted suggestions' priorities, that **is** a breaking schema change and requires a
> coordinated migration with the existing `todos` Alembic history.
