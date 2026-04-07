/**
 * Represents a Category as returned by the API.
 */
export interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Payload for creating a new Category.
 * `description` is optional; omitting it is treated the same as passing null.
 */
export interface CategoryCreate {
  name: string;
  description?: string | null;
}

/**
 * Payload for partially updating an existing Category.
 * All fields are optional — only the provided fields will be changed.
 * Pass `null` for `description` to clear the field.
 */
export interface CategoryUpdate {
  name?: string;
  description?: string | null;
}
