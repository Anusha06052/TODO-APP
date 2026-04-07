"""Public re-exports for the models package.

All models are imported here so that:

- Alembic autogenerate detects every table via ``Base.metadata``.
- The rest of the app can import from ``app.models`` directly:

    from app.models import Todo
"""

from app.models.category import Category  # noqa: F401
from app.models.todo import Todo  # noqa: F401

__all__ = [
    "Category",
    "Todo",
]

