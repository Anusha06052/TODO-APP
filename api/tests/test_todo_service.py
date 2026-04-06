"""Unit tests for :class:`~app.services.todo_service.TodoService`.

All database I/O is eliminated by injecting a fully mocked
:class:`~app.repositories.todo_repository.TodoRepository`.  Tests focus
exclusively on the business logic enforced by the service layer:

* Correct delegation to repository methods.
* Transaction management (``commit`` / ``refresh`` ordering and call count).
* 404 :class:`~fastapi.HTTPException` raised when a todo is absent.
* Return values match the repository output without transformation.

Naming convention: ``test_<method>_<scenario>_<expected_outcome>``.
"""

from typing import Callable
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from fastapi import HTTPException, status

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.todo_service import TodoService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_repo() -> MagicMock:
    """Return a :class:`~unittest.mock.MagicMock` that mimics
    :class:`~app.repositories.todo_repository.TodoRepository`.

    All async repository methods are backed by :class:`~unittest.mock.AsyncMock`
    so they can be ``await``-ed without error.  The nested ``db`` attribute
    exposes ``commit`` and ``refresh`` as :class:`~unittest.mock.AsyncMock`
    instances, matching the surface that :class:`~app.services.todo_service.TodoService`
    calls for transaction management.

    Returns:
        MagicMock: A fully wired stand-in for ``TodoRepository``.
    """
    repo = MagicMock()
    repo.get_all = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()

    # Service commits / refreshes through repo.db (the underlying AsyncSession).
    repo.db = MagicMock()
    repo.db.commit = AsyncMock()
    repo.db.refresh = AsyncMock()

    return repo


@pytest.fixture()
def service(mock_repo: MagicMock) -> TodoService:
    """Return a :class:`~app.services.todo_service.TodoService` wired to
    :fixture:`mock_repo`.

    Args:
        mock_repo: The mocked repository injected at construction time.

    Returns:
        TodoService: A fully initialised service instance under test.
    """
    return TodoService(repo=mock_repo)


# ---------------------------------------------------------------------------
# get_all_todos
# ---------------------------------------------------------------------------


class TestGetAllTodos:
    """Tests for :meth:`~app.services.todo_service.TodoService.get_all_todos`."""

    async def test_returns_empty_list_when_no_todos_exist(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """get_all_todos returns [] when the repository returns an empty list."""
        mock_repo.get_all.return_value = []

        result = await service.get_all_todos()

        assert result == []

    async def test_returns_all_todos_from_repository(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """get_all_todos returns the exact list supplied by the repository."""
        todos = [todo_factory(id=1, title="Alpha"), todo_factory(id=2, title="Beta")]
        mock_repo.get_all.return_value = todos

        result = await service.get_all_todos()

        assert result == todos
        assert len(result) == 2

    async def test_returns_single_todo(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """get_all_todos returns a one-element list when only one todo exists."""
        todos = [todo_factory(id=1)]
        mock_repo.get_all.return_value = todos

        result = await service.get_all_todos()

        assert result == todos

    async def test_calls_repo_get_all_exactly_once(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """get_all_todos delegates to repo.get_all exactly once."""
        mock_repo.get_all.return_value = []

        await service.get_all_todos()

        mock_repo.get_all.assert_called_once_with()

    async def test_does_not_commit_or_refresh(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """get_all_todos must not mutate the database session."""
        mock_repo.get_all.return_value = []

        await service.get_all_todos()

        mock_repo.db.commit.assert_not_called()
        mock_repo.db.refresh.assert_not_called()


# ---------------------------------------------------------------------------
# get_todo_by_id
# ---------------------------------------------------------------------------


class TestGetTodoById:
    """Tests for :meth:`~app.services.todo_service.TodoService.get_todo_by_id`."""

    async def test_returns_todo_when_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """get_todo_by_id returns the todo returned by the repository."""
        todo = todo_factory(id=7, title="Buy milk")
        mock_repo.get_by_id.return_value = todo

        result = await service.get_todo_by_id(7)

        assert result is todo

    async def test_calls_repo_get_by_id_with_correct_id(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """get_todo_by_id forwards the requested id to repo.get_by_id."""
        mock_repo.get_by_id.return_value = todo_factory(id=42)

        await service.get_todo_by_id(42)

        mock_repo.get_by_id.assert_called_once_with(42)

    async def test_raises_404_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """get_todo_by_id raises HTTPException 404 when repo returns None."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_todo_by_id(99)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_raises_404_with_descriptive_detail(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """The 404 detail message includes the requested todo id."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_todo_by_id(5)

        assert "5" in exc_info.value.detail

    async def test_does_not_commit_or_refresh(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """get_todo_by_id must not mutate the database session."""
        mock_repo.get_by_id.return_value = todo_factory(id=1)

        await service.get_todo_by_id(1)

        mock_repo.db.commit.assert_not_called()
        mock_repo.db.refresh.assert_not_called()


# ---------------------------------------------------------------------------
# create_todo
# ---------------------------------------------------------------------------


class TestCreateTodo:
    """Tests for :meth:`~app.services.todo_service.TodoService.create_todo`."""

    async def test_returns_todo_created_by_repository(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo returns the ORM instance produced by repo.create."""
        created = todo_factory(id=10, title="Write docs")
        mock_repo.create.return_value = created

        payload = TodoCreate(title="Write docs")
        result = await service.create_todo(payload)

        assert result is created

    async def test_calls_repo_create_with_payload(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo passes the TodoCreate schema directly to repo.create."""
        mock_repo.create.return_value = todo_factory()

        payload = TodoCreate(title="Ship it", description="Deploy to prod")
        await service.create_todo(payload)

        mock_repo.create.assert_called_once_with(payload)

    async def test_calls_commit_after_create(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo commits the session exactly once after creating the todo."""
        mock_repo.create.return_value = todo_factory()

        await service.create_todo(TodoCreate(title="Commit me"))

        mock_repo.db.commit.assert_called_once()

    async def test_calls_refresh_on_created_todo(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo refreshes the exact ORM instance returned by repo.create."""
        created = todo_factory(id=3)
        mock_repo.create.return_value = created

        await service.create_todo(TodoCreate(title="Refresh me"))

        mock_repo.db.refresh.assert_called_once_with(created)

    async def test_commit_called_before_refresh(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo must commit before refreshing to see server-side defaults."""
        call_order: list[str] = []
        mock_repo.db.commit.side_effect = lambda: call_order.append("commit")
        mock_repo.db.refresh.side_effect = lambda _: call_order.append("refresh")
        mock_repo.create.return_value = todo_factory()

        await service.create_todo(TodoCreate(title="Order matters"))

        assert call_order == ["commit", "refresh"]

    async def test_create_todo_with_description(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo forwards the description field to repo.create unchanged."""
        mock_repo.create.return_value = todo_factory(description="Some detail")

        payload = TodoCreate(title="Detailed todo", description="Some detail")
        await service.create_todo(payload)

        mock_repo.create.assert_called_once_with(payload)

    async def test_create_todo_with_no_description(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """create_todo works when description is omitted (None by default)."""
        mock_repo.create.return_value = todo_factory()

        payload = TodoCreate(title="No description")
        await service.create_todo(payload)

        mock_repo.create.assert_called_once_with(payload)


# ---------------------------------------------------------------------------
# update_todo
# ---------------------------------------------------------------------------


class TestUpdateTodo:
    """Tests for :meth:`~app.services.todo_service.TodoService.update_todo`."""

    async def test_returns_updated_todo(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo returns the ORM instance produced by repo.update."""
        original = todo_factory(id=1, title="Old title")
        updated = todo_factory(id=1, title="New title")
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = updated

        result = await service.update_todo(1, TodoUpdate(title="New title"))

        assert result is updated

    async def test_raises_404_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """update_todo raises HTTPException 404 when the todo does not exist."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update_todo(99, TodoUpdate(title="Ghost update"))

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_raises_404_with_descriptive_detail(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """The 404 detail includes the todo id that was not found."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update_todo(77, TodoUpdate(title="Missing"))

        assert "77" in exc_info.value.detail

    async def test_calls_repo_get_by_id_with_correct_id(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo fetches the todo by the supplied id before updating."""
        original = todo_factory(id=5)
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = original

        await service.update_todo(5, TodoUpdate(is_completed=True))

        mock_repo.get_by_id.assert_called_once_with(5)

    async def test_calls_repo_update_with_fetched_todo_and_payload(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo passes both the fetched todo and the update schema to repo.update."""
        original = todo_factory(id=2, title="Original")
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = original

        data = TodoUpdate(title="Updated")
        await service.update_todo(2, data)

        mock_repo.update.assert_called_once_with(original, data)

    async def test_calls_commit_after_update(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo commits the session exactly once after updating."""
        original = todo_factory(id=1)
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = original

        await service.update_todo(1, TodoUpdate(is_completed=True))

        mock_repo.db.commit.assert_called_once()

    async def test_calls_refresh_on_updated_todo(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo refreshes the ORM instance returned by repo.update."""
        original = todo_factory(id=1, title="Before")
        updated = todo_factory(id=1, title="After")
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = updated

        await service.update_todo(1, TodoUpdate(title="After"))

        # Must refresh the *updated* instance, not the original.
        mock_repo.db.refresh.assert_called_once_with(updated)

    async def test_commit_called_before_refresh(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo must commit before refreshing to observe persisted changes."""
        call_order: list[str] = []
        mock_repo.db.commit.side_effect = lambda: call_order.append("commit")
        mock_repo.db.refresh.side_effect = lambda _: call_order.append("refresh")

        original = todo_factory(id=1)
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = original

        await service.update_todo(1, TodoUpdate(is_completed=True))

        assert call_order == ["commit", "refresh"]

    async def test_does_not_call_repo_update_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """update_todo must not call repo.update when the 404 guard fires."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.update_todo(99, TodoUpdate(title="Nope"))

        mock_repo.update.assert_not_called()

    async def test_does_not_commit_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """update_todo must not commit if the 404 guard fires."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.update_todo(99, TodoUpdate(title="Nope"))

        mock_repo.db.commit.assert_not_called()

    async def test_partial_update_passes_payload_with_only_provided_fields(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """update_todo forwards the exact schema object so repo can apply only
        model_fields_set fields — ensuring true PATCH semantics."""
        original = todo_factory(id=3)
        mock_repo.get_by_id.return_value = original
        mock_repo.update.return_value = original

        # Only is_completed is set — title and description must not be touched.
        data = TodoUpdate(is_completed=True)
        assert data.model_fields_set == {"is_completed"}

        await service.update_todo(3, data)

        _, call_data = mock_repo.update.call_args.args
        assert call_data is data
        assert call_data.model_fields_set == {"is_completed"}


# ---------------------------------------------------------------------------
# delete_todo
# ---------------------------------------------------------------------------


class TestDeleteTodo:
    """Tests for :meth:`~app.services.todo_service.TodoService.delete_todo`."""

    async def test_returns_none_on_success(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """delete_todo returns None when deletion completes successfully."""
        mock_repo.get_by_id.return_value = todo_factory(id=1)

        result = await service.delete_todo(1)

        assert result is None

    async def test_raises_404_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """delete_todo raises HTTPException 404 when the todo does not exist."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_todo(55)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_raises_404_with_descriptive_detail(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """The 404 detail includes the todo id that was not found."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_todo(88)

        assert "88" in exc_info.value.detail

    async def test_calls_repo_get_by_id_with_correct_id(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """delete_todo looks up the todo by the supplied id before deleting."""
        mock_repo.get_by_id.return_value = todo_factory(id=4)

        await service.delete_todo(4)

        mock_repo.get_by_id.assert_called_once_with(4)

    async def test_calls_repo_delete_with_fetched_todo(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """delete_todo passes the fetched ORM instance to repo.delete."""
        todo = todo_factory(id=6)
        mock_repo.get_by_id.return_value = todo

        await service.delete_todo(6)

        mock_repo.delete.assert_called_once_with(todo)

    async def test_calls_commit_after_delete(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """delete_todo commits the session exactly once after the deletion."""
        mock_repo.get_by_id.return_value = todo_factory(id=1)

        await service.delete_todo(1)

        mock_repo.db.commit.assert_called_once()

    async def test_does_not_call_repo_delete_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """delete_todo must not call repo.delete when the 404 guard fires."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.delete_todo(99)

        mock_repo.delete.assert_not_called()

    async def test_does_not_commit_when_todo_not_found(
        self,
        service: TodoService,
        mock_repo: MagicMock,
    ) -> None:
        """delete_todo must not commit if the 404 guard fires."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.delete_todo(99)

        mock_repo.db.commit.assert_not_called()

    async def test_does_not_refresh_after_delete(
        self,
        service: TodoService,
        mock_repo: MagicMock,
        todo_factory: Callable[..., Todo],
    ) -> None:
        """delete_todo must never call refresh — there is nothing to reload."""
        mock_repo.get_by_id.return_value = todo_factory(id=1)

        await service.delete_todo(1)

        mock_repo.db.refresh.assert_not_called()
