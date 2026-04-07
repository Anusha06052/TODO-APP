"""FastAPI dependency factories for the Category resource.

This module wires the repository and service layers together via FastAPI's
``Depends()`` system.  Route handlers should import from here — never
instantiate repositories or services manually.

Dependency chain::

    get_db() → AsyncSession
        ↓
    get_category_repository(session) → CategoryRepository
        ↓
    get_category_service(repository, session) → CategoryService
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService


async def get_category_repository(
    session: AsyncSession = Depends(get_db),
) -> CategoryRepository:
    """Construct a :class:`~app.repositories.category_repository.CategoryRepository`.

    Args:
        session: An async database session provided by :func:`~app.db.session.get_db`.

    Returns:
        A :class:`~app.repositories.category_repository.CategoryRepository` bound to
        the current request's database session.
    """
    return CategoryRepository(session)


async def get_category_service(
    repository: CategoryRepository = Depends(get_category_repository),
    session: AsyncSession = Depends(get_db),
) -> CategoryService:
    """Construct a :class:`~app.services.category_service.CategoryService`.

    Intended for use with ``Depends()`` in route handlers::

        async def list_categories(
            service: Annotated[CategoryService, Depends(get_category_service)],
        ) -> list[CategoryResponse]: ...

    Args:
        repository: A :class:`~app.repositories.category_repository.CategoryRepository`
            provided by :func:`get_category_repository`.
        session: An async database session provided by :func:`~app.db.session.get_db`.
            Passed directly to the service so it can commit transactions.

    Returns:
        A fully configured :class:`~app.services.category_service.CategoryService`.
    """
    return CategoryService(repository, session)
