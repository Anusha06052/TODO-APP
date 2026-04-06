"""Integration tests for the Todo HTTP router.

All five CRUD endpoints are exercised against the real FastAPI application
using an ``httpx.AsyncClient`` wired via ASGI transport.  The database session
is the only mock: every other layer (routes, services, repositories) executes
as production code, making these true integration tests.

Fixtures consumed from ``conftest.py``:
    - ``app_client``     — httpx.AsyncClient + ASGITransport, ``get_db`` overridden.
    - ``mock_db``        — AsyncMock stand-in for SQLAlchemy ``AsyncSession``.
    - ``todo_factory``   — Callable that builds fully-populated ``Todo`` ORM objects.
    - ``sample_create_dto`` — Pre-built valid ``TodoCreate`` payload.

Naming convention: ``test_<action>_<condition>_<expected_outcome>``.
"""

from datetime import datetime
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.models.todo import Todo


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

FIXED_DT = datetime(2024, 6, 15, 10, 30, 0)
"""A deterministic timestamp used wherever server-side datetimes are needed."""


def _execute_result_list(todos: list[Todo]) -> MagicMock:
    """Return a mock execute result compatible with ``repository.get_all()``.

    ``get_all`` calls ``result.scalars().all()`` on the ``execute`` return
    value.  This helper pre-configures all three levels of the call chain so
    tests only need to specify the desired list of todos.

    Args:
        todos: The list of :class:`~app.models.todo.Todo` objects to return.

    Returns:
        MagicMock: Drop-in for the ``CursorResult`` returned by ``execute``.
    """
    result = MagicMock()
    result.scalars.return_value.all.return_value = todos
    return result


def _execute_result_single(todo: Todo | None) -> MagicMock:
    """Return a mock execute result compatible with ``repository.get_by_id()``.

    ``get_by_id`` calls ``result.scalar_one_or_none()`` on the ``execute``
    return value.  This helper pre-configures that level of the call chain.

    Args:
        todo: The :class:`~app.models.todo.Todo` to return, or ``None`` to
            simulate a missing record.

    Returns:
        MagicMock: Drop-in for the ``CursorResult`` returned by ``execute``.
    """
    result = MagicMock()
    result.scalar_one_or_none.return_value = todo
    return result


def _refresh_populates(
    todo_id: int = 1,
    is_completed: bool = False,
) -> Callable[[Todo], None]:
    """Return a ``side_effect`` function for ``mock_db.refresh``.

    Because the test environment never hits a real database, server-side
    defaults (``id``, ``created_at``, ``updated_at``) are never applied to
    newly created ORM instances.  Attaching this as a ``side_effect`` on the
    mock ``refresh`` call simulates what a real ``session.refresh()`` would
    populate from the database row.

    Args:
        todo_id: The ``id`` to write onto the instance.
        is_completed: The ``is_completed`` flag to write onto the instance.

    Returns:
        Callable: A synchronous callable accepted by ``AsyncMock.side_effect``.
    """

    def _populate(instance: Todo) -> None:
        instance.id = todo_id
        instance.is_completed = is_completed
        instance.created_at = FIXED_DT
        instance.updated_at = FIXED_DT

    return _populate


# ---------------------------------------------------------------------------
# GET /todos
# ---------------------------------------------------------------------------


class TestListTodos:
    """Integration tests for ``GET /todos``."""

    async def test_list_todos_with_no_todos_returns_200_empty_list(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """200 OK with an empty JSON array when the todos table is empty."""
        mock_db.execute.return_value = _execute_result_list([])

        response = await app_client.get("/todos")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_todos_with_existing_todos_returns_200_with_items(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """200 OK — response body contains every todo serialised correctly."""
        first = todo_factory(id=1, title="Buy groceries", description="Milk and eggs")
        second = todo_factory(id=2, title="Read docs", description=None, is_completed=True)
        mock_db.execute.return_value = _execute_result_list([first, second])

        response = await app_client.get("/todos")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["title"] == "Buy groceries"
        assert data[0]["description"] == "Milk and eggs"
        assert data[0]["is_completed"] is False
        assert data[1]["id"] == 2
        assert data[1]["title"] == "Read docs"
        assert data[1]["description"] is None
        assert data[1]["is_completed"] is True


# ---------------------------------------------------------------------------
# POST /todos
# ---------------------------------------------------------------------------


class TestCreateTodo:
    """Integration tests for ``POST /todos``."""

    async def test_create_todo_with_valid_payload_returns_201(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """201 Created — response body contains the new todo with server fields."""
        mock_db.refresh.side_effect = _refresh_populates(todo_id=1)

        response = await app_client.post(
            "/todos",
            json={"title": "Write integration tests", "description": "Cover all routes"},
        )
        data = response.json()

        assert response.status_code == 201
        assert data["id"] == 1
        assert data["title"] == "Write integration tests"
        assert data["description"] == "Cover all routes"
        assert data["is_completed"] is False
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    async def test_create_todo_without_description_returns_201(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """201 Created — description field is optional and defaults to null."""
        mock_db.refresh.side_effect = _refresh_populates(todo_id=2)

        response = await app_client.post("/todos", json={"title": "Minimal todo"})
        data = response.json()

        assert response.status_code == 201
        assert data["title"] == "Minimal todo"
        assert data["description"] is None

    async def test_create_todo_with_missing_title_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the required title field is absent."""
        response = await app_client.post(
            "/todos",
            json={"description": "No title provided"},
        )

        assert response.status_code == 422

    async def test_create_todo_with_blank_title_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the title consists only of whitespace."""
        response = await app_client.post("/todos", json={"title": "   "})

        assert response.status_code == 422

    async def test_create_todo_with_title_exceeding_max_length_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when title exceeds the 200-character limit."""
        response = await app_client.post("/todos", json={"title": "x" * 201})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /todos/{todo_id}
# ---------------------------------------------------------------------------


class TestGetTodo:
    """Integration tests for ``GET /todos/{todo_id}``."""

    async def test_get_todo_with_existing_id_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """200 OK — response body matches the stored todo."""
        todo = todo_factory(id=5, title="Existing todo", description="Some details")
        mock_db.execute.return_value = _execute_result_single(todo)

        response = await app_client.get("/todos/5")
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == 5
        assert data["title"] == "Existing todo"
        assert data["description"] == "Some details"
        assert data["is_completed"] is False

    async def test_get_todo_with_nonexistent_id_returns_404(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """404 Not Found — detail message contains the missing id."""
        mock_db.execute.return_value = _execute_result_single(None)

        response = await app_client.get("/todos/999")

        assert response.status_code == 404
        assert "999" in response.json()["detail"]


# ---------------------------------------------------------------------------
# PATCH /todos/{todo_id}
# ---------------------------------------------------------------------------


class TestUpdateTodo:
    """Integration tests for ``PATCH /todos/{todo_id}``."""

    async def test_update_todo_title_returns_200_with_updated_title(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """200 OK — updated title is reflected in the response body."""
        existing = todo_factory(id=3, title="Old title", description="Same desc")
        mock_db.execute.return_value = _execute_result_single(existing)

        response = await app_client.patch("/todos/3", json={"title": "New title"})
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == 3
        assert data["title"] == "New title"
        assert data["description"] == "Same desc"

    async def test_update_todo_completion_flag_returns_200_as_completed(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """200 OK — is_completed is updated to True in the response body."""
        existing = todo_factory(id=4, title="Finish report", is_completed=False)
        mock_db.execute.return_value = _execute_result_single(existing)

        response = await app_client.patch("/todos/4", json={"is_completed": True})
        data = response.json()

        assert response.status_code == 200
        assert data["id"] == 4
        assert data["is_completed"] is True

    async def test_update_todo_with_nonexistent_id_returns_404(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """404 Not Found — detail message contains the missing id."""
        mock_db.execute.return_value = _execute_result_single(None)

        response = await app_client.patch("/todos/42", json={"title": "Ghost update"})

        assert response.status_code == 404
        assert "42" in response.json()["detail"]

    async def test_update_todo_with_blank_title_returns_422(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """422 Unprocessable Entity when the supplied title is all whitespace."""
        response = await app_client.patch("/todos/1", json={"title": "   "})

        assert response.status_code == 422

    async def test_update_todo_description_to_null_returns_200(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """200 OK — description can be cleared by sending null."""
        existing = todo_factory(id=6, title="Has desc", description="Remove me")
        mock_db.execute.return_value = _execute_result_single(existing)

        response = await app_client.patch("/todos/6", json={"description": None})
        data = response.json()

        assert response.status_code == 200
        assert data["description"] is None


# ---------------------------------------------------------------------------
# DELETE /todos/{todo_id}
# ---------------------------------------------------------------------------


class TestDeleteTodo:
    """Integration tests for ``DELETE /todos/{todo_id}``."""

    async def test_delete_todo_with_existing_id_returns_204_no_body(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """204 No Content — response body is empty on successful deletion."""
        todo = todo_factory(id=7, title="Deletable todo")
        mock_db.execute.return_value = _execute_result_single(todo)
        # Conftest sets delete as MagicMock; the repository awaits it, so
        # override to AsyncMock to ensure awaiting succeeds.
        mock_db.delete = AsyncMock()

        response = await app_client.delete("/todos/7")

        assert response.status_code == 204
        assert response.content == b""

    async def test_delete_todo_with_nonexistent_id_returns_404(
        self,
        app_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        """404 Not Found — detail message contains the missing id.

        The service raises 404 before the repository delete is ever called,
        so no special delete mock is required.
        """
        mock_db.execute.return_value = _execute_result_single(None)

        response = await app_client.delete("/todos/999")

        assert response.status_code == 404
        assert "999" in response.json()["detail"]
