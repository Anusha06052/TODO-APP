"""Pydantic v2 schemas for the Todo resource.

Four schema classes cover every use-case:

* :class:`TodoBase`     — shared, validated fields inherited by Create/Response.
* :class:`TodoCreate`   — fields accepted when creating a new todo (POST body).
* :class:`TodoUpdate`   — all-optional fields for a partial update (PATCH body).
* :class:`TodoResponse` — the full representation returned to clients, including
                          optional nested :class:`~app.schemas.category.CategoryResponse`.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryResponse


class TodoBase(BaseModel):
    """Shared, validated fields for the Todo resource.

    Inherited by :class:`TodoCreate` and :class:`TodoResponse` to avoid
    duplicating field definitions and validators.

    Attributes:
        title: Short label for the todo (1–200 non-whitespace characters).
        description: Optional longer description (max 1 000 characters).
        category_id: Optional FK linking the todo to a category.
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    category_id: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        """Reject titles that consist entirely of whitespace.

        Args:
            value: The raw title string supplied by the caller.

        Returns:
            The stripped title string when it contains visible characters.

        Raises:
            ValueError: If the title is blank or contains only whitespace.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank or contain only whitespace")
        return stripped


class TodoCreate(TodoBase):
    """Validated payload for creating a new todo (POST body).

    Inherits ``title`` and ``description`` from :class:`TodoBase` with all
    their constraints.  No additional fields are required at creation time.
    """


class TodoUpdate(BaseModel):
    """Validated payload for partially updating an existing todo (PATCH body).

    All fields are optional — only the fields present in the request body are
    applied to the stored record.  Clients may omit any field they do not wish
    to change.

    Attributes:
        title: Replacement title (1–200 non-whitespace characters).
        description: Replacement description (max 1 000 characters); send
            ``null`` to clear the field.
        is_completed: New completion state.
        category_id: Replacement category FK; send ``null`` to unassign.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    is_completed: bool | None = None
    category_id: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        """Reject titles that consist entirely of whitespace when provided.

        Args:
            value: The raw title string supplied by the caller, or ``None``
                when the field is omitted from the PATCH body.

        Returns:
            The stripped title string, or ``None`` when the field was omitted.

        Raises:
            ValueError: If a non-null title is blank or contains only whitespace.
        """
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank or contain only whitespace")
        return stripped


class TodoResponse(TodoBase):
    """Full todo representation returned by the API.

    Extends :class:`TodoBase` with server-assigned fields that are not present
    in create/update payloads.  ``from_attributes=True`` allows direct
    construction from SQLAlchemy ORM model instances.

    Attributes:
        id: Auto-assigned primary key.
        is_completed: Whether the todo has been marked as done.
        created_at: UTC timestamp set automatically on INSERT.
        updated_at: UTC timestamp set automatically on INSERT and every UPDATE.
        category: Nested category representation; ``None`` when no category is
            assigned or the category has been soft-deleted.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse | None = None
