"""Unit tests for :class:`~app.repositories.todo_repository.TodoRepository`.

All database I/O is replaced with a fully mocked
:class:`~sqlalchemy.ext.asyncio.AsyncSession`.  Tests verify that:

* The correct session methods are called in the correct order.
* ``flush()`` and ``refresh()`` are invoked after every write operation.
* Return values are derived from what the mock session produces.
* ``update()`` applies **only** the fields present in ``model_fields_set``,
  leaving untouched fields unchanged.

No real database connection is required; the entire suite runs in-process.

Naming convention: ``test_<method>_<scenario>_<expected_outcome>``.
"""

from datetime import datetime
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.todo import Todo
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import TodoCreate, TodoUpdate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_db() -> AsyncMock:
    """Return a :class:`~unittest.mock.AsyncMock` that mimics
    :class:`~sqlalchemy.ext.asyncio.AsyncSession`.

    ``add`` is overridden to a plain :class:`~unittest.mock.MagicMock` because
    the real ``AsyncSession.add()`` is a synchronous helper.  All other
    session methods (``flush``, ``refresh``, ``delete``, ``execute``) are left
    as auto-created :class:`~unittest.mock.AsyncMock` instances so they can be
    properly awaited.

    ``refresh`` is given a default ``side_effect`` that sets ``instance.id = 1``
    when ``id`` is ``None``.  This simulates the database assigning an
    auto-increment primary key after a flush, which is required so that the
    ``logger.debug("… id=%d", db_todo.id)`` call inside
    :meth:`~app.repositories.todo_repository.TodoRepository.create` does not
    receive ``None`` and raise a ``TypeError``.

    Scope — ``"function"``:
        A fresh mock is constructed per test to prevent recorded calls and
        configured return values from bleeding across tests.

    Returns:
        AsyncMock: Configured stand-in for ``AsyncSession``.
    """
    session = AsyncMock()

    # AsyncSession.add() is synchronous — override the default AsyncMock.
    session.add = MagicMock()

    # ``execute`` is async, but its *return value* is a plain CursorResult whose
    # methods (``scalars()``, ``scalar_one_or_none()``) are all synchronous.
    # If we leave ``execute.return_value`` as the default AsyncMock child, those
    # calls return coroutine objects instead of plain values.  Replacing the
    # return value with a MagicMock restores correct sync-call semantics.
    session.execute.return_value = MagicMock()

    # Simulate the database assigning a primary key after flush + refresh so
    # that repository logging ("id=%d") receives an integer, not None.
    async def _default_refresh(instance: object) -> None:
        if getattr(instance, "id", None) is None:
            instance.id = 1  # type: ignore[union-attr]

    session.refresh.side_effect = _default_refresh
    return session


@pytest.fixture()
def repo(mock_db: AsyncMock) -> TodoRepository:
    """Return a :class:`~app.repositories.todo_repository.TodoRepository`
    wired to :fixture:`mock_db`.

    Args:
        mock_db: Mocked async session injected at construction time.

    Returns:
        TodoRepository: Instance under test.
    """
    return TodoRepository(db=mock_db)


@pytest.fixture()
def make_todo() -> Callable[..., Todo]:
    """Return a factory that constructs :class:`~app.models.todo.Todo` ORM
    instances with sensible, deterministic defaults.

    Usage::

        def test_something(make_todo):
            todo = make_todo(id=7, title="Buy milk")
            assert todo.id == 7

    Returns:
        Callable: Factory that produces :class:`~app.models.todo.Todo` instances.
    """

    def factory(
        id: int = 1,
        title: str = "Test Todo",
        description: str | None = None,
        is_completed: bool = False,
    ) -> Todo:
        """Construct a :class:`~app.models.todo.Todo` with the given values.

        Args:
            id: Primary key assigned to the instance.
            title: Short title string (not validated here).
            description: Optional longer description.
            is_completed: Completion flag; defaults to ``False``.

        Returns:
            Todo: An unsaved ORM instance suitable for unit test assertions.
        """
        todo = Todo()
        todo.id = id
        todo.title = title
        todo.description = description
        todo.is_completed = is_completed
        todo.created_at = datetime(2026, 1, 1, 12, 0, 0)
        todo.updated_at = datetime(2026, 1, 1, 12, 0, 0)
        return todo

    return factory


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------


class TestGetAll:
    """Tests for :meth:`~app.repositories.todo_repository.TodoRepository.get_all`."""

    async def test_returns_empty_list_when_no_todos_exist(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_all returns [] when execute yields an empty result set."""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = await repo.get_all()

        assert result == []

    async def test_returns_all_todos_from_session(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """get_all returns the exact list produced by scalars().all()."""
        todo1 = make_todo(id=1, title="First")
        todo2 = make_todo(id=2, title="Second")
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            todo1,
            todo2,
        ]

        result = await repo.get_all()

        assert result == [todo1, todo2]

    async def test_returns_single_todo_in_list(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """get_all wraps a single row in a list, not returning the raw object."""
        solo = make_todo(id=5, title="Solo")
        mock_db.execute.return_value.scalars.return_value.all.return_value = [solo]

        result = await repo.get_all()

        assert result == [solo]
        assert len(result) == 1

    async def test_calls_execute_exactly_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_all issues exactly one SELECT statement per call."""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.get_all()

        mock_db.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    """Tests for :meth:`~app.repositories.todo_repository.TodoRepository.get_by_id`."""

    async def test_returns_todo_when_found(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """get_by_id returns the Todo instance when scalar_one_or_none finds a row."""
        todo = make_todo(id=3, title="Write docs")
        mock_db.execute.return_value.scalar_one_or_none.return_value = todo

        result = await repo.get_by_id(3)

        assert result is todo

    async def test_returns_none_when_not_found(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_by_id returns None when no row matches the given id."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await repo.get_by_id(999)

        assert result is None

    async def test_calls_execute_exactly_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """get_by_id issues exactly one SELECT statement per call."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = make_todo()

        await repo.get_by_id(1)

        mock_db.execute.assert_awaited_once()

    async def test_returns_correct_todo_for_given_id(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """get_by_id propagates the exact object returned by scalar_one_or_none."""
        expected = make_todo(id=42, title="Specific Todo")
        mock_db.execute.return_value.scalar_one_or_none.return_value = expected

        result = await repo.get_by_id(42)

        assert result is expected
        assert result.id == 42  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    """Tests for :meth:`~app.repositories.todo_repository.TodoRepository.create`."""

    async def test_add_is_called_with_todo_orm_instance(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create calls session.add() with a new Todo ORM instance."""
        payload = TodoCreate(title="New Task")

        await repo.create(payload)

        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, Todo)

    async def test_creates_todo_with_correct_title(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create builds a Todo whose title matches the payload."""
        payload = TodoCreate(title="Buy groceries")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.title == "Buy groceries"

    async def test_creates_todo_with_correct_description(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create builds a Todo whose description matches the payload."""
        payload = TodoCreate(title="Task with description", description="Milk and eggs")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.description == "Milk and eggs"

    async def test_creates_todo_with_none_description_when_omitted(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create sets description to None when the payload omits it."""
        payload = TodoCreate(title="No description here")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.description is None

    async def test_flush_is_awaited_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create awaits session.flush() exactly once to obtain server-assigned defaults."""
        payload = TodoCreate(title="Flush test")

        await repo.create(payload)

        mock_db.flush.assert_awaited_once()

    async def test_refresh_is_awaited_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create awaits session.refresh() exactly once after flushing."""
        payload = TodoCreate(title="Refresh test")

        await repo.create(payload)

        mock_db.refresh.assert_awaited_once()

    async def test_refresh_receives_the_created_todo_instance(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create passes the same Todo instance to both add() and refresh()."""
        payload = TodoCreate(title="Refresh arg test")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        refreshed = mock_db.refresh.call_args[0][0]
        assert added is refreshed

    async def test_add_flush_refresh_called_in_correct_order(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create calls add → flush → refresh in the correct order."""
        payload = TodoCreate(title="Order test")
        call_order: list[str] = []

        mock_db.add.side_effect = lambda _: call_order.append("add")

        async def flush_side_effect() -> None:
            call_order.append("flush")

        async def refresh_side_effect(instance: Todo) -> None:
            # Set id so the post-refresh logger.debug("%d") call succeeds.
            if getattr(instance, "id", None) is None:
                instance.id = 1
            call_order.append("refresh")

        mock_db.flush.side_effect = flush_side_effect
        mock_db.refresh.side_effect = refresh_side_effect

        await repo.create(payload)

        assert call_order == ["add", "flush", "refresh"]

    async def test_returns_todo_orm_instance(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create returns the Todo ORM instance that was added and refreshed."""
        payload = TodoCreate(title="Return test")

        result = await repo.create(payload)

        assert isinstance(result, Todo)

    async def test_returned_todo_is_same_instance_passed_to_add(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create returns the same object reference that was passed to session.add()."""
        payload = TodoCreate(title="Identity test")

        result = await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert result is added


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    """Tests for :meth:`~app.repositories.todo_repository.TodoRepository.update`."""

    async def test_sets_title_when_title_in_fields_set(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update applies a new title when title is present in model_fields_set."""
        todo = make_todo(id=1, title="Old Title")
        data = TodoUpdate(title="New Title")

        await repo.update(todo, data)

        assert todo.title == "New Title"

    async def test_sets_description_when_description_in_fields_set(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update applies a new description when it is present in model_fields_set."""
        todo = make_todo(id=1, title="Todo", description="Old desc")
        data = TodoUpdate(description="Updated description")

        await repo.update(todo, data)

        assert todo.description == "Updated description"

    async def test_clears_description_when_null_is_explicit(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update sets description to None when the payload explicitly sends null."""
        # Use model_validate so that 'description' appears in model_fields_set.
        todo = make_todo(id=1, title="Todo", description="Has a description")
        data = TodoUpdate.model_validate({"description": None})

        await repo.update(todo, data)

        assert todo.description is None

    async def test_sets_is_completed_when_in_fields_set(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update flips is_completed when it is present in model_fields_set."""
        todo = make_todo(id=1, title="Todo", is_completed=False)
        data = TodoUpdate(is_completed=True)

        await repo.update(todo, data)

        assert todo.is_completed is True

    async def test_does_not_touch_title_when_absent_from_fields_set(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update leaves title unchanged when only other fields are provided."""
        todo = make_todo(id=1, title="Untouched Title")
        data = TodoUpdate(is_completed=True)

        await repo.update(todo, data)

        assert todo.title == "Untouched Title"

    async def test_does_not_touch_description_when_absent_from_fields_set(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update leaves description unchanged when it is absent from model_fields_set."""
        todo = make_todo(id=1, title="Todo", description="Original description")
        data = TodoUpdate(title="New Title")

        await repo.update(todo, data)

        assert todo.description == "Original description"

    async def test_applies_multiple_fields_simultaneously(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update applies all supplied fields when multiple are provided at once."""
        todo = make_todo(
            id=1, title="Old", description="Old desc", is_completed=False
        )
        data = TodoUpdate(title="New", description="New desc", is_completed=True)

        await repo.update(todo, data)

        assert todo.title == "New"
        assert todo.description == "New desc"
        assert todo.is_completed is True

    async def test_no_fields_modified_when_fields_set_is_empty(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update leaves the todo unchanged when no fields were explicitly supplied."""
        todo = make_todo(id=1, title="Unchanged", description="Unchanged desc")
        data = TodoUpdate()  # model_fields_set will be empty

        assert "title" not in data.model_fields_set
        assert "description" not in data.model_fields_set

        await repo.update(todo, data)

        assert todo.title == "Unchanged"
        assert todo.description == "Unchanged desc"

    async def test_flush_is_awaited_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update awaits flush() once to propagate changes to the database."""
        data = TodoUpdate(title="Flushed")

        await repo.update(make_todo(), data)

        mock_db.flush.assert_awaited_once()

    async def test_refresh_is_awaited_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update awaits refresh() once to reload server-side timestamps."""
        data = TodoUpdate(title="Refreshed")

        await repo.update(make_todo(), data)

        mock_db.refresh.assert_awaited_once()

    async def test_refresh_is_called_with_the_todo_instance(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update passes the same todo instance it received to session.refresh()."""
        todo = make_todo(id=9)
        data = TodoUpdate(title="Refresh arg test")

        await repo.update(todo, data)

        mock_db.refresh.assert_awaited_once_with(todo)

    async def test_flush_called_before_refresh(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update awaits flush before refresh — correct post-write ordering."""
        todo = make_todo()
        data = TodoUpdate(title="Order test")
        call_order: list[str] = []

        async def flush_side_effect() -> None:
            call_order.append("flush")

        async def refresh_side_effect(_: Todo) -> None:
            call_order.append("refresh")

        mock_db.flush.side_effect = flush_side_effect
        mock_db.refresh.side_effect = refresh_side_effect

        await repo.update(todo, data)

        assert call_order == ["flush", "refresh"]

    async def test_returns_the_same_todo_instance(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """update returns the exact todo instance it was given."""
        todo = make_todo(id=5)
        data = TodoUpdate(title="Return me")

        result = await repo.update(todo, data)

        assert result is todo


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    """Tests for :meth:`~app.repositories.todo_repository.TodoRepository.delete`."""

    async def test_calls_session_delete_with_the_todo(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """delete passes the target todo instance to session.delete()."""
        todo = make_todo(id=10)

        await repo.delete(todo)

        mock_db.delete.assert_awaited_once_with(todo)

    async def test_flush_is_awaited_once(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """delete awaits flush() once to propagate the deletion to the database."""
        await repo.delete(make_todo(id=10))

        mock_db.flush.assert_awaited_once()

    async def test_delete_called_before_flush(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """delete marks the object for deletion before issuing flush."""
        todo = make_todo(id=10)
        call_order: list[str] = []

        async def delete_side_effect(_: Todo) -> None:
            call_order.append("delete")

        async def flush_side_effect() -> None:
            call_order.append("flush")

        mock_db.delete.side_effect = delete_side_effect
        mock_db.flush.side_effect = flush_side_effect

        await repo.delete(todo)

        assert call_order == ["delete", "flush"]

    async def test_refresh_is_not_called(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """delete never calls refresh — there is nothing to reload after a deletion."""
        await repo.delete(make_todo(id=10))

        mock_db.refresh.assert_not_called()

    async def test_returns_none(
        self,
        repo: TodoRepository,
        mock_db: AsyncMock,
        make_todo: Callable[..., Todo],
    ) -> None:
        """delete returns None — callers need no data back after a deletion."""
        result = await repo.delete(make_todo(id=10))

        assert result is None
