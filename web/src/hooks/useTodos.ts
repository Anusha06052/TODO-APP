import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { todoService } from '@/services/todoService';
import type { CreateTodoDto, UpdateTodoDto } from '@/types';

/**
 * Fetches all Todo items.
 *
 * @returns TanStack Query result containing the array of Todo objects.
 */
export const useGetTodos = () =>
  useQuery({
    queryKey: ['todos'],
    queryFn: todoService.getAll,
  });

/**
 * Fetches a single Todo item by ID.
 *
 * @param id - The numeric ID of the Todo to retrieve.
 * @returns TanStack Query result containing the matching Todo object.
 */
export const useGetTodo = (id: number) =>
  useQuery({
    queryKey: ['todos', id],
    queryFn: () => todoService.getById(id),
    enabled: !!id,
  });

/**
 * Mutation hook for creating a new Todo item.
 * Invalidates the ['todos'] query on success.
 *
 * @returns TanStack Mutation object. Call `.mutate(payload)` to create.
 */
export const useCreateTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTodoDto) => todoService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

/**
 * Mutation hook for updating an existing Todo item.
 * Invalidates the ['todos'] list and the individual ['todos', id] query on success.
 *
 * @returns TanStack Mutation object. Call `.mutate({ id, payload })` to update.
 */
export const useUpdateTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateTodoDto }) =>
      todoService.update(id, payload),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
      queryClient.invalidateQueries({ queryKey: ['todos', id] });
    },
  });
};

/**
 * Mutation hook for deleting a Todo item by ID.
 * Invalidates the ['todos'] list on success.
 *
 * @returns TanStack Mutation object. Call `.mutate(id)` to delete.
 */
export const useDeleteTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => todoService.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};
