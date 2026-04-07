"""Pydantic v2 schemas for the Category resource.

Four schema classes cover every use-case:

* :class:`CategoryBase`     — shared, validated fields inherited by Create/Response.
* :class:`CategoryCreate`   — fields accepted when creating a new category (POST body).
* :class:`CategoryUpdate`   — all-optional fields for a partial update (PATCH body).
* :class:`CategoryResponse` — the full representation returned to clients.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    """Shared, validated fields for the Category resource.

    Inherited by :class:`CategoryCreate` and :class:`CategoryResponse` to avoid
    duplicating field definitions and validators.

    Attributes:
        name: Display name of the category (1–100 non-whitespace characters, unique).
        description: Optional longer description (max 500 characters).
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        """Reject names that consist entirely of whitespace.

        Args:
            value: The raw name string supplied by the caller.

        Returns:
            The stripped name string when it contains visible characters.

        Raises:
            ValueError: If the name is blank or contains only whitespace.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank or contain only whitespace")
        return stripped


class CategoryCreate(CategoryBase):
    """Validated payload for creating a new category (POST body).

    Inherits ``name`` and ``description`` from :class:`CategoryBase` with all
    their constraints.  No additional fields are required at creation time.
    """


class CategoryUpdate(BaseModel):
    """Validated payload for partially updating an existing category (PATCH body).

    All fields are optional — only the fields present in the request body are
    applied to the stored record.  Clients may omit any field they do not wish
    to change.

    Attributes:
        name: Replacement display name (1–100 non-whitespace characters, unique).
        description: Replacement description (max 500 characters); send
            ``null`` to clear the field.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str | None) -> str | None:
        """Reject names that consist entirely of whitespace when provided.

        Args:
            value: The raw name string supplied by the caller, or ``None``
                when the field is omitted from the PATCH body.

        Returns:
            The stripped name string, or ``None`` when the field was omitted.

        Raises:
            ValueError: If a non-null name is blank or contains only whitespace.
        """
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank or contain only whitespace")
        return stripped


class CategoryResponse(CategoryBase):
    """Full category representation returned by the API.

    Extends :class:`CategoryBase` with server-assigned fields that are not
    present in create/update payloads.  ``from_attributes=True`` allows direct
    construction from SQLAlchemy ORM model instances.

    Attributes:
        id: Auto-assigned primary key.
        created_at: UTC timestamp set automatically on INSERT.
        updated_at: UTC timestamp set automatically on INSERT and every UPDATE.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
