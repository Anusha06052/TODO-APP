"""HTTP routing layer for the Category resource.

Defines a single :data:`router` with all five CRUD endpoints.  Each handler
delegates immediately to :class:`~app.services.category_service.CategoryService` —
no business logic or database access lives here.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies.category import get_category_service
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse], status_code=status.HTTP_200_OK)
async def list_categories(
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> list[CategoryResponse]:
    """Return all categories ordered by name ascending.

    HTTP contract:
        GET /categories
        200 OK — body is a JSON array of :class:`~app.schemas.category.CategoryResponse`
        objects.  Returns an empty array when no categories exist.
    """
    logger.debug("GET /categories requested")
    return await service.get_all_categories()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Create a new category from the supplied payload.

    HTTP contract:
        POST /categories
        Request body: :class:`~app.schemas.category.CategoryCreate` JSON.
        201 Created — body is the newly created
        :class:`~app.schemas.category.CategoryResponse`.
        409 Conflict — a category with the same name already exists.
        422 Unprocessable Entity — body fails Pydantic validation.
    """
    logger.debug("POST /categories requested")
    return await service.create_category(payload)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_category(
    category_id: int,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Retrieve a single category by its primary key.

    HTTP contract:
        GET /categories/{category_id}
        200 OK — body is the matching :class:`~app.schemas.category.CategoryResponse`.
        404 Not Found — no category exists with the given ``category_id``.
    """
    logger.debug("GET /categories/%d requested", category_id)
    return await service.get_category_by_id(category_id)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Partially update an existing category.

    HTTP contract:
        PATCH /categories/{category_id}
        Request body: :class:`~app.schemas.category.CategoryUpdate` JSON (all fields
        optional — only supplied fields are applied).
        200 OK — body is the updated :class:`~app.schemas.category.CategoryResponse`.
        404 Not Found — no category exists with the given ``category_id``.
        409 Conflict — a different category with the same name already exists.
        422 Unprocessable Entity — body fails Pydantic validation.
    """
    logger.debug("PATCH /categories/%d requested", category_id)
    return await service.update_category(category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> Response:
    """Delete a category by its primary key.

    HTTP contract:
        DELETE /categories/{category_id}
        204 No Content — category was deleted successfully; body is empty.
        404 Not Found — no category exists with the given ``category_id``.
        409 Conflict — one or more todos are still assigned to the category.
    """
    logger.debug("DELETE /categories/%d requested", category_id)
    await service.delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
