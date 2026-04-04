"""Business logic layer for the Todo resource.

This module contains :class:`TodoService`, which enforces all domain rules for
Todo operations, and the FastAPI dependency function :func:`get_todo_service`
used to wire everything together via ``Depends()``.

Layer responsibilities:
- Validate business rules (e.g. raise 404 when a todo does not exist).
- Delegate all database access to :class:`~app.repositories.TodoRepository`.
- Own the transaction boundary: call ``commit()`` after every successful write.
- Never execute raw SQL — that belongs in the repository.
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.todo import Todo
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import TodoCreate, TodoUpdate

logger = logging.getLogger(__name__)


class TodoService:
    """Orchestrates all business operations for the Todo resource.

    Sits between the HTTP route layer and the repository layer.  All public
    methods enforce domain rules before delegating to
    :class:`~app.repositories.TodoRepository` for database access.

    Attributes:
        repo: The repository instance used for all database operations.
    """

    def __init__(self, repo: TodoRepository) -> None:
        """Initialise the service with a TodoRepository instance.

        Args:
            repo: A :class:`~app.repositories.TodoRepository` bound to an
                active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
        """
        self.repo = repo

    async def get_all_todos(self) -> list[Todo]:
        """Return every todo in the database, newest first.

        Args:
            None

        Returns:
            A list of :class:`~app.models.todo.Todo` ORM instances ordered by
            ``created_at`` descending.  Returns an empty list when no todos
            exist.
        """
        todos = await self.repo.get_all()
        logger.info("get_all_todos returned %d todo(s)", len(todos))
        return todos

    async def get_todo_by_id(self, todo_id: int) -> Todo:
        """Fetch a single todo by its primary key.

        Args:
            todo_id: The integer primary key of the todo to retrieve.

        Returns:
            The matching :class:`~app.models.todo.Todo` ORM instance.

        Raises:
            HTTPException: 404 if no todo with ``todo_id`` exists.
        """
        todo = await self.repo.get_by_id(todo_id)
        if todo is None:
            logger.warning("get_todo_by_id: todo id=%d not found", todo_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo with id {todo_id} not found",
            )
        logger.info("get_todo_by_id: todo id=%d found", todo_id)
        return todo

    async def create_todo(self, data: TodoCreate) -> Todo:
        """Create a new todo and persist it to the database.

        Args:
            data: A validated :class:`~app.schemas.todo.TodoCreate` payload
                with the title and optional description for the new todo.

        Returns:
            The newly created :class:`~app.models.todo.Todo` ORM instance with
            all server-assigned fields (``id``, ``created_at``, ``updated_at``)
            populated.
        """
        todo = await self.repo.create(data)
        await self.repo.db.commit()
        await self.repo.db.refresh(todo)
        logger.info("create_todo: created todo id=%d", todo.id)
        return todo

    async def update_todo(self, todo_id: int, data: TodoUpdate) -> Todo:
        """Apply a partial update to an existing todo.

        First fetches the todo (raising 404 if absent), then delegates the
        field-level update to the repository.  Only the fields explicitly
        included in the PATCH body are modified.

        Args:
            todo_id: The primary key of the todo to update.
            data: A validated :class:`~app.schemas.todo.TodoUpdate` payload
                containing only the fields the caller wishes to change.

        Returns:
            The updated :class:`~app.models.todo.Todo` ORM instance with the
            new field values and a refreshed ``updated_at`` timestamp.

        Raises:
            HTTPException: 404 if no todo with ``todo_id`` exists.
        """
        todo = await self.get_todo_by_id(todo_id)
        todo = await self.repo.update(todo, data)
        await self.repo.db.commit()
        await self.repo.db.refresh(todo)
        logger.info("update_todo: updated todo id=%d fields=%s", todo_id, data.model_fields_set)
        return todo

    async def delete_todo(self, todo_id: int) -> None:
        """Delete an existing todo from the database.

        First fetches the todo (raising 404 if absent), then delegates the
        deletion to the repository and commits the transaction.

        Args:
            todo_id: The primary key of the todo to delete.

        Returns:
            None

        Raises:
            HTTPException: 404 if no todo with ``todo_id`` exists.
        """
        todo = await self.get_todo_by_id(todo_id)
        await self.repo.delete(todo)
        await self.repo.db.commit()
        logger.info("delete_todo: deleted todo id=%d", todo_id)


async def get_todo_service(
    db: AsyncSession = Depends(get_db),
) -> TodoService:
    """FastAPI dependency that wires ``TodoRepository`` and ``TodoService``.

    Constructs a :class:`TodoRepository` from the injected
    :class:`~sqlalchemy.ext.asyncio.AsyncSession`, then wraps it in a
    :class:`TodoService`.  Intended for use with ``Depends()`` in route
    handlers::

        async def list_todos(
            service: Annotated[TodoService, Depends(get_todo_service)],
        ) -> list[TodoResponse]: ...

    Args:
        db: An async database session provided by :func:`~app.db.session.get_db`.

    Returns:
        A fully configured :class:`TodoService` instance.
    """
    return TodoService(TodoRepository(db))
