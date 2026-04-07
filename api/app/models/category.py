"""ORM model for the ``categories`` table.

Represents a category that can be assigned to one or more :class:`Todo` items.
The relationship back to ``Todo`` is defined here via ``back_populates`` so
that SQLAlchemy can resolve both sides of the association.
"""

import logging

from sqlalchemy import UniqueConstraint, func
from sqlalchemy.dialects.mssql import DATETIME2, NVARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

logger = logging.getLogger(__name__)


class Category(Base):
    """SQLAlchemy ORM model for the ``categories`` table.

    Attributes:
        id: Auto-incrementing primary key (IDENTITY in SQL Server).
        name: Display name of the category (max 100 characters, unique).
        description: Optional longer description (max 500 characters).
        created_at: UTC timestamp set automatically on INSERT.
        updated_at: UTC timestamp set automatically on INSERT and every UPDATE.
        todos: Back-reference to all :class:`~app.models.todo.Todo` items
            assigned to this category (lazy-loaded by default).
    """

    __tablename__ = "categories"

    __table_args__ = (
        # Case-insensitive uniqueness is enforced at the database level via
        # a filtered index in the Alembic migration; the constraint here
        # provides a standard unique index as a baseline.
        UniqueConstraint("name", name="uq_categories_name"),
        {"comment": "Lookup table of categories that can be assigned to todos."},
    )

    # Primary key — SQL Server uses IDENTITY for autoincrement.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        index=True,
        comment="Auto-incrementing surrogate key (SQL Server IDENTITY).",
    )

    # Name: required, Unicode, limited to 100 chars, unique.
    name: Mapped[str] = mapped_column(
        NVARCHAR(100),
        nullable=False,
        comment="Display name of the category (max 100 characters, unique).",
    )

    # Description: optional, Unicode, limited to 500 chars.
    description: Mapped[str | None] = mapped_column(
        NVARCHAR(500),
        nullable=True,
        comment="Optional description of the category (max 500 characters).",
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

    # One-to-many: a category has zero or more todos.
    # lazy="raise" prevents accidental sync lazy-loads in async context;
    # all callers must eagerly load this relationship via selectinload().
    todos: Mapped[list["Todo"]] = relationship(  # type: ignore[name-defined]
        "Todo",
        back_populates="category",
        lazy="raise",
    )

    def __repr__(self) -> str:
        """Return an unambiguous developer representation of the instance."""
        return (
            f"<Category id={self.id!r} name={self.name!r}>"
        )
