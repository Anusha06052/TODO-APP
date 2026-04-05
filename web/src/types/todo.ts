/**
 * Represents a Todo item as returned by the API.
 */
export interface Todo {
  id: number;
  title: string;
  description: string | null;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Payload for creating a new Todo item.
 * `description` is optional; omitting it is treated the same as passing null.
 */
export interface CreateTodoDto {
  title: string;
  description?: string | null;
}

/**
 * Payload for updating an existing Todo item.
 * All fields are optional — only the provided fields will be changed.
 */
export interface UpdateTodoDto {
  title?: string;
  description?: string | null;
  is_completed?: boolean;
}

/**
 * Shape of a FastAPI error response body.
 * Maps to the `detail` field returned by FastAPI on 4xx / 5xx responses.
 */
export interface ApiError {
  detail: string;
}
