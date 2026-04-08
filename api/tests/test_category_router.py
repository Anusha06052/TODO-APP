"""Integration tests for the Category HTTP router.

All five CRUD endpoints are exercised against the real FastAPI application
using an ``httpx.AsyncClient`` wired via ASGI transport.  The database session
is the only mock: every other layer (routes, services, repositories) executes
as production code, making these true integration tests.

Fixtures consumed from ``conftest.py``:
    - ``app_client``         — httpx.AsyncClient + ASGITransport, ``get_db`` overridden.
    - ``mock_db``            — AsyncMock stand-in for SQLAlchemy ``AsyncSession``.
    - ``category_factory``   — Callable that builds fully-populated ``Category`` ORM objects.
    - ``sample_category_create_dto`` — Pre-built valid ``CategoryCreate`` payload.

Naming convention: ``test_<action>_<condition>_<expected_outcome>``.
"""

from datetime import datetime
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.models.category import Category


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

FIXED_DT = datetime(2024, 6, 15, 10, 30, 0)
"""A deterministic timestamp used wherever server-side datetimes are needed."""


def _execute_result_list(categories: list[Category]) -> MagicMock:
    """Return a mock execute result compatible with ``repository.get_all()``.

    ``get_all`` calls ``result.scalars().all()`` on the ``execute`` return
    value.  This helper pre-configures all three levels of the call chain so
    tests only need to specify the desired list of categories.

    Args:
        categories: The list of :class:`~app.models.category.Category`
            objects to return.

    Returns:
        MagicMock: Drop-in for the ``CursorResult`` returned by ``execute``.
    """
    result = MagicMock()
    result.scalars.return_value.all.return_value = categories
    return result


def _execute_result_single(category: Category | None) -> MagicMock:
    """Return a mock execute result compatible with ``repository.get_by_id()``
    and ``repository.get_by_name()``.

    Both methods call ``result.scalar_one_or_none()`` on the ``execute``
    return value.  This helper pre-configures that level of the call chain.

    Args:
        category: The :class:`~app.models.category.Category` to return, or
            ``None`` to simulate a missing record.

    Returns:
        MagicMock: Drop-in for the ``CursorResult`` returned by ``execute``.
    """
    result = MagicMock()
    result.scalar_one_or_none.return_value = category
    return result


def _category_refresh_populates(
    category_id: int = 1,
) -> Callable[..., None]:
    """Return a ``side_effect`` function for ``mock_db.refresh`` on Category
    write operations (create and update).

    The repository and service each call ``db.refresh(category)`` after a
    write (once in the repository, once in the service after commit).  Both
    calls are plain ``refresh`` with no ``attribute_names`` kwarg.  This
    helper's inner function sets ``id``, ``created_at``, and ``updated_at``
    idempotently so that every call leaves the instance in a valid state for
    :class:`~app.schemas.category.CategoryResponse` serialisation.

    Args:
        category_id: The ``id`` to assign to the refreshed instance.

    Returns:
        Callable: A synchronous callable accepted by ``AsyncMock.side_effect``.
    """

    def _populate(instance: Category, **_kwargs: object) -> None:
        instance.id = category_id
        instance.created_at = FIXED_DT
        instance.updated_at = FIXED_DT

    return _populate


# ---------------------------------------------------------------------------
# GET /categories
# ---------------------------------------------------------------------------


class TestListCategories:
    """Integration tests for ``GET /categories``."""

    async def test_list_categories_with_no_categories_returns_200_empty_list(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """200 OK with an empty JSON array when the categories table is empty."""
        mock_db.execute.return_value = _execute_result_list([])

        response = await app_client.get("/categories")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_categories_with_existing_categories_returns_200_with_items(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — response body contains every category serialised correctly."""
        first = category_factory(id=1, name="Personal", description="My tasks")
        second = category_factory(id=2, name="Work", description=None)
        mock_db.execute.return_value = _execute_result_list([first, second])

        response = await app_client.get("/categories")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Personal"
        assert data[0]["description"] == "My tasks"
        assert data[1]["id"] == 2
        assert data[1]["name"] == "Work"
        assert data[1]["description"] is None

    async def test_list_categories_single_category_returns_200_with_one_item(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — a single-item list is returned correctly."""
        solo = category_factory(id=5, name="Hobbies")
        mock_db.execute.return_value = _execute_result_list([solo])

        response = await app_client.get("/categories")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["id"] == 5
        assert data[0]["name"] == "Hobbies"

    async def test_list_categories_response_includes_timestamps(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — ``created_at`` and ``updated_at`` are present in each item."""
        cat = category_factory(id=1, name="Personal")
        mock_db.execute.return_value = _execute_result_list([cat])

        response = await app_client.get("/categories")
        data = response.json()

        assert data[0]["created_at"] is not None
        assert data[0]["updated_at"] is not None


# ---------------------------------------------------------------------------
# POST /categories
# ---------------------------------------------------------------------------


class TestCreateCategory:
    """Integration tests for ``POST /categories``."""

    async def test_create_category_with_valid_payload_returns_201(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """201 Created — response body contains the new category with server fields."""
        # get_by_name returns None (no conflict).
        mock_db.execute.return_value = _execute_result_single(None)
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=1)

        response = await app_client.post(
            "/categories",
            json={"name": "Work", "description": "Office tasks"},
        )
        data = response.json()

        assert response.status_code == 201
        assert data["id"] == 1
        assert data["name"] == "Work"
        assert data["description"] == "Office tasks"
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    async def test_create_category_without_description_returns_201(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """201 Created — description is optional and defaults to null."""
        mock_db.execute.return_value = _execute_result_single(None)
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=2)

        response = await app_client.post("/categories", json={"name": "Personal"})
        data = response.json()

        assert response.status_code == 201
        assert data["name"] == "Personal"
        assert data["description"] is None

    async def test_create_category_with_duplicate_name_returns_409(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """409 Conflict — service raises 409 when the name is already taken."""
        existing = category_factory(id=10, name="Work")
        mock_db.execute.return_value = _execute_result_single(existing)

        response = await app_client.post("/categories", json={"name": "Work"})

        assert response.status_code == 409

    async def test_create_category_409_detail_contains_conflicting_name(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """409 detail message contains the conflicting name for transparency."""
        existing = category_factory(id=10, name="Work")
        mock_db.execute.return_value = _execute_result_single(existing)

        response = await app_client.post("/categories", json={"name": "Work"})

        assert "Work" in response.json()["detail"]

    async def test_create_category_with_missing_name_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the required name field is absent."""
        response = await app_client.post("/categories", json={})

        assert response.status_code == 422

    async def test_create_category_with_blank_name_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the name consists only of whitespace."""
        response = await app_client.post("/categories", json={"name": "   "})

        assert response.status_code == 422

    async def test_create_category_with_empty_name_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the name is an empty string."""
        response = await app_client.post("/categories", json={"name": ""})

        assert response.status_code == 422

    async def test_create_category_with_name_exceeding_max_length_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when name exceeds the 100-character limit."""
        response = await app_client.post("/categories", json={"name": "A" * 101})

        assert response.status_code == 422

    async def test_create_category_with_description_exceeding_max_length_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when description exceeds the 500-character limit."""
        response = await app_client.post(
            "/categories",
            json={"name": "Valid", "description": "D" * 501},
        )

        assert response.status_code == 422

    async def test_create_category_name_at_max_length_returns_201(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """201 Created — a name exactly 100 characters long is valid."""
        mock_db.execute.return_value = _execute_result_single(None)
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=3)

        response = await app_client.post("/categories", json={"name": "A" * 100})

        assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /categories/{category_id}
# ---------------------------------------------------------------------------


class TestGetCategory:
    """Integration tests for ``GET /categories/{category_id}``."""

    async def test_get_category_with_existing_id_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — response body matches the stored category."""
        cat = category_factory(id=5, name="Work", description="Office work")
        mock_db.execute.return_value = _execute_result_single(cat)

        response = await app_client.get("/categories/5")
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == 5
        assert data["name"] == "Work"
        assert data["description"] == "Office work"

    async def test_get_category_with_nonexistent_id_returns_404(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """404 Not Found — detail message contains the missing id."""
        mock_db.execute.return_value = _execute_result_single(None)

        response = await app_client.get("/categories/999")

        assert response.status_code == 404
        assert "999" in response.json()["detail"]

    async def test_get_category_response_includes_all_fields(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — all CategoryResponse fields are present in the response body."""
        cat = category_factory(id=3, name="Errands", description="Quick tasks")
        mock_db.execute.return_value = _execute_result_single(cat)

        response = await app_client.get("/categories/3")
        data = response.json()

        assert response.status_code == 200
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_category_with_null_description_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — description is null when the category has none."""
        cat = category_factory(id=7, name="Minimal", description=None)
        mock_db.execute.return_value = _execute_result_single(cat)

        response = await app_client.get("/categories/7")
        data = response.json()

        assert response.status_code == 200
        assert data["description"] is None


# ---------------------------------------------------------------------------
# PATCH /categories/{category_id}
# ---------------------------------------------------------------------------


class TestUpdateCategory:
    """Integration tests for ``PATCH /categories/{category_id}``."""

    async def test_update_category_name_returns_200_with_new_name(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — updated name is reflected in the response body.

        Two execute calls are made: get_by_id (fetch target) then get_by_name
        (uniqueness check).  ``side_effect`` is used to provide each call's
        return value in sequence.
        """
        existing = category_factory(id=1, name="Old Name")
        # get_by_id → existing; get_by_name → None (new name is free).
        mock_db.execute.side_effect = [
            _execute_result_single(existing),
            _execute_result_single(None),
        ]
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=1)

        response = await app_client.patch("/categories/1", json={"name": "New Name"})
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == 1
        assert data["name"] == "New Name"

    async def test_update_category_description_only_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — patching only description skips the uniqueness execute call.

        Only one execute call is made (get_by_id) because the name field is
        absent from the payload.
        """
        existing = category_factory(id=2, name="Work", description="Old desc")
        mock_db.execute.return_value = _execute_result_single(existing)
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=2)

        response = await app_client.patch(
            "/categories/2", json={"description": "New desc"}
        )
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == 2
        assert data["description"] == "New desc"

    async def test_update_category_description_to_null_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — description can be cleared to null via an explicit null value."""
        existing = category_factory(id=3, name="Work", description="Remove me")
        mock_db.execute.return_value = _execute_result_single(existing)
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=3)

        response = await app_client.patch(
            "/categories/3", json={"description": None}
        )
        data = response.json()

        assert response.status_code == 200
        assert data["description"] is None

    async def test_update_category_keeping_own_name_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — renaming a category to its own current name does not raise 409.

        The same ORM instance is returned by both get_by_id and get_by_name
        (same ``id``), so the service's self-match guard allows the update.
        """
        existing = category_factory(id=4, name="Work")
        mock_db.execute.side_effect = [
            _execute_result_single(existing),   # get_by_id
            _execute_result_single(existing),   # get_by_name (same id — no conflict)
        ]
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=4)

        response = await app_client.patch("/categories/4", json={"name": "Work"})

        assert response.status_code == 200

    async def test_update_category_with_name_taken_by_other_returns_409(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """409 Conflict — service raises 409 when the new name is used by a
        different category."""
        own_cat = category_factory(id=1, name="Work")
        other_cat = category_factory(id=2, name="Personal")
        mock_db.execute.side_effect = [
            _execute_result_single(own_cat),    # get_by_id
            _execute_result_single(other_cat),  # get_by_name → different id
        ]

        response = await app_client.patch("/categories/1", json={"name": "Personal"})

        assert response.status_code == 409

    async def test_update_category_409_detail_contains_conflicting_name(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """409 detail message contains the conflicting name."""
        own_cat = category_factory(id=1, name="Work")
        other_cat = category_factory(id=2, name="Personal")
        mock_db.execute.side_effect = [
            _execute_result_single(own_cat),
            _execute_result_single(other_cat),
        ]

        response = await app_client.patch("/categories/1", json={"name": "Personal"})

        assert "Personal" in response.json()["detail"]

    async def test_update_category_with_nonexistent_id_returns_404(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """404 Not Found — detail message contains the missing id."""
        mock_db.execute.return_value = _execute_result_single(None)

        response = await app_client.patch("/categories/99", json={"name": "Ghost"})

        assert response.status_code == 404
        assert "99" in response.json()["detail"]

    async def test_update_category_with_blank_name_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the supplied name is all whitespace."""
        response = await app_client.patch("/categories/1", json={"name": "   "})

        assert response.status_code == 422

    async def test_update_category_with_name_exceeding_max_length_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when name exceeds the 100-character limit."""
        response = await app_client.patch(
            "/categories/1", json={"name": "A" * 101}
        )

        assert response.status_code == 422

    async def test_update_category_empty_patch_body_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — an empty PATCH body is valid; no fields are changed."""
        existing = category_factory(id=6, name="Work", description="Unchanged")
        mock_db.execute.return_value = _execute_result_single(existing)
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=6)

        response = await app_client.patch("/categories/6", json={})

        assert response.status_code == 200

    async def test_update_category_response_includes_all_fields(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """200 OK — all CategoryResponse fields are present after a successful update."""
        existing = category_factory(id=8, name="Errands")
        mock_db.execute.side_effect = [
            _execute_result_single(existing),
            _execute_result_single(None),
        ]
        mock_db.refresh.side_effect = _category_refresh_populates(category_id=8)

        response = await app_client.patch("/categories/8", json={"name": "Updated"})
        data = response.json()

        assert response.status_code == 200
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "created_at" in data
        assert "updated_at" in data


# ---------------------------------------------------------------------------
# DELETE /categories/{category_id}
# ---------------------------------------------------------------------------


class TestDeleteCategory:
    """Integration tests for ``DELETE /categories/{category_id}``."""

    async def test_delete_category_with_existing_id_returns_204_no_body(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """204 No Content — response body is empty on successful deletion."""
        cat = category_factory(id=3, name="Work")
        mock_db.execute.return_value = _execute_result_single(cat)
        # CategoryRepository.delete awaits db.delete(); override to AsyncMock
        # since conftest sets it to a synchronous MagicMock by default.
        mock_db.delete = AsyncMock()

        response = await app_client.delete("/categories/3")

        assert response.status_code == 204
        assert response.content == b""

    async def test_delete_category_with_nonexistent_id_returns_404(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """404 Not Found — detail message contains the missing id.

        The service raises 404 before the repository delete is ever called,
        so no special delete mock is required.
        """
        mock_db.execute.return_value = _execute_result_single(None)

        response = await app_client.delete("/categories/42")

        assert response.status_code == 404
        assert "42" in response.json()["detail"]

    async def test_delete_category_commit_is_called_after_delete(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """The session is committed after a successful deletion."""
        cat = category_factory(id=5, name="Personal")
        mock_db.execute.return_value = _execute_result_single(cat)
        mock_db.delete = AsyncMock()

        await app_client.delete("/categories/5")

        mock_db.commit.assert_called_once()
