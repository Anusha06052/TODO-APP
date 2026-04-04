"""Public re-exports for the routes package.

Import from ``app.routes`` instead of the individual submodules:

    from app.routes import todos_router
"""

from app.routes.todos import router as todos_router

__all__ = [
    "todos_router",
]

