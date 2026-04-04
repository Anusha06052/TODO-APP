"""ORM model for the ``todos`` table.

Represents a single to-do item persisted in SQL Server.  No relationships are
defined here; the optional category association is added in Phase 3.
"""

import logging

from sqlalchemy import Boolean, func
from sqlalchemy.dialects.mssql import DATETIME2, NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

logger = logging.getLogger(__name__)


class Todo(Base):
    """SQLAlchemy ORM model for the ``todos`` table.

    Attributes:
        id: Auto-incrementing primary key (IDENTITY in SQL Server).
        title: Short title of the todo item (max 200 characters).
        description: Optional longer description (max 1 000 characters).
        is_completed: Whether the todo has been marked as done.
        created_at: UTC timestamp set automatically on INSERT.
        updated_at: UTC timestamp set automatically on INSERT and every UPDATE.
    """

    __tablename__ = "todos"

    # Primary key — SQL Server uses IDENTITY for autoincrement.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="Auto-incrementing surrogate key (SQL Server IDENTITY).",
    )

    # Title: required, Unicode, limited to 200 chars.
    title: Mapped[str] = mapped_column(
        NVARCHAR(200),
        nullable=False,
        comment="Short title of the todo item (max 200 characters).",
    )

    # Description: optional, Unicode, limited to 1 000 chars.
    description: Mapped[str | None] = mapped_column(
        NVARCHAR(1000),
        nullable=True,
        comment="Optional longer description (max 1 000 characters).",
    )

    # Completion flag: defaults to False on creation.
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="Whether the todo has been completed.",
    )

    # Created timestamp: set by the database on INSERT.
    created_at: Mapped[object] = mapped_column(
        DATETIME2,
        nullable=False,
        server_default=func.getutcdate(),
        comment="UTC timestamp of record creation (set by database).",
    )

    # Updated timestamp: set on INSERT and refreshed on every UPDATE.
    updated_at: Mapped[object] = mapped_column(
        DATETIME2,
        nullable=False,
        server_default=func.getutcdate(),
        onupdate=func.getutcdate(),
        comment="UTC timestamp of last update (maintained by database/ORM).",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"<Todo id={self.id!r} title={self.title!r} "
            f"is_completed={self.is_completed!r}>"
        )
