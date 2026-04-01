"""Pydantic schemas for the Todo resource.

Three separate schema classes model the three main use-cases:

* :class:`TodoCreate`   — fields accepted when creating a new todo.
* :class:`TodoUpdate`   — all-optional fields for a PATCH operation.
* :class:`TodoResponse` — the full representation returned to clients.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    """Validated payload for creating a new todo.

    Attributes:
        title: Short label for the todo (1–200 characters).
        description: Optional longer description (max 1 000 characters).
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class TodoUpdate(BaseModel):
    """Validated payload for partially updating an existing todo.

    All fields are optional — only the fields present in the request body are
    applied to the stored record.

    Attributes:
        title: Replacement title (1–200 characters).
        description: Replacement description (max 1 000 characters); pass
            ``null`` to clear the field.
        is_completed: New completion state.
    """

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_completed: bool | None = None


class TodoResponse(BaseModel):
    """Full todo representation returned by the API.

    Attributes:
        id: Auto-assigned primary key.
        title: Short label of the todo.
        description: Optional longer description.
        is_completed: Whether the todo has been completed.
        created_at: UTC timestamp of record creation.
        updated_at: UTC timestamp of the most recent update.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
