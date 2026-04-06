"""Shared pytest fixtures for the Todo API test suite.

All fixtures default to ``scope="function"`` so that every test receives a
fresh, isolated mock.  A shared fixture (e.g. ``scope="session"``) would
allow side-effects from one test to leak into another — for example, a call
recorded on the mock in test A would still be visible when test B asserts on
the same mock.  Function scope eliminates that class of flakiness entirely.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_db
from app.main import app
from app.models.todo import Todo
from app.schemas.todo import TodoCreate


# ---------------------------------------------------------------------------
# mock_db
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def mock_db() -> AsyncMock:
    """Return an :class:`~unittest.mock.AsyncMock` that mimics
    :class:`~sqlalchemy.ext.asyncio.AsyncSession`.

    Mocked surface:

    * ``add()``    — records an ORM object for insertion/update (sync helper).
    * ``commit()`` — flushes the unit-of-work and persists changes (async).
    * ``refresh()`` — reloads ORM attributes from the database (async).
    * ``delete()`` — marks an ORM object for deletion (sync helper).
    * ``execute()`` — executes a Core/ORM statement (async).
    * ``scalars()`` — retrieves scalar results from the last execute (sync
      helper); its return value exposes ``.all()``, ``.first()``, and
      ``.scalar_one_or_none()`` as plain :class:`~unittest.mock.MagicMock`
      callables so tests can configure return values freely.

    Scope — ``"function"``:
        A new mock is created per test so recorded calls, configured
        return values, and ``side_effect`` settings never bleed between tests.

    Returns:
        AsyncMock: A fully configured stand-in for ``AsyncSession``.
    """
    # Build the scalars() return object first so tests can configure it.
    scalars_result = MagicMock()
    scalars_result.all = MagicMock(return_value=[])
    scalars_result.first = MagicMock(return_value=None)
    scalars_result.scalar_one_or_none = MagicMock(return_value=None)

    session = AsyncMock()

    # Sync helpers — plain MagicMock so they can be called without await.
    session.add = MagicMock()
    session.delete = MagicMock()

    # Async methods.
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()

    # scalars() is sync on AsyncSession (it wraps the CursorResult).
    session.scalars = MagicMock(return_value=scalars_result)

    return session


# ---------------------------------------------------------------------------
# todo_factory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def todo_factory() -> Callable[..., Todo]:
    """Return a factory callable that constructs :class:`~app.models.todo.Todo`
    ORM instances with sensible defaults.

    Usage::

        def test_something(todo_factory):
            todo = todo_factory(id=5, title="Write tests")
            assert todo.id == 5

    The factory signature is::

        make_todo(
            id: int = 1,
            title: str = "Test",
            description: str | None = None,
            is_completed: bool = False,
        ) -> Todo

    ``created_at`` and ``updated_at`` are always set to
    :func:`~datetime.datetime.now` at call time, matching the behaviour of a
    freshly fetched database row.

    Scope — ``"function"``:
        The fixture itself is stateless (it just returns a function), but
        function scope keeps the teardown boundary consistent with the rest of
        the suite.

    Returns:
        Callable: Factory that produces :class:`~app.models.todo.Todo` objects.
    """

    def make_todo(
        id: int = 1,
        title: str = "Test",
        description: str | None = None,
        is_completed: bool = False,
    ) -> Todo:
        """Construct a :class:`~app.models.todo.Todo` with the given values.

        Args:
            id: Primary key to assign to the instance.
            title: Short title string (not validated here).
            description: Optional longer description.
            is_completed: Completion state; defaults to ``False``.

        Returns:
            Todo: An unsaved ORM instance suitable for unit test assertions.
        """
        now = datetime.now()
        todo = Todo()
        todo.id = id
        todo.title = title
        todo.description = description
        todo.is_completed = is_completed
        todo.created_at = now
        todo.updated_at = now
        return todo

    return make_todo


# ---------------------------------------------------------------------------
# app_client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
async def app_client(mock_db: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """Provide an :class:`~httpx.AsyncClient` wired to the FastAPI app with the
    real database dependency swapped out for :fixture:`mock_db`.

    The ``get_db`` dependency is overridden for the lifetime of the fixture so
    every layer below the route (service, repository) receives the same mock
    session.  The override is removed after the test to avoid contaminating
    other test modules that may use the real database.

    Usage::

        async def test_list_todos_empty(app_client, mock_db):
            mock_db.scalars.return_value.all.return_value = []
            response = await app_client.get("/api/todos")
            assert response.status_code == 200

    Scope — ``"function"``:
        Each test gets its own client and its own mock session, so HTTP
        interactions and mock state are never shared between tests.

    Args:
        mock_db: The function-scoped :class:`~unittest.mock.AsyncMock` that
            replaces the real ``AsyncSession``.

    Yields:
        AsyncClient: HTTP test client pointed at ``http://test``.
    """

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        """Yield the pre-built mock session in place of the real one."""
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    # Always restore the override map so unrelated tests are not affected.
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# sample_create_dto
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def sample_create_dto() -> TodoCreate:
    """Return a pre-built :class:`~app.schemas.todo.TodoCreate` payload.

    Provides a realistic, valid creation DTO so individual tests do not need
    to repeat boilerplate construction.  Use as a baseline and mutate a copy
    when the test requires a different value.

    Scope — ``"function"``:
        Pydantic models are immutable-by-default in v2; however, function scope
        is kept for consistency with the rest of the suite and to avoid any
        risk of shared-object mutation in tests that use ``model_copy()``.

    Returns:
        TodoCreate: A valid creation payload with title ``"Buy groceries"``
        and description ``"Milk and eggs"``.
    """
    return TodoCreate(title="Buy groceries", description="Milk and eggs")
