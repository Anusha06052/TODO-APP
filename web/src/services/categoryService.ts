import { api } from '@/services/api';

import type { Category, CategoryCreate, CategoryUpdate } from '@/types';

/**
 * Fetches all Category items from the API.
 *
 * @returns A promise that resolves to an array of Category objects.
 */
const getAll = async (): Promise<Category[]> => {
  const response = await api.get<Category[]>('/categories');
  return response.data;
};

/**
 * Fetches a single Category item by its ID.
 *
 * @param id - The numeric ID of the Category to retrieve.
 * @returns A promise that resolves to the matching Category object.
 */
const getById = async (id: number): Promise<Category> => {
  const response = await api.get<Category>(`/categories/${id}`);
  return response.data;
};

/**
 * Creates a new Category item.
 *
 * @param payload - The data for the new Category (name, optional description).
 * @returns A promise that resolves to the newly created Category object.
 */
const create = async (payload: CategoryCreate): Promise<Category> => {
  const response = await api.post<Category>('/categories', payload);
  return response.data;
};

/**
 * Updates an existing Category item by its ID.
 *
 * @param id - The numeric ID of the Category to update.
 * @param payload - The fields to update (all optional).
 * @returns A promise that resolves to the updated Category object.
 */
const update = async (id: number, payload: CategoryUpdate): Promise<Category> => {
  const response = await api.patch<Category>(`/categories/${id}`, payload);
  return response.data;
};

/**
 * Deletes a Category item by its ID.
 *
 * @param id - The numeric ID of the Category to delete.
 * @returns A promise that resolves when the deletion is complete.
 */
const remove = async (id: number): Promise<void> => {
  await api.delete(`/categories/${id}`);
};

export const categoryService = {
  getAll,
  getById,
  create,
  update,
  remove,
};
