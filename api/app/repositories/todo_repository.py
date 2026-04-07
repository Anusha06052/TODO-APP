"""Repository for the Todo resource.

Provides all SQLAlchemy async queries for the ``todos`` table.  This layer
has no knowledge of HTTP concerns — it never raises :class:`HTTPException` and
never calls ``session.commit()``.  Committing is the responsibility of the
Service layer.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate

logger = logging.getLogger(__name__)


class TodoRepository:
    """Data-access layer for the ``todos`` table.

    All methods are ``async`` and operate through a single
    :class:`~sqlalchemy.ext.asyncio.AsyncSession` that is injected at
    construction time via FastAPI's dependency injection system.

    Attributes:
        db: The async database session used for all queries in this instance.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialise the repository with an async database session.

        Args:
            db: An :class:`~sqlalchemy.ext.asyncio.AsyncSession` provided by
                the ``get_db`` dependency.
        """
        self.db = db

    async def get_all(self) -> list[Todo]:
        """Retrieve every todo ordered by creation date (newest first).

        Returns:
            A list of :class:`~app.models.todo.Todo` ORM instances ordered by
            ``created_at`` descending.  Returns an empty list when the table
            is empty.
        """
        result = await self.db.execute(
            select(Todo).options(selectinload(Todo.category)).order_by(Todo.created_at.desc())
        )
        todos = list(result.scalars().all())
        logger.debug("get_all returned %d todo(s)", len(todos))
        return todos

    async def get_by_id(self, todo_id: int) -> Todo | None:
        """Retrieve a single todo by its primary key.

        Args:
            todo_id: The integer primary key of the todo to fetch.

        Returns:
            The matching :class:`~app.models.todo.Todo` instance, or ``None``
            when no row with that ``id`` exists.
        """
        result = await self.db.execute(
            select(Todo).options(selectinload(Todo.category)).where(Todo.id == todo_id)
        )
        todo = result.scalar_one_or_none()
        logger.debug("get_by_id(%d) → %s", todo_id, "found" if todo else "not found")
        return todo

    async def create(self, todo: TodoCreate) -> Todo:
        """Insert a new todo row and return the persisted ORM instance.

        The method flushes the session so that the database assigns the
        auto-incremented ``id`` and server-default timestamps, then refreshes
        the instance to load those values into memory.  ``commit()`` is
        intentionally not called here — the Service layer is responsible for
        committing the transaction.

        Args:
            todo: A validated :class:`~app.schemas.todo.TodoCreate` payload
                containing the fields for the new todo.

        Returns:
            The newly created :class:`~app.models.todo.Todo` ORM instance with
            all server-assigned fields (``id``, ``created_at``, ``updated_at``)
            populated.
        """
        db_todo = Todo(
            title=todo.title,
            description=todo.description,
            category_id=todo.category_id,
        )
        self.db.add(db_todo)
        # Flush to send the INSERT to the DB and populate server-side defaults
        # (id, created_at, updated_at) without committing the transaction.
        await self.db.flush()
        await self.db.refresh(db_todo, attribute_names=["category"])
        logger.debug("create → new todo id=%d", db_todo.id)
        return db_todo

    async def update(self, todo: Todo, data: TodoUpdate) -> Todo:
        """Apply a partial update to an existing todo ORM instance.

        Only fields that the client explicitly included in the PATCH body are
        written — fields omitted by the client are left unchanged.

        ``model_fields_set`` is a Pydantic v2 attribute that records exactly
        which field names were present in the original input dict.  Iterating
        over it (rather than all fields) ensures that a missing field is treated
        as "do not touch" rather than "set to None", which is critical for
        correct PATCH semantics.

        Args:
            todo: The existing :class:`~app.models.todo.Todo` ORM instance to
                modify.
            data: A validated :class:`~app.schemas.todo.TodoUpdate` payload
                containing only the fields the caller wishes to change.

        Returns:
            The updated :class:`~app.models.todo.Todo` ORM instance with the
            new field values applied and server-side ``updated_at`` refreshed.
        """
        # model_fields_set contains only the field names that were explicitly
        # provided by the caller in the PATCH body — it excludes fields that
        # were left out and received their default value of None.  This is what
        # makes true partial updates possible: we only touch what was sent.
        for field in data.model_fields_set:
            setattr(todo, field, getattr(data, field))

        await self.db.flush()
        await self.db.refresh(todo, attribute_names=["category"])
        logger.debug("update → todo id=%d fields=%s", todo.id, data.model_fields_set)
        return todo

    async def delete(self, todo: Todo) -> None:
        """Delete an existing todo row from the database.

        The row is removed from the session and a ``DELETE`` statement is
        flushed to the database.  The caller (Service layer) must commit the
        transaction for the deletion to be permanent.

        Args:
            todo: The :class:`~app.models.todo.Todo` ORM instance to delete.

        Returns:
            None
        """
        await self.db.delete(todo)
        await self.db.flush()
        logger.debug("delete → todo id=%d removed from session", todo.id)
