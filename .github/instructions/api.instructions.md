---
applyTo: "api/**/*.py"
---

# Python / FastAPI Language Instructions
# Auto-loaded for all .py files in /api. Layered on top of copilot-instructions.md.

## Async Pattern

- `async def` for ALL route handlers, service methods, and repository methods.
- `await` on every database operation — no sync DB calls in async context.
- Never mix sync and async — no `run_sync()` workarounds.
- Use `asyncio.gather()` for parallel independent async operations.

## Type Hints

- Type-hint every function parameter and return value — no exceptions.
- `Optional[Model]` for lookups that may return `None`.
- `list[Model]` (lowercase) for collections — not `List[Model]`.
- `Annotated[Type, Depends()]` for all dependency injection parameters.
- `|` union syntax allowed (Python 3.10+): `str | None` over `Optional[str]`.

## Dependency Injection

```python
# Route → Service → Repository → Session chain
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_todo_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TodoRepository:
    return TodoRepository(session)

async def get_todo_service(
    repository: Annotated[TodoRepository, Depends(get_todo_repository)],
) -> TodoService:
    return TodoService(repository)

@router.get("/todos")
async def list_todos(
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> list[TodoResponse]:
    return await service.get_all()
```

## Pydantic v2 Schemas

```python
from pydantic import BaseModel, ConfigDict, Field

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_completed: bool | None = None

class TodoResponse(TodoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
```

## SQLAlchemy 2.x Models

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, func

class Base(DeclarativeBase):
    pass

class Todo(Base):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

## Repository Pattern

```python
class TodoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Todo]:
        result = await self.session.execute(select(Todo).order_by(Todo.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, todo_id: int) -> Todo | None:
        result = await self.session.execute(select(Todo).where(Todo.id == todo_id))
        return result.scalars().first()

    async def create(self, data: TodoCreate) -> Todo:
        todo = Todo(**data.model_dump())
        self.session.add(todo)
        await self.session.flush()  # flush to get ID; service commits
        return todo
```

## Service Pattern

```python
class TodoService:
    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    async def get_by_id(self, todo_id: int) -> Todo:
        todo = await self.repository.get_by_id(todo_id)
        if todo is None:
            logger.warning("Todo %s not found", todo_id)
            raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
        return todo

    async def create(self, data: TodoCreate) -> Todo:
        todo = await self.repository.create(data)
        await self.repository.session.commit()
        await self.repository.session.refresh(todo)
        logger.info("Created todo id=%s", todo.id)
        return todo
```

## Error Handling

- Services raise `HTTPException` only — repositories raise plain Python exceptions.
- Always include a `detail` string in `HTTPException`.
- Log before raising: `logger.warning("Todo %s not found", todo_id)`.
- No bare `except:` — always catch specific exceptions.
- Use `409 Conflict` for duplicate/constraint violations.

## Logging

```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.info("Created todo id=%s title=%r", todo.id, todo.title)
logger.warning("Todo %s not found", todo_id)
logger.error("Unexpected error creating todo: %s", exc, exc_info=True)
```

## FastAPI Router Conventions

```python
router = APIRouter(prefix="/api/v1/todos", tags=["todos"])

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a new todo", description="Creates a todo item.")
async def create_todo(payload: TodoCreate, service: Annotated[TodoService, Depends(...)]) -> TodoResponse:
    ...
```

## Alembic

- Every schema change requires a migration — never modify DB manually.
- Migration message describes the change: `"add_category_id_to_todos"`.
- Always implement both `upgrade()` and `downgrade()`.
- For non-null new columns: nullable first → backfill → add constraint (staged).
- Check FK drop order in `downgrade()` — FK must drop before the referenced table.

## Import Order

```python
# 1. Standard library
import logging
from datetime import datetime
from typing import Annotated

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoResponse
```
