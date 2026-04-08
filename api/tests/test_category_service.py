"""Unit tests for :class:`~app.services.category_service.CategoryService`.

All database I/O is eliminated by injecting a fully mocked
:class:`~app.repositories.category_repository.CategoryRepository` (from the
shared ``mock_category_repo`` conftest fixture) and a mocked
:class:`~sqlalchemy.ext.asyncio.AsyncSession` (``mock_db``).  Tests focus
exclusively on the business logic enforced by the service layer:

* Correct delegation to repository methods with the right arguments.
* Transaction management — ``commit()`` and ``refresh()`` ordering and count.
* 404 :class:`~fastapi.HTTPException` raised when a category is absent.
* 409 :class:`~fastapi.HTTPException` raised on duplicate name (create/update).
* 409 is NOT raised when an update keeps the category's own existing name.
* Return values are :class:`~app.schemas.category.CategoryResponse` instances.
* Write-abort path: no ``commit`` / ``delete`` called when a guard raises.

Naming convention: ``test_<method>_<scenario>_<expected_outcome>``.
"""

from typing import Callable

import pytest
from fastapi import HTTPException, status
from unittest.mock import AsyncMock

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService


# ---------------------------------------------------------------------------
# service fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def service(mock_category_repo: AsyncMock, mock_db: AsyncMock) -> CategoryService:
    """Return a :class:`~app.services.category_service.CategoryService` wired
    to the shared mock repository and mock database session.

    Args:
        mock_category_repo: AsyncMock stand-in for ``CategoryRepository``.
        mock_db: AsyncMock stand-in for ``AsyncSession``.

    Returns:
        CategoryService: A fully initialised service instance under test.
    """
    return CategoryService(repo=mock_category_repo, db=mock_db)


# ===========================================================================
# get_all_categories
# ===========================================================================


class TestGetAllCategories:
    """Tests for :meth:`~app.services.category_service.CategoryService.get_all_categories`."""

    async def test_returns_empty_list_when_no_categories_exist(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """get_all_categories returns [] when the repository returns an empty list."""
        mock_category_repo.get_all.return_value = []

        result = await service.get_all_categories()

        assert result == []

    async def test_returns_list_of_category_responses(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """Each ORM object is converted to a CategoryResponse before returning."""
        cats = [
            category_factory(id=1, name="Work"),
            category_factory(id=2, name="Personal"),
        ]
        mock_category_repo.get_all.return_value = cats

        result = await service.get_all_categories()

        assert len(result) == 2
        assert all(isinstance(r, CategoryResponse) for r in result)

    async def test_response_fields_match_orm_instance(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """id and name on the response match the source ORM object."""
        cat = category_factory(id=7, name="Errands", description="Quick errands")
        mock_category_repo.get_all.return_value = [cat]

        result = await service.get_all_categories()

        assert result[0].id == 7
        assert result[0].name == "Errands"
        assert result[0].description == "Quick errands"

    async def test_calls_repo_get_all_exactly_once(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """get_all_categories delegates to repo.get_all exactly once."""
        mock_category_repo.get_all.return_value = []

        await service.get_all_categories()

        mock_category_repo.get_all.assert_called_once_with()

    async def test_does_not_commit_or_refresh(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """A read operation must not mutate the database session."""
        mock_category_repo.get_all.return_value = []

        await service.get_all_categories()

        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()


# ===========================================================================
# get_category_by_id
# ===========================================================================


class TestGetCategoryById:
    """Tests for :meth:`~app.services.category_service.CategoryService.get_category_by_id`."""

    async def test_returns_category_response_when_found(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """A found category is returned as a CategoryResponse."""
        cat = category_factory(id=3, name="Work")
        mock_category_repo.get_by_id.return_value = cat

        result = await service.get_category_by_id(3)

        assert isinstance(result, CategoryResponse)
        assert result.id == 3
        assert result.name == "Work"

    async def test_calls_repo_get_by_id_with_correct_id(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """The requested id is forwarded verbatim to repo.get_by_id."""
        mock_category_repo.get_by_id.return_value = category_factory(id=10)

        await service.get_category_by_id(10)

        mock_category_repo.get_by_id.assert_called_once_with(10)

    async def test_raises_404_when_category_not_found(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """get_category_by_id raises HTTPException 404 when repo returns None."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_category_by_id(99)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_raises_404_detail_contains_requested_id(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """The 404 detail message includes the missing id for traceability."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_category_by_id(99)

        assert "99" in exc_info.value.detail

    async def test_does_not_commit_on_read(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """A successful read must not commit the session."""
        mock_category_repo.get_by_id.return_value = category_factory(id=1)

        await service.get_category_by_id(1)

        mock_db.commit.assert_not_called()


# ===========================================================================
# create_category
# ===========================================================================


class TestCreateCategory:
    """Tests for :meth:`~app.services.category_service.CategoryService.create_category`."""

    async def test_raises_409_when_name_already_exists(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """A duplicate name triggers a 409 Conflict before any INSERT."""
        mock_category_repo.get_by_name.return_value = category_factory(
            id=99, name=sample_category_create_dto.name
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_category(sample_category_create_dto)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    async def test_409_detail_contains_duplicate_name(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """The 409 detail message includes the conflicting name."""
        mock_category_repo.get_by_name.return_value = category_factory(
            id=99, name=sample_category_create_dto.name
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_category(sample_category_create_dto)

        assert sample_category_create_dto.name in exc_info.value.detail

    async def test_does_not_call_repo_create_when_name_conflicts(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """repo.create must not be called when a duplicate name is detected."""
        mock_category_repo.get_by_name.return_value = category_factory(id=99)

        with pytest.raises(HTTPException):
            await service.create_category(sample_category_create_dto)

        mock_category_repo.create.assert_not_called()

    async def test_does_not_commit_when_name_conflicts(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """The session must not be committed when a 409 is raised."""
        mock_category_repo.get_by_name.return_value = category_factory(id=99)

        with pytest.raises(HTTPException):
            await service.create_category(sample_category_create_dto)

        mock_db.commit.assert_not_called()

    async def test_checks_uniqueness_before_inserting(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """repo.get_by_name is called with the payload name before repo.create."""
        mock_category_repo.get_by_name.return_value = None
        created = category_factory(id=5, name=sample_category_create_dto.name)
        mock_category_repo.create.return_value = created

        await service.create_category(sample_category_create_dto)

        mock_category_repo.get_by_name.assert_called_once_with(
            sample_category_create_dto.name
        )

    async def test_calls_repo_create_with_payload(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """repo.create receives the original CategoryCreate payload unchanged."""
        mock_category_repo.get_by_name.return_value = None
        created = category_factory(id=5, name=sample_category_create_dto.name)
        mock_category_repo.create.return_value = created

        await service.create_category(sample_category_create_dto)

        mock_category_repo.create.assert_called_once_with(sample_category_create_dto)

    async def test_commits_after_create(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """The session is committed exactly once after a successful create."""
        mock_category_repo.get_by_name.return_value = None
        created = category_factory(id=5, name=sample_category_create_dto.name)
        mock_category_repo.create.return_value = created

        await service.create_category(sample_category_create_dto)

        mock_db.commit.assert_called_once()

    async def test_refreshes_created_instance_after_commit(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """db.refresh is called with the exact ORM object returned by repo.create."""
        mock_category_repo.get_by_name.return_value = None
        created = category_factory(id=5, name=sample_category_create_dto.name)
        mock_category_repo.create.return_value = created

        await service.create_category(sample_category_create_dto)

        mock_db.refresh.assert_called_once_with(created)

    async def test_commit_is_called_before_refresh(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """commit must precede refresh in the write transaction sequence."""
        call_order: list[str] = []

        async def record_commit() -> None:
            call_order.append("commit")

        async def record_refresh(_: object) -> None:
            call_order.append("refresh")

        mock_db.commit.side_effect = record_commit
        mock_db.refresh.side_effect = record_refresh
        mock_category_repo.get_by_name.return_value = None
        created = category_factory(id=5, name=sample_category_create_dto.name)
        mock_category_repo.create.return_value = created

        await service.create_category(sample_category_create_dto)

        assert call_order == ["commit", "refresh"]

    async def test_returns_category_response(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
        sample_category_create_dto: CategoryCreate,
    ) -> None:
        """A successful create returns a fully populated CategoryResponse."""
        mock_category_repo.get_by_name.return_value = None
        created = category_factory(id=5, name=sample_category_create_dto.name)
        mock_category_repo.create.return_value = created

        result = await service.create_category(sample_category_create_dto)

        assert isinstance(result, CategoryResponse)
        assert result.id == 5
        assert result.name == sample_category_create_dto.name


# ===========================================================================
# update_category
# ===========================================================================


class TestUpdateCategory:
    """Tests for :meth:`~app.services.category_service.CategoryService.update_category`."""

    async def test_raises_404_when_category_not_found(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """update_category raises 404 when the target category does not exist."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update_category(99, CategoryUpdate(name="New"))

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_404_detail_contains_requested_id(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """The 404 detail message includes the missing category id."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update_category(99, CategoryUpdate(name="New"))

        assert "99" in exc_info.value.detail

    async def test_raises_409_when_new_name_taken_by_different_category(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """A name already used by a *different* category results in 409 Conflict."""
        own_cat = category_factory(id=1, name="Work")
        other_cat = category_factory(id=2, name="Personal")
        mock_category_repo.get_by_id.return_value = own_cat
        mock_category_repo.get_by_name.return_value = other_cat

        with pytest.raises(HTTPException) as exc_info:
            await service.update_category(1, CategoryUpdate(name="Personal"))

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    async def test_409_detail_contains_conflicting_name(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """The 409 detail message includes the conflicting name."""
        own_cat = category_factory(id=1, name="Work")
        other_cat = category_factory(id=2, name="Personal")
        mock_category_repo.get_by_id.return_value = own_cat
        mock_category_repo.get_by_name.return_value = other_cat

        with pytest.raises(HTTPException) as exc_info:
            await service.update_category(1, CategoryUpdate(name="Personal"))

        assert "Personal" in exc_info.value.detail

    async def test_allows_keeping_own_existing_name(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """No 409 is raised when the same name belongs to the category being updated."""
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        mock_category_repo.get_by_name.return_value = cat  # same id — own name
        updated = category_factory(id=1, name="Work")
        mock_category_repo.update.return_value = updated

        result = await service.update_category(1, CategoryUpdate(name="Work"))

        assert isinstance(result, CategoryResponse)

    async def test_skips_name_uniqueness_check_when_name_not_in_payload(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """repo.get_by_name is not called when the PATCH body omits the name field."""
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        updated = category_factory(id=1, name="Work", description="Updated desc")
        mock_category_repo.update.return_value = updated

        await service.update_category(1, CategoryUpdate(description="Updated desc"))

        mock_category_repo.get_by_name.assert_not_called()

    async def test_calls_repo_update_with_category_and_payload(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """repo.update is called with the fetched category and the exact update payload."""
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        mock_category_repo.get_by_name.return_value = None
        updated = category_factory(id=1, name="NewWork")
        mock_category_repo.update.return_value = updated
        payload = CategoryUpdate(name="NewWork")

        await service.update_category(1, payload)

        mock_category_repo.update.assert_called_once_with(cat, payload)

    async def test_commits_after_update(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """The session is committed exactly once after a successful update."""
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        mock_category_repo.get_by_name.return_value = None
        mock_category_repo.update.return_value = category_factory(id=1, name="NewWork")

        await service.update_category(1, CategoryUpdate(name="NewWork"))

        mock_db.commit.assert_called_once()

    async def test_refreshes_updated_instance_after_commit(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """db.refresh is called with the exact ORM object returned by repo.update."""
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        mock_category_repo.get_by_name.return_value = None
        updated = category_factory(id=1, name="NewWork")
        mock_category_repo.update.return_value = updated

        await service.update_category(1, CategoryUpdate(name="NewWork"))

        mock_db.refresh.assert_called_once_with(updated)

    async def test_commit_is_called_before_refresh(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """commit must precede refresh in the update transaction sequence."""
        call_order: list[str] = []

        async def record_commit() -> None:
            call_order.append("commit")

        async def record_refresh(_: object) -> None:
            call_order.append("refresh")

        mock_db.commit.side_effect = record_commit
        mock_db.refresh.side_effect = record_refresh
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        mock_category_repo.get_by_name.return_value = None
        mock_category_repo.update.return_value = category_factory(id=1, name="NewWork")

        await service.update_category(1, CategoryUpdate(name="NewWork"))

        assert call_order == ["commit", "refresh"]

    async def test_returns_category_response(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """A successful update returns a CategoryResponse reflecting the new values."""
        cat = category_factory(id=1, name="Work")
        mock_category_repo.get_by_id.return_value = cat
        mock_category_repo.get_by_name.return_value = None
        updated = category_factory(id=1, name="NewWork")
        mock_category_repo.update.return_value = updated

        result = await service.update_category(1, CategoryUpdate(name="NewWork"))

        assert isinstance(result, CategoryResponse)
        assert result.id == 1
        assert result.name == "NewWork"

    async def test_does_not_commit_when_404_on_update(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """The session must not be committed when the target category is not found."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.update_category(99, CategoryUpdate(name="X"))

        mock_db.commit.assert_not_called()

    async def test_does_not_commit_when_409_on_update(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """The session must not be committed when a name conflict is detected."""
        own_cat = category_factory(id=1, name="Work")
        other_cat = category_factory(id=2, name="Personal")
        mock_category_repo.get_by_id.return_value = own_cat
        mock_category_repo.get_by_name.return_value = other_cat

        with pytest.raises(HTTPException):
            await service.update_category(1, CategoryUpdate(name="Personal"))

        mock_db.commit.assert_not_called()


# ===========================================================================
# delete_category
# ===========================================================================


class TestDeleteCategory:
    """Tests for :meth:`~app.services.category_service.CategoryService.delete_category`."""

    async def test_raises_404_when_category_not_found(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """delete_category raises 404 when the target category does not exist."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_category(99)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    async def test_404_detail_contains_requested_id(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """The 404 detail message includes the missing category id."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_category(42)

        assert "42" in exc_info.value.detail

    async def test_calls_repo_delete_with_correct_category(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """repo.delete is called with the ORM object returned by get_by_id."""
        cat = category_factory(id=3, name="Work")
        mock_category_repo.get_by_id.return_value = cat

        await service.delete_category(3)

        mock_category_repo.delete.assert_called_once_with(cat)

    async def test_commits_after_delete(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """The session is committed exactly once after a successful delete."""
        cat = category_factory(id=3, name="Work")
        mock_category_repo.get_by_id.return_value = cat

        await service.delete_category(3)

        mock_db.commit.assert_called_once()

    async def test_does_not_call_repo_delete_when_404(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
    ) -> None:
        """repo.delete must not be called when the 404 guard fires."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.delete_category(99)

        mock_category_repo.delete.assert_not_called()

    async def test_does_not_commit_when_404(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """The session must not be committed when the 404 guard fires."""
        mock_category_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await service.delete_category(99)

        mock_db.commit.assert_not_called()

    async def test_returns_none_on_success(
        self,
        service: CategoryService,
        mock_category_repo: AsyncMock,
        mock_db: AsyncMock,
        category_factory: Callable[..., Category],
    ) -> None:
        """A successful delete returns None (maps to HTTP 204 No Content)."""
        cat = category_factory(id=3, name="Work")
        mock_category_repo.get_by_id.return_value = cat

        result = await service.delete_category(3)

        assert result is None
