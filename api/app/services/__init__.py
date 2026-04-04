"""Public re-exports for the services package.

Import from ``app.services`` instead of the individual submodules:

    from app.services import TodoService, get_todo_service
"""

from app.services.todo_service import TodoService, get_todo_service

__all__ = [
    "TodoService",
    "get_todo_service",
]

