"""HTTP routing layer for the Todo resource.

Defines a single :data:`router` with all five CRUD endpoints.  Each handler
delegates immediately to :class:`~app.services.todo_service.TodoService` —
no business logic or database access lives here.
"""

import logging

from fastapi import APIRouter, Depends, Response, status
from typing import Annotated

from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate
from app.services.todo_service import TodoService, get_todo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
async def list_todos(
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> list[TodoResponse]:
    """Return all todos ordered by creation date descending.

    HTTP contract:
        GET /todos
        200 OK — body is a JSON array of :class:`~app.schemas.todo.TodoResponse`
        objects.  Returns an empty array when no todos exist.
    """
    logger.debug("GET /todos requested")
    return await service.get_all_todos()


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    """Create a new todo from the supplied payload.

    HTTP contract:
        POST /todos
        Request body: :class:`~app.schemas.todo.TodoCreate` JSON.
        201 Created — body is the newly created
        :class:`~app.schemas.todo.TodoResponse`.
        422 Unprocessable Entity — body fails Pydantic validation.
    """
    logger.debug("POST /todos requested")
    return await service.create_todo(payload)


@router.get("/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def get_todo(
    todo_id: int,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    """Retrieve a single todo by its primary key.

    HTTP contract:
        GET /todos/{todo_id}
        200 OK — body is the matching :class:`~app.schemas.todo.TodoResponse`.
        404 Not Found — no todo exists with the given ``todo_id``.
    """
    logger.debug("GET /todos/%d requested", todo_id)
    return await service.get_todo_by_id(todo_id)


@router.patch("/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    """Partially update an existing todo.

    HTTP contract:
        PATCH /todos/{todo_id}
        Request body: :class:`~app.schemas.todo.TodoUpdate` JSON (all fields
        optional — only supplied fields are applied).
        200 OK — body is the updated :class:`~app.schemas.todo.TodoResponse`.
        404 Not Found — no todo exists with the given ``todo_id``.
        422 Unprocessable Entity — body fails Pydantic validation.
    """
    logger.debug("PATCH /todos/%d requested", todo_id)
    return await service.update_todo(todo_id, payload)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> Response:
    """Delete a todo by its primary key.

    HTTP contract:
        DELETE /todos/{todo_id}
        204 No Content — todo was deleted successfully; body is empty.
        404 Not Found — no todo exists with the given ``todo_id``.
    """
    logger.debug("DELETE /todos/%d requested", todo_id)
    await service.delete_todo(todo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
