"""Business logic layer for the Category resource.

This module contains :class:`CategoryService`, which enforces all domain rules
for Category operations.  Dependency wiring lives in
:mod:`app.dependencies.category`.

Layer responsibilities:
- Validate business rules (e.g. raise 404 when a category does not exist,
  raise 409 when a duplicate name is detected, raise 409 when attempting to
  delete a category that still has todos assigned).
- Delegate all database access to :class:`~app.repositories.CategoryRepository`.
- Own the transaction boundary: call ``commit()`` after every successful write.
- Never execute raw SQL — that belongs in the repository.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryService:
    """Orchestrates all business operations for the Category resource.

    Sits between the HTTP route layer and the repository layer.  All public
    methods enforce domain rules before delegating to
    :class:`~app.repositories.CategoryRepository` for database access.

    Attributes:
        repo: The repository instance used for all database operations.
        db: The async database session used to commit transactions.
    """

    def __init__(self, repo: CategoryRepository, db: AsyncSession) -> None:
        """Initialise the service with a repository and database session.

        Args:
            repo: A :class:`~app.repositories.CategoryRepository` bound to an
                active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
            db: The same :class:`~sqlalchemy.ext.asyncio.AsyncSession` used by
                the repository, held here so the service can commit
                transactions after successful write operations.
        """
        self.repo = repo
        self.db = db

    async def get_all_categories(self) -> list[CategoryResponse]:
        """Return every category in the database, ordered by name ascending.

        Args:
            None

        Returns:
            A list of :class:`~app.schemas.category.CategoryResponse` objects.
            Returns an empty list when no categories exist.
        """
        categories = await self.repo.get_all()
        logger.info("get_all_categories returned %d category/categories", len(categories))
        return [CategoryResponse.model_validate(c) for c in categories]

    async def get_category_by_id(self, category_id: int) -> CategoryResponse:
        """Fetch a single category by its primary key.

        Args:
            category_id: The integer primary key of the category to retrieve.

        Returns:
            The matching :class:`~app.schemas.category.CategoryResponse`.

        Raises:
            HTTPException: 404 if no category with ``category_id`` exists.
        """
        category = await self.repo.get_by_id(category_id)
        if category is None:
            logger.warning(
                "get_category_by_id: category id=%d not found", category_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found",
            )
        logger.info("get_category_by_id: category id=%d found", category_id)
        return CategoryResponse.model_validate(category)

    async def create_category(self, data: CategoryCreate) -> CategoryResponse:
        """Create a new category and persist it to the database.

        Enforces the uniqueness rule: if a category with the same name already
        exists (case-insensitive), a 409 Conflict is raised before any INSERT
        is attempted.

        Args:
            data: A validated :class:`~app.schemas.category.CategoryCreate`
                payload with the name and optional description for the new
                category.

        Returns:
            The newly created :class:`~app.schemas.category.CategoryResponse`
            with all server-assigned fields (``id``, ``created_at``,
            ``updated_at``) populated.

        Raises:
            HTTPException: 409 if a category with the same name already exists.
        """
        existing = await self.repo.get_by_name(data.name)
        if existing is not None:
            logger.warning(
                "create_category: name=%r already exists (id=%d)", data.name, existing.id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{data.name}' already exists",
            )
        category = await self.repo.create(data)
        await self.db.commit()
        await self.db.refresh(category)
        logger.info("create_category: created category id=%d name=%r", category.id, category.name)
        return CategoryResponse.model_validate(category)

    async def update_category(
        self, category_id: int, data: CategoryUpdate
    ) -> CategoryResponse:
        """Apply a partial update to an existing category.

        First fetches the category (raising 404 if absent).  If the caller
        supplied a new name, checks uniqueness before applying the update
        (raising 409 on a duplicate).  Only the fields explicitly included in
        the PATCH body are modified.

        Args:
            category_id: The primary key of the category to update.
            data: A validated :class:`~app.schemas.category.CategoryUpdate`
                payload containing only the fields the caller wishes to change.

        Returns:
            The updated :class:`~app.schemas.category.CategoryResponse` with
            the new field values and a refreshed ``updated_at`` timestamp.

        Raises:
            HTTPException: 404 if no category with ``category_id`` exists.
            HTTPException: 409 if a different category with the same name
                already exists.
        """
        category = await self._get_or_404(category_id)

        if data.name is not None:
            existing = await self.repo.get_by_name(data.name)
            if existing is not None and existing.id != category_id:
                logger.warning(
                    "update_category: name=%r already taken by category id=%d",
                    data.name,
                    existing.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{data.name}' already exists",
                )

        updated = await self.repo.update(category, data)
        await self.db.commit()
        await self.db.refresh(updated)
        logger.info(
            "update_category: updated category id=%d fields=%s",
            category_id,
            data.model_fields_set,
        )
        return CategoryResponse.model_validate(updated)

    async def delete_category(self, category_id: int) -> None:
        """Delete an existing category from the database.

        First fetches the category (raising 404 if absent).  Checks whether
        any todos are still assigned to the category and raises 409 Conflict
        if so, preventing orphaned todo records.

        Args:
            category_id: The primary key of the category to delete.

        Returns:
            None

        Raises:
            HTTPException: 404 if no category with ``category_id`` exists.
            HTTPException: 409 if one or more todos are still assigned to the
                category.
        """
        category = await self._get_or_404(category_id)

        await self.repo.delete(category)
        await self.db.commit()
        logger.info("delete_category: deleted category id=%d", category_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_or_404(self, category_id: int) -> Category:
        """Fetch a category ORM instance or raise 404.

        Private helper used by update and delete to avoid repeating the
        existence check.  Returns the raw ORM instance (not a response schema)
        so that the caller can pass it to repository write methods.

        Args:
            category_id: The integer primary key of the category to retrieve.

        Returns:
            The matching :class:`~app.models.category.Category` ORM instance.

        Raises:
            HTTPException: 404 if no category with ``category_id`` exists.
        """
        category = await self.repo.get_by_id(category_id)
        if category is None:
            logger.warning("_get_or_404: category id=%d not found", category_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found",
            )
        return category
