import { api } from '@/services/api';

import type { CreateTodoDto, Todo, UpdateTodoDto } from '@/types';

/**
 * Fetches all Todo items from the API.
 *
 * @returns A promise that resolves to an array of Todo objects.
 */
const getAll = async (): Promise<Todo[]> => {
  const response = await api.get<Todo[]>('/todos');
  return response.data;
};

/**
 * Fetches a single Todo item by its ID.
 *
 * @param id - The numeric ID of the Todo to retrieve.
 * @returns A promise that resolves to the matching Todo object.
 */
const getById = async (id: number): Promise<Todo> => {
  const response = await api.get<Todo>(`/todos/${id}`);
  return response.data;
};

/**
 * Creates a new Todo item.
 *
 * @param payload - The data for the new Todo (title, optional description).
 * @returns A promise that resolves to the newly created Todo object.
 */
const create = async (payload: CreateTodoDto): Promise<Todo> => {
  const response = await api.post<Todo>('/todos', payload);
  return response.data;
};

/**
 * Updates an existing Todo item by its ID.
 *
 * @param id - The numeric ID of the Todo to update.
 * @param payload - The fields to update (all optional).
 * @returns A promise that resolves to the updated Todo object.
 */
const update = async (id: number, payload: UpdateTodoDto): Promise<Todo> => {
  const response = await api.patch<Todo>(`/todos/${id}`, payload);
  return response.data;
};

/**
 * Deletes a Todo item by its ID.
 *
 * @param id - The numeric ID of the Todo to delete.
 * @returns A promise that resolves when the deletion is complete.
 */
const remove = async (id: number): Promise<void> => {
  await api.delete(`/todos/${id}`);
};

export const todoService = {
  getAll,
  getById,
  create,
  update,
  remove,
};
