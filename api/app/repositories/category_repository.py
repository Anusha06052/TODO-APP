"""Repository for the Category resource.

Provides all SQLAlchemy async queries for the ``categories`` table.  This
layer has no knowledge of HTTP concerns — it never raises
:class:`HTTPException` and never calls ``session.commit()``.  Committing is
the responsibility of the Service layer.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryRepository:
    """Data-access layer for the ``categories`` table.

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

    async def get_all(self) -> list[Category]:
        """Retrieve every category ordered by name ascending.

        Eagerly loads the ``todos`` relationship so callers receive fully
        populated instances without triggering additional queries.

        Returns:
            A list of :class:`~app.models.category.Category` ORM instances
            ordered by ``name`` ascending.  Returns an empty list when the
            table is empty.
        """
        result = await self.db.execute(
            select(Category)
            .options(selectinload(Category.todos))
            .order_by(Category.name.asc())
        )
        categories = list(result.scalars().all())
        logger.debug("get_all returned %d category/categories", len(categories))
        return categories

    async def get_by_id(self, category_id: int) -> Category | None:
        """Retrieve a single category by its primary key.

        Args:
            category_id: The integer primary key of the category to fetch.

        Returns:
            The matching :class:`~app.models.category.Category` instance with
            its ``todos`` relationship eagerly loaded, or ``None`` when no row
            with that ``id`` exists.
        """
        result = await self.db.execute(
            select(Category)
            .options(selectinload(Category.todos))
            .where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        logger.debug(
            "get_by_id(%d) → %s",
            category_id,
            "found" if category else "not found",
        )
        return category

    async def get_by_name(self, name: str) -> Category | None:
        """Retrieve a single category by its name (case-insensitive).

        Used by the Service layer to enforce the uniqueness business rule
        before attempting an INSERT or UPDATE, and to return a 409 Conflict
        when a duplicate name is detected.

        Args:
            name: The category name to look up.  The comparison is performed
                case-insensitively using the database ``LOWER()`` function so
                that "Work" and "work" are treated as duplicates.

        Returns:
            The matching :class:`~app.models.category.Category` instance, or
            ``None`` when no category with that name exists.
        """
        result = await self.db.execute(
            select(Category).where(func.lower(Category.name) == name.lower())
        )
        category = result.scalar_one_or_none()
        logger.debug(
            "get_by_name(%r) → %s",
            name,
            "found" if category else "not found",
        )
        return category

    async def count_todos(self, category_id: int) -> int:
        """Count how many todos are currently assigned to a category.

        Used by the Service layer to enforce the business rule that a category
        may not be deleted while it still has todos assigned to it (the
        service raises HTTP 409 Conflict in that case).

        Args:
            category_id: The primary key of the category whose assigned todos
                should be counted.

        Returns:
            The number of todos whose ``category_id`` column equals the
            supplied ``category_id``.  Returns ``0`` when no todos are
            assigned.
        """
        # Import here to avoid a circular import at module level; the models
        # are only needed for this one query.
        from app.models.todo import Todo  # noqa: PLC0415

        result = await self.db.execute(
            select(func.count()).select_from(Todo).where(Todo.category_id == category_id)
        )
        count = result.scalar_one()
        logger.debug("count_todos(category_id=%d) → %d", category_id, count)
        return count

    async def create(self, category: CategoryCreate) -> Category:
        """Insert a new category row and return the persisted ORM instance.

        The method flushes the session so that the database assigns the
        auto-incremented ``id`` and server-default timestamps, then refreshes
        the instance to load those values into memory.  ``commit()`` is
        intentionally not called here — the Service layer is responsible for
        committing the transaction.

        Args:
            category: A validated :class:`~app.schemas.category.CategoryCreate`
                payload containing the fields for the new category.

        Returns:
            The newly created :class:`~app.models.category.Category` ORM
            instance with all server-assigned fields (``id``, ``created_at``,
            ``updated_at``) populated.
        """
        db_category = Category(
            name=category.name,
            description=category.description,
        )
        self.db.add(db_category)
        # Flush to send the INSERT to the DB and populate server-side defaults
        # (id, created_at, updated_at) without committing the transaction.
        await self.db.flush()
        await self.db.refresh(db_category)
        logger.debug("create → new category id=%d name=%r", db_category.id, db_category.name)
        return db_category

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        """Apply a partial update to an existing category ORM instance.

        Only fields that the client explicitly included in the PATCH body are
        written — fields omitted by the client are left unchanged.

        ``model_fields_set`` is a Pydantic v2 attribute that records exactly
        which field names were present in the original input dict.  Iterating
        over it (rather than all fields) ensures that a missing field is
        treated as "do not touch" rather than "set to None", which is critical
        for correct PATCH semantics.

        Args:
            category: The existing :class:`~app.models.category.Category` ORM
                instance to modify.
            data: A validated :class:`~app.schemas.category.CategoryUpdate`
                payload containing only the fields the caller wishes to change.

        Returns:
            The updated :class:`~app.models.category.Category` ORM instance
            with the new field values applied and server-side ``updated_at``
            refreshed.
        """
        for field in data.model_fields_set:
            setattr(category, field, getattr(data, field))

        await self.db.flush()
        await self.db.refresh(category)
        logger.debug(
            "update → category id=%d fields=%s",
            category.id,
            data.model_fields_set,
        )
        return category

    async def delete(self, category: Category) -> None:
        """Delete an existing category row from the database.

        The row is removed from the session and a ``DELETE`` statement is
        flushed to the database.  The caller (Service layer) must commit the
        transaction for the deletion to be permanent.

        Args:
            category: The :class:`~app.models.category.Category` ORM instance
                to delete.

        Returns:
            None
        """
        await self.db.delete(category)
        await self.db.flush()
        logger.debug("delete → category id=%d removed from session", category.id)
