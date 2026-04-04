"""Shared declarative base for all SQLAlchemy ORM models.

All models in this application must inherit from :class:`Base` so that:

- Their metadata is registered on a single :class:`~sqlalchemy.MetaData`
  instance, which Alembic uses for autogenerate diff detection.
- Relationships, type-checking helpers, and future mixins (timestamps, soft
  delete, etc.) can be added here once and inherited project-wide.

Usage::

    from app.models.base import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        ...
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class shared by every ORM model in the application.

    Inheriting from :class:`~sqlalchemy.orm.DeclarativeBase` (SQLAlchemy 2.x
    style) gives each subclass a ``__table__`` attribute and registers it on
    ``Base.metadata``, which is the single source of truth for Alembic
    autogenerate migrations.
    """

    pass
