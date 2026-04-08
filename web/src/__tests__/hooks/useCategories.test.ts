import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  useCreateCategory,
  useDeleteCategory,
  useGetCategories,
  useGetCategory,
  useUpdateCategory,
} from '@/hooks/useCategories';
import { categoryService } from '@/services/categoryService';
import type { Category } from '@/types';

vi.mock('@/services/categoryService');

// ─── Factories ───────────────────────────────────────────────────────────────

const createCategory = (overrides: Partial<Category> = {}): Category => ({
  id: 1,
  name: 'Work',
  description: null,
  created_at: '2026-04-08T00:00:00Z',
  updated_at: '2026-04-08T00:00:00Z',
  ...overrides,
});

// ─── Wrapper factory ─────────────────────────────────────────────────────────

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

// ─── useGetCategories ─────────────────────────────────────────────────────────

describe('useGetCategories', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('is in loading state on initial fetch', () => {
    vi.mocked(categoryService.getAll).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useGetCategories(), { wrapper: createWrapper() });

    expect(result.current.isLoading).toBe(true);
  });

  it('returns categories on successful fetch', async () => {
    const categories = [
      createCategory({ id: 1 }),
      createCategory({ id: 2, name: 'Personal' }),
    ];
    vi.mocked(categoryService.getAll).mockResolvedValue(categories);

    const { result } = renderHook(() => useGetCategories(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(categories);
  });

  it('returns an empty array when the API returns no categories', async () => {
    vi.mocked(categoryService.getAll).mockResolvedValue([]);

    const { result } = renderHook(() => useGetCategories(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(categoryService.getAll).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useGetCategories(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Network error');
  });
});

// ─── useGetCategory ───────────────────────────────────────────────────────────

describe('useGetCategory', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('returns a single category on successful fetch', async () => {
    const category = createCategory({ id: 5, name: 'Health' });
    vi.mocked(categoryService.getById).mockResolvedValue(category);

    const { result } = renderHook(() => useGetCategory(5), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(category);
    expect(categoryService.getById).toHaveBeenCalledWith(5);
  });

  it('is disabled and does not fetch when id is 0', () => {
    const { result } = renderHook(() => useGetCategory(0), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe('idle');
    expect(categoryService.getById).not.toHaveBeenCalled();
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(categoryService.getById).mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useGetCategory(99), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Not found');
  });
});

// ─── useCreateCategory ────────────────────────────────────────────────────────

describe('useCreateCategory', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('calls categoryService.create with the correct payload', async () => {
    const created = createCategory({ id: 10, name: 'Fitness' });
    vi.mocked(categoryService.create).mockResolvedValue(created);

    const { result } = renderHook(() => useCreateCategory(), { wrapper: createWrapper() });

    result.current.mutate({ name: 'Fitness' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(categoryService.create).toHaveBeenCalledWith({ name: 'Fitness' });
    expect(categoryService.create).toHaveBeenCalledTimes(1);
  });

  it('returns the created category as mutation data', async () => {
    const created = createCategory({ id: 10, name: 'Fitness' });
    vi.mocked(categoryService.create).mockResolvedValue(created);

    const { result } = renderHook(() => useCreateCategory(), { wrapper: createWrapper() });

    result.current.mutate({ name: 'Fitness' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(created);
  });

  it('invalidates ["categories"] on success', async () => {
    vi.mocked(categoryService.create).mockResolvedValue(createCategory());

    const { result } = renderHook(() => useCreateCategory(), { wrapper: createWrapper() });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    result.current.mutate({ name: 'Fitness' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['categories'] });
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(categoryService.create).mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useCreateCategory(), { wrapper: createWrapper() });

    result.current.mutate({ name: 'Fitness' });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Server error');
  });
});

// ─── useUpdateCategory ────────────────────────────────────────────────────────

describe('useUpdateCategory', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('calls categoryService.update with id and payload', async () => {
    const updated = createCategory({ id: 3, name: 'Renamed' });
    vi.mocked(categoryService.update).mockResolvedValue(updated);

    const { result } = renderHook(() => useUpdateCategory(), { wrapper: createWrapper() });

    result.current.mutate({ id: 3, payload: { name: 'Renamed' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(categoryService.update).toHaveBeenCalledWith(3, { name: 'Renamed' });
    expect(categoryService.update).toHaveBeenCalledTimes(1);
  });

  it('returns the updated category as mutation data', async () => {
    const updated = createCategory({ id: 3, name: 'Renamed' });
    vi.mocked(categoryService.update).mockResolvedValue(updated);

    const { result } = renderHook(() => useUpdateCategory(), { wrapper: createWrapper() });

    result.current.mutate({ id: 3, payload: { name: 'Renamed' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(updated);
  });

  it('invalidates ["categories"] and ["categories", id] on success', async () => {
    vi.mocked(categoryService.update).mockResolvedValue(createCategory({ id: 3 }));

    const { result } = renderHook(() => useUpdateCategory(), { wrapper: createWrapper() });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    result.current.mutate({ id: 3, payload: { name: 'Renamed' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['categories'] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['categories', 3] });
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(categoryService.update).mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useUpdateCategory(), { wrapper: createWrapper() });

    result.current.mutate({ id: 99, payload: { name: 'x' } });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Not found');
  });
});

// ─── useDeleteCategory ────────────────────────────────────────────────────────

describe('useDeleteCategory', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('calls categoryService.remove with the correct id', async () => {
    vi.mocked(categoryService.remove).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteCategory(), { wrapper: createWrapper() });

    result.current.mutate(7);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(categoryService.remove).toHaveBeenCalledWith(7);
    expect(categoryService.remove).toHaveBeenCalledTimes(1);
  });

  it('invalidates ["categories"] on success', async () => {
    vi.mocked(categoryService.remove).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteCategory(), { wrapper: createWrapper() });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    result.current.mutate(7);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['categories'] });
  });

  it('returns error state when the service rejects', async () => {
    vi.mocked(categoryService.remove).mockRejectedValue(new Error('Delete failed'));

    const { result } = renderHook(() => useDeleteCategory(), { wrapper: createWrapper() });

    result.current.mutate(7);

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toBe('Delete failed');
  });
});
