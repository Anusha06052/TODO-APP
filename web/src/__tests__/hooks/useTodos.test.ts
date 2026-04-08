import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  useCreateTodo,
  useDeleteTodo,
  useGetTodo,
  useGetTodos,
  useUpdateTodo,
} from '@/hooks/useTodos';
import { todoService } from '@/services/todoService';
import type { Todo } from '@/types';

vi.mock('@/services/todoService');

// ─── Factories ───────────────────────────────────────────────────────────────

const createTodo = (overrides: Partial<Todo> = {}): Todo => ({
  id: 1,
  title: 'Test todo',
  description: null,
  is_completed: false,
  category_id: null,
  created_at: '2026-04-06T00:00:00Z',
  updated_at: '2026-04-06T00:00:00Z',
  ...overrides,
});

// ─── Wrapper factory ─────────────────────────────────────────────────────────

// queryClient is module-scoped so tests can spy on it after createWrapper() runs.
let queryClient: QueryClient;

const createWrapper = () => {
  queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

// ─── useGetTodos ──────────────────────────────────────────────────────────────

describe('useGetTodos', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('is in loading state on initial fetch', () => {
    vi.mocked(todoService.getAll).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useGetTodos(), { wrapper: createWrapper() });

    expect(result.current.isLoading).toBe(true);
  });

  it('returns todos on successful fetch', async () => {
    const todos = [createTodo({ id: 1 }), createTodo({ id: 2, title: 'Second todo' })];
    vi.mocked(todoService.getAll).mockResolvedValue(todos);

    const { result } = renderHook(() => useGetTodos(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(todos);
  });

  it('returns an empty array when the API returns no todos', async () => {
    vi.mocked(todoService.getAll).mockResolvedValue([]);

    const { result } = renderHook(() => useGetTodos(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(todoService.getAll).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useGetTodos(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Network error');
  });
});

// ─── useGetTodo ───────────────────────────────────────────────────────────────

describe('useGetTodo', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('returns a single todo on successful fetch', async () => {
    const todo = createTodo({ id: 5, title: 'Specific todo' });
    vi.mocked(todoService.getById).mockResolvedValue(todo);

    const { result } = renderHook(() => useGetTodo(5), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(todo);
    expect(todoService.getById).toHaveBeenCalledWith(5);
  });

  it('is disabled and does not fetch when id is 0', () => {
    const { result } = renderHook(() => useGetTodo(0), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe('idle');
    expect(todoService.getById).not.toHaveBeenCalled();
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(todoService.getById).mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useGetTodo(99), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Not found');
  });
});

// ─── useCreateTodo ────────────────────────────────────────────────────────────

describe('useCreateTodo', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('calls todoService.create with the correct payload', async () => {
    const created = createTodo({ id: 10, title: 'New task' });
    vi.mocked(todoService.create).mockResolvedValue(created);

    const { result } = renderHook(() => useCreateTodo(), { wrapper: createWrapper() });

    result.current.mutate({ title: 'New task' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(todoService.create).toHaveBeenCalledWith({ title: 'New task' });
    expect(todoService.create).toHaveBeenCalledTimes(1);
  });

  it('returns the created todo as mutation data', async () => {
    const created = createTodo({ id: 10, title: 'New task' });
    vi.mocked(todoService.create).mockResolvedValue(created);

    const { result } = renderHook(() => useCreateTodo(), { wrapper: createWrapper() });

    result.current.mutate({ title: 'New task' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(created);
  });

  it('invalidates ["todos"] on success', async () => {
    vi.mocked(todoService.create).mockResolvedValue(createTodo());

    const { result } = renderHook(() => useCreateTodo(), { wrapper: createWrapper() });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    result.current.mutate({ title: 'New task' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['todos'] });
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(todoService.create).mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useCreateTodo(), { wrapper: createWrapper() });

    result.current.mutate({ title: 'New task' });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Server error');
  });
});

// ─── useUpdateTodo ────────────────────────────────────────────────────────────

describe('useUpdateTodo', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('calls todoService.update with id and payload', async () => {
    const updated = createTodo({ id: 3, is_completed: true });
    vi.mocked(todoService.update).mockResolvedValue(updated);

    const { result } = renderHook(() => useUpdateTodo(), { wrapper: createWrapper() });

    result.current.mutate({ id: 3, payload: { is_completed: true } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(todoService.update).toHaveBeenCalledWith(3, { is_completed: true });
    expect(todoService.update).toHaveBeenCalledTimes(1);
  });

  it('returns the updated todo as mutation data', async () => {
    const updated = createTodo({ id: 3, title: 'Renamed' });
    vi.mocked(todoService.update).mockResolvedValue(updated);

    const { result } = renderHook(() => useUpdateTodo(), { wrapper: createWrapper() });

    result.current.mutate({ id: 3, payload: { title: 'Renamed' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(updated);
  });

  it('invalidates ["todos"] and ["todos", id] on success', async () => {
    vi.mocked(todoService.update).mockResolvedValue(createTodo({ id: 3 }));

    const { result } = renderHook(() => useUpdateTodo(), { wrapper: createWrapper() });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    result.current.mutate({ id: 3, payload: { is_completed: true } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['todos'] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['todos', 3] });
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(todoService.update).mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useUpdateTodo(), { wrapper: createWrapper() });

    result.current.mutate({ id: 99, payload: { title: 'x' } });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Not found');
  });
});

// ─── useDeleteTodo ────────────────────────────────────────────────────────────

describe('useDeleteTodo', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('calls todoService.remove with the correct id', async () => {
    vi.mocked(todoService.remove).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteTodo(), { wrapper: createWrapper() });

    result.current.mutate(7);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(todoService.remove).toHaveBeenCalledWith(7);
    expect(todoService.remove).toHaveBeenCalledTimes(1);
  });

  it('invalidates ["todos"] on success', async () => {
    vi.mocked(todoService.remove).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteTodo(), { wrapper: createWrapper() });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    result.current.mutate(7);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['todos'] });
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(todoService.remove).mockRejectedValue(new Error('Delete failed'));

    const { result } = renderHook(() => useDeleteTodo(), { wrapper: createWrapper() });

    result.current.mutate(99);

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Delete failed');
  });
});
