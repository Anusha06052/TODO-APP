import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { categoryService } from '@/services/categoryService';
import type { CategoryCreate, CategoryUpdate } from '@/types';

/**
 * Fetches all Category items.
 *
 * @returns TanStack Query result containing the array of Category objects.
 */
export const useGetCategories = () =>
  useQuery({
    queryKey: ['categories'],
    queryFn: categoryService.getAll,
  });

/**
 * Fetches a single Category item by ID.
 *
 * @param id - The numeric ID of the Category to retrieve.
 * @returns TanStack Query result containing the matching Category object.
 */
export const useGetCategory = (id: number) =>
  useQuery({
    queryKey: ['categories', id],
    queryFn: () => categoryService.getById(id),
    enabled: !!id,
  });

/**
 * Mutation hook for creating a new Category item.
 * Invalidates the ['categories'] query on success.
 *
 * @returns TanStack Mutation object. Call `.mutate(payload)` to create.
 */
export const useCreateCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CategoryCreate) => categoryService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

/**
 * Mutation hook for updating an existing Category item.
 * Invalidates the ['categories'] list and the individual ['categories', id] query on success.
 *
 * @returns TanStack Mutation object. Call `.mutate({ id, payload })` to update.
 */
export const useUpdateCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: CategoryUpdate }) =>
      categoryService.update(id, payload),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['categories', id] });
    },
  });
};

/**
 * Mutation hook for deleting a Category item by ID.
 * Invalidates the ['categories'] list on success.
 *
 * @returns TanStack Mutation object. Call `.mutate(id)` to delete.
 */
export const useDeleteCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => categoryService.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};
