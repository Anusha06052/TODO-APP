"""Unit tests for :class:`~app.repositories.category_repository.CategoryRepository`.

All database I/O is replaced with a fully mocked
:class:`~sqlalchemy.ext.asyncio.AsyncSession`.  Tests verify that:

* The correct session methods are called in the correct order.
* ``flush()`` and ``refresh()`` are invoked after every write operation.
* Return values are derived from what the mock session produces.
* ``update()`` applies **only** the fields present in ``model_fields_set``,
  leaving untouched fields unchanged.
* ``count_todos()`` returns the integer scalar from the session result.
* ``delete()`` awaits both ``session.delete()`` and then ``flush()``.

No real database connection is required; the entire suite runs in-process.

Naming convention: ``test_<method>_<scenario>_<expected_outcome>``.
"""

from datetime import datetime
from typing import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


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

    ``execute.return_value`` is replaced with a :class:`~unittest.mock.MagicMock`
    so that synchronous access chains such as ``result.scalars().all()``,
    ``result.scalar_one_or_none()``, and ``result.scalar_one()`` return plain
    values instead of coroutine objects.

    ``refresh`` is given a default ``side_effect`` that assigns ``id = 1`` when
    the refreshed instance has no id yet, simulating the database assigning an
    auto-increment primary key after a flush.

    Scope — ``"function"``:
        A fresh mock is constructed per test to prevent recorded calls and
        configured return values from bleeding across tests.

    Returns:
        AsyncMock: Configured stand-in for ``AsyncSession``.
    """
    session = AsyncMock()

    # AsyncSession.add() is synchronous — override the default AsyncMock.
    session.add = MagicMock()

    # Replace the execute return value so sync chained calls work correctly.
    session.execute.return_value = MagicMock()

    # Simulate the database assigning a primary key after flush + refresh.
    async def _default_refresh(instance: object) -> None:
        if getattr(instance, "id", None) is None:
            instance.id = 1  # type: ignore[union-attr]

    session.refresh.side_effect = _default_refresh
    return session


@pytest.fixture()
def repo(mock_db: AsyncMock) -> CategoryRepository:
    """Return a :class:`~app.repositories.category_repository.CategoryRepository`
    wired to :fixture:`mock_db`.

    Args:
        mock_db: Mocked async session injected at construction time.

    Returns:
        CategoryRepository: Instance under test.
    """
    return CategoryRepository(db=mock_db)


@pytest.fixture()
def make_category() -> Callable[..., Category]:
    """Return a factory that constructs :class:`~app.models.category.Category`
    ORM instances with sensible, deterministic defaults.

    Usage::

        def test_something(make_category):
            cat = make_category(id=3, name="Work")
            assert cat.name == "Work"

    Returns:
        Callable: Factory that produces :class:`~app.models.category.Category` instances.
    """

    def factory(
        id: int = 1,
        name: str = "Personal",
        description: str | None = None,
    ) -> Category:
        """Construct a :class:`~app.models.category.Category` with the given values.

        Args:
            id: Primary key assigned to the instance.
            name: Display name (not validated here).
            description: Optional longer description.

        Returns:
            Category: An unsaved ORM instance suitable for unit test assertions.
        """
        cat = Category()
        cat.id = id
        cat.name = name
        cat.description = description
        cat.created_at = datetime(2026, 1, 1, 12, 0, 0)
        cat.updated_at = datetime(2026, 1, 1, 12, 0, 0)
        return cat

    return factory


# ===========================================================================
# get_all
# ===========================================================================


class TestGetAll:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.get_all`."""

    async def test_returns_empty_list_when_no_categories_exist(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_all returns [] when execute yields an empty result set."""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = await repo.get_all()

        assert result == []

    async def test_returns_all_categories_from_session(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_all returns the exact list produced by scalars().all()."""
        cat1 = make_category(id=1, name="Personal")
        cat2 = make_category(id=2, name="Work")
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            cat1,
            cat2,
        ]

        result = await repo.get_all()

        assert result == [cat1, cat2]

    async def test_returns_single_category_in_list(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_all wraps a single row in a list, not returning the raw object."""
        solo = make_category(id=5, name="Errands")
        mock_db.execute.return_value.scalars.return_value.all.return_value = [solo]

        result = await repo.get_all()

        assert result == [solo]
        assert len(result) == 1

    async def test_calls_execute_exactly_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_all issues exactly one SELECT statement per call."""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        await repo.get_all()

        mock_db.execute.assert_awaited_once()


# ===========================================================================
# get_by_id
# ===========================================================================


class TestGetById:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.get_by_id`."""

    async def test_returns_category_when_found(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_by_id returns the Category instance when scalar_one_or_none finds a row."""
        cat = make_category(id=3, name="Work")
        mock_db.execute.return_value.scalar_one_or_none.return_value = cat

        result = await repo.get_by_id(3)

        assert result is cat

    async def test_returns_none_when_not_found(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_by_id returns None when no row matches the given id."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await repo.get_by_id(999)

        assert result is None

    async def test_calls_execute_exactly_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_by_id issues exactly one SELECT statement per call."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = make_category()

        await repo.get_by_id(1)

        mock_db.execute.assert_awaited_once()

    async def test_propagates_exact_object_from_session(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_by_id returns the exact object reference from scalar_one_or_none."""
        expected = make_category(id=42, name="Specific")
        mock_db.execute.return_value.scalar_one_or_none.return_value = expected

        result = await repo.get_by_id(42)

        assert result is expected
        assert result.id == 42  # type: ignore[union-attr]


# ===========================================================================
# get_by_name
# ===========================================================================


class TestGetByName:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.get_by_name`."""

    async def test_returns_category_when_name_found(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_by_name returns the Category instance when matching name is found."""
        cat = make_category(id=1, name="Work")
        mock_db.execute.return_value.scalar_one_or_none.return_value = cat

        result = await repo.get_by_name("Work")

        assert result is cat

    async def test_returns_none_when_name_not_found(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """get_by_name returns None when no row matches the given name."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await repo.get_by_name("Nonexistent")

        assert result is None

    async def test_calls_execute_exactly_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_by_name issues exactly one SELECT statement per call."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = make_category()

        await repo.get_by_name("Personal")

        mock_db.execute.assert_awaited_once()

    async def test_propagates_exact_object_from_session(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """get_by_name returns the exact object reference from scalar_one_or_none."""
        expected = make_category(id=5, name="Hobbies")
        mock_db.execute.return_value.scalar_one_or_none.return_value = expected

        result = await repo.get_by_name("Hobbies")

        assert result is expected


# ===========================================================================
# count_todos
# ===========================================================================


class TestCountTodos:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.count_todos`."""

    async def test_returns_zero_when_no_todos_assigned(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """count_todos returns 0 when the category has no assigned todos."""
        mock_db.execute.return_value.scalar_one.return_value = 0

        result = await repo.count_todos(category_id=1)

        assert result == 0

    async def test_returns_correct_count_when_todos_assigned(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """count_todos returns the integer scalar returned by the session."""
        mock_db.execute.return_value.scalar_one.return_value = 5

        result = await repo.count_todos(category_id=2)

        assert result == 5

    async def test_returns_single_todo_count(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """count_todos returns 1 when exactly one todo is assigned."""
        mock_db.execute.return_value.scalar_one.return_value = 1

        result = await repo.count_todos(category_id=3)

        assert result == 1

    async def test_calls_execute_exactly_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """count_todos issues exactly one SELECT COUNT statement per call."""
        mock_db.execute.return_value.scalar_one.return_value = 0

        await repo.count_todos(category_id=1)

        mock_db.execute.assert_awaited_once()


# ===========================================================================
# create
# ===========================================================================


class TestCreate:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.create`."""

    async def test_add_is_called_with_category_orm_instance(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create calls session.add() with a new Category ORM instance."""
        payload = CategoryCreate(name="Work")

        await repo.create(payload)

        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, Category)

    async def test_creates_category_with_correct_name(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create builds a Category whose name matches the payload."""
        payload = CategoryCreate(name="Hobbies")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.name == "Hobbies"

    async def test_creates_category_with_correct_description(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create builds a Category whose description matches the payload."""
        payload = CategoryCreate(name="Work", description="Office tasks")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.description == "Office tasks"

    async def test_creates_category_with_none_description_when_omitted(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create sets description to None when the payload omits it."""
        payload = CategoryCreate(name="No Description")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.description is None

    async def test_flush_is_awaited_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create awaits session.flush() exactly once to obtain server-assigned defaults."""
        payload = CategoryCreate(name="Flush test")

        await repo.create(payload)

        mock_db.flush.assert_awaited_once()

    async def test_refresh_is_awaited_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create awaits session.refresh() exactly once after flushing."""
        payload = CategoryCreate(name="Refresh test")

        await repo.create(payload)

        mock_db.refresh.assert_awaited_once()

    async def test_refresh_receives_the_created_category_instance(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create passes the same Category instance to both add() and refresh()."""
        payload = CategoryCreate(name="Refresh arg test")

        await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        refreshed = mock_db.refresh.call_args[0][0]
        assert added is refreshed

    async def test_add_flush_refresh_called_in_correct_order(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create calls add → flush → refresh in the correct order."""
        payload = CategoryCreate(name="Order test")
        call_order: list[str] = []

        mock_db.add.side_effect = lambda _: call_order.append("add")

        async def flush_side_effect() -> None:
            call_order.append("flush")

        async def refresh_side_effect(instance: Category) -> None:
            if getattr(instance, "id", None) is None:
                instance.id = 1
            call_order.append("refresh")

        mock_db.flush.side_effect = flush_side_effect
        mock_db.refresh.side_effect = refresh_side_effect

        await repo.create(payload)

        assert call_order == ["add", "flush", "refresh"]

    async def test_returns_category_orm_instance(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create returns a Category ORM instance."""
        payload = CategoryCreate(name="Return test")

        result = await repo.create(payload)

        assert isinstance(result, Category)

    async def test_returned_category_is_same_instance_passed_to_add(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
    ) -> None:
        """create returns the same object reference that was passed to session.add()."""
        payload = CategoryCreate(name="Identity test")

        result = await repo.create(payload)

        added = mock_db.add.call_args[0][0]
        assert result is added


# ===========================================================================
# update
# ===========================================================================


class TestUpdate:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.update`."""

    async def test_sets_name_when_name_in_fields_set(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update applies a new name when name is present in model_fields_set."""
        cat = make_category(id=1, name="Old Name")
        data = CategoryUpdate(name="New Name")

        await repo.update(cat, data)

        assert cat.name == "New Name"

    async def test_sets_description_when_description_in_fields_set(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update applies a new description when it is present in model_fields_set."""
        cat = make_category(id=1, name="Work", description="Old desc")
        data = CategoryUpdate(description="Updated description")

        await repo.update(cat, data)

        assert cat.description == "Updated description"

    async def test_clears_description_when_null_is_explicit(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update sets description to None when the payload explicitly sends null."""
        cat = make_category(id=1, name="Work", description="Has a description")
        data = CategoryUpdate.model_validate({"description": None})

        await repo.update(cat, data)

        assert cat.description is None

    async def test_does_not_touch_name_when_absent_from_fields_set(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update leaves name unchanged when only description is provided."""
        cat = make_category(id=1, name="Untouched Name")
        data = CategoryUpdate(description="New desc")

        await repo.update(cat, data)

        assert cat.name == "Untouched Name"

    async def test_does_not_touch_description_when_absent_from_fields_set(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update leaves description unchanged when only name is provided."""
        cat = make_category(id=1, name="Work", description="Original description")
        data = CategoryUpdate(name="New Work")

        await repo.update(cat, data)

        assert cat.description == "Original description"

    async def test_applies_both_fields_simultaneously(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update applies all supplied fields when multiple are provided at once."""
        cat = make_category(id=1, name="Old", description="Old desc")
        data = CategoryUpdate(name="New", description="New desc")

        await repo.update(cat, data)

        assert cat.name == "New"
        assert cat.description == "New desc"

    async def test_no_fields_modified_when_fields_set_is_empty(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update leaves the category unchanged when no fields were explicitly supplied."""
        cat = make_category(id=1, name="Unchanged", description="Unchanged desc")
        data = CategoryUpdate()

        assert "name" not in data.model_fields_set
        assert "description" not in data.model_fields_set

        await repo.update(cat, data)

        assert cat.name == "Unchanged"
        assert cat.description == "Unchanged desc"

    async def test_flush_is_awaited_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update awaits flush() once to propagate changes to the database."""
        data = CategoryUpdate(name="Flushed")

        await repo.update(make_category(), data)

        mock_db.flush.assert_awaited_once()

    async def test_refresh_is_awaited_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update awaits refresh() once to reload server-side timestamps."""
        data = CategoryUpdate(name="Refreshed")

        await repo.update(make_category(), data)

        mock_db.refresh.assert_awaited_once()

    async def test_refresh_is_called_with_the_category_instance(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update passes the same category instance it received to session.refresh()."""
        cat = make_category(id=9)
        data = CategoryUpdate(name="Refresh arg test")

        await repo.update(cat, data)

        mock_db.refresh.assert_awaited_once_with(cat)

    async def test_flush_called_before_refresh(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update awaits flush before refresh — correct post-write ordering."""
        cat = make_category()
        data = CategoryUpdate(name="Order test")
        call_order: list[str] = []

        async def flush_side_effect() -> None:
            call_order.append("flush")

        async def refresh_side_effect(_: Category) -> None:
            call_order.append("refresh")

        mock_db.flush.side_effect = flush_side_effect
        mock_db.refresh.side_effect = refresh_side_effect

        await repo.update(cat, data)

        assert call_order == ["flush", "refresh"]

    async def test_returns_the_same_category_instance(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """update returns the exact category instance it was given."""
        cat = make_category(id=5)
        data = CategoryUpdate(name="Return me")

        result = await repo.update(cat, data)

        assert result is cat


# ===========================================================================
# delete
# ===========================================================================


class TestDelete:
    """Tests for :meth:`~app.repositories.category_repository.CategoryRepository.delete`."""

    async def test_calls_session_delete_with_the_category(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """delete passes the target category instance to session.delete()."""
        cat = make_category(id=10)

        await repo.delete(cat)

        mock_db.delete.assert_awaited_once_with(cat)

    async def test_flush_is_awaited_once(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """delete awaits flush() once to propagate the deletion to the database."""
        await repo.delete(make_category(id=10))

        mock_db.flush.assert_awaited_once()

    async def test_delete_called_before_flush(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """delete marks the object for deletion before issuing flush."""
        cat = make_category(id=10)
        call_order: list[str] = []

        async def delete_side_effect(_: Category) -> None:
            call_order.append("delete")

        async def flush_side_effect() -> None:
            call_order.append("flush")

        mock_db.delete.side_effect = delete_side_effect
        mock_db.flush.side_effect = flush_side_effect

        await repo.delete(cat)

        assert call_order == ["delete", "flush"]

    async def test_refresh_is_not_called(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """delete never calls refresh — there is nothing to reload after a deletion."""
        await repo.delete(make_category(id=10))

        mock_db.refresh.assert_not_called()

    async def test_returns_none(
        self,
        repo: CategoryRepository,
        mock_db: AsyncMock,
        make_category: Callable[..., Category],
    ) -> None:
        """delete returns None — callers need no data back after a deletion."""
        result = await repo.delete(make_category(id=10))

        assert result is None
