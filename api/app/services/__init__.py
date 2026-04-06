"""Public re-exports for the services package.

Import from ``app.services`` instead of the individual submodules:

    from app.services import TodoService, get_todo_service
"""

from app.dependencies.todo import get_todo_service
__all__ = [
    "get_todo_service",
]

