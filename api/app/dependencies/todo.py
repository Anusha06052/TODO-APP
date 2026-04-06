"""FastAPI dependency factories for the Todo resource.

This module wires the repository and service layers together via FastAPI's
``Depends()`` system.  Route handlers should import from here — never
instantiate repositories or services manually.

Dependency chain::

    get_db() → AsyncSession
        ↓
    get_todo_repository(session) → TodoRepository
        ↓
    get_todo_service(repository, session) → TodoService
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.todo_repository import TodoRepository
from app.services.todo_service import TodoService


async def get_todo_repository(
    session: AsyncSession = Depends(get_db),
) -> TodoRepository:
    """Construct a :class:`~app.repositories.todo_repository.TodoRepository`.

    Args:
        session: An async database session provided by :func:`~app.db.session.get_db`.

    Returns:
        A :class:`~app.repositories.todo_repository.TodoRepository` bound to
        the current request's database session.
    """
    return TodoRepository(session)


async def get_todo_service(
    repository: TodoRepository = Depends(get_todo_repository),
) -> TodoService:
    """Construct a :class:`~app.services.todo_service.TodoService`.

    Intended for use with ``Depends()`` in route handlers::

        async def list_todos(
            service: Annotated[TodoService, Depends(get_todo_service)],
        ) -> list[TodoResponse]: ...

    Args:
        repository: A :class:`~app.repositories.todo_repository.TodoRepository`
            provided by :func:`get_todo_repository`.

    Returns:
        A fully configured :class:`~app.services.todo_service.TodoService`.
    """
    return TodoService(repository)
