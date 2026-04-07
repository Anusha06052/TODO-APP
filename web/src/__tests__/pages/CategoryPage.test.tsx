import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCreateCategory, useDeleteCategory, useGetCategories, useUpdateCategory } from '@/hooks/useCategories';
import CategoryPage from '@/pages/CategoryPage';
import type { Category } from '@/types';

vi.mock('@/hooks/useCategories');

// ─── Factories ───────────────────────────────────────────────────────────────

const createCategory = (overrides: Partial<Category> = {}): Category => ({
  id: 1,
  name: 'Work',
  description: null,
  created_at: '2026-04-07T00:00:00Z',
  updated_at: '2026-04-07T00:00:00Z',
  ...overrides,
});

// ─── Mock helpers ─────────────────────────────────────────────────────────────

const mockCreateMutate = vi.fn();
const mockUpdateMutate = vi.fn();
const mockDeleteMutate = vi.fn();

const mockUseGetCategories = (
  overrides: Partial<ReturnType<typeof useGetCategories>> = {},
) => {
  vi.mocked(useGetCategories).mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: false,
    ...overrides,
  } as ReturnType<typeof useGetCategories>);
};

const mockUseCreateCategory = (
  overrides: Partial<ReturnType<typeof useCreateCategory>> = {},
) => {
  vi.mocked(useCreateCategory).mockReturnValue({
    mutate: mockCreateMutate,
    isPending: false,
    isError: false,
    error: null,
    ...overrides,
  } as ReturnType<typeof useCreateCategory>);
};

const mockUseUpdateCategory = (
  overrides: Partial<ReturnType<typeof useUpdateCategory>> = {},
) => {
  vi.mocked(useUpdateCategory).mockReturnValue({
    mutate: mockUpdateMutate,
    isPending: false,
    isError: false,
    error: null,
    ...overrides,
  } as ReturnType<typeof useUpdateCategory>);
};

const mockUseDeleteCategory = (
  overrides: Partial<ReturnType<typeof useDeleteCategory>> = {},
) => {
  vi.mocked(useDeleteCategory).mockReturnValue({
    mutate: mockDeleteMutate,
    isPending: false,
    ...overrides,
  } as ReturnType<typeof useDeleteCategory>);
};

const setupDefaultMocks = () => {
  mockUseGetCategories();
  mockUseCreateCategory();
  mockUseUpdateCategory();
  mockUseDeleteCategory();
};

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('CategoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  // ─── Page structure ───────────────────────────────────────────────────────

  describe('page structure', () => {
    it('renders the page heading', () => {
      render(<CategoryPage />);

      expect(screen.getByRole('heading', { name: /categories/i })).toBeInTheDocument();
    });

    it('renders the "Add a new category" landmark section', () => {
      render(<CategoryPage />);

      expect(
        screen.getByRole('region', { name: /add a new category/i }),
      ).toBeInTheDocument();
    });

    it('renders the category list landmark section', () => {
      render(<CategoryPage />);

      expect(screen.getByRole('region', { name: /category list/i })).toBeInTheDocument();
    });

    it('renders the name input and submit button inside the form section', () => {
      render(<CategoryPage />);

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add category/i })).toBeInTheDocument();
    });
  });

  // ─── Loading state ────────────────────────────────────────────────────────

  describe('loading state', () => {
    it('renders a loading indicator while categories are being fetched', () => {
      mockUseGetCategories({ isLoading: true });

      render(<CategoryPage />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('does not render any list items while loading', () => {
      mockUseGetCategories({ isLoading: true });

      render(<CategoryPage />);

      expect(screen.queryByRole('listitem')).not.toBeInTheDocument();
    });
  });

  // ─── Error state ──────────────────────────────────────────────────────────

  describe('error state', () => {
    it('renders an error alert when the categories request fails', () => {
      mockUseGetCategories({ isError: true });

      render(<CategoryPage />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('still renders the form when the list fails to load', () => {
      mockUseGetCategories({ isError: true });

      render(<CategoryPage />);

      expect(screen.getByRole('button', { name: /add category/i })).toBeInTheDocument();
    });
  });

  // ─── Empty state ──────────────────────────────────────────────────────────

  describe('empty state', () => {
    it('renders the empty-state message when the category list is empty', () => {
      mockUseGetCategories({ data: [] });

      render(<CategoryPage />);

      expect(screen.getByText(/no categories yet/i)).toBeInTheDocument();
    });
  });

  // ─── Happy path — list ────────────────────────────────────────────────────

  describe('populated list', () => {
    it('renders a list item for every category returned by the hook', () => {
      const categories = [
        createCategory({ id: 1, name: 'Work' }),
        createCategory({ id: 2, name: 'Personal' }),
        createCategory({ id: 3, name: 'Health' }),
      ];
      mockUseGetCategories({ data: categories });

      render(<CategoryPage />);

      expect(screen.getAllByRole('listitem')).toHaveLength(3);
    });

    it('renders each category name in the list', () => {
      const categories = [
        createCategory({ id: 1, name: 'Work' }),
        createCategory({ id: 2, name: 'Personal' }),
      ];
      mockUseGetCategories({ data: categories });

      render(<CategoryPage />);

      expect(screen.getByText('Work')).toBeInTheDocument();
      expect(screen.getByText('Personal')).toBeInTheDocument();
    });
  });

  // ─── Create category ──────────────────────────────────────────────────────

  describe('creating a category', () => {
    it('calls createCategory with the entered name on form submit', async () => {
      const user = userEvent.setup();
      mockUseGetCategories({ data: [] });

      render(<CategoryPage />);

      await user.type(screen.getByLabelText(/name/i), 'Shopping');
      await user.click(screen.getByRole('button', { name: /add category/i }));

      expect(mockCreateMutate).toHaveBeenCalledOnce();
      expect(mockCreateMutate).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Shopping' }),
        expect.any(Object),
      );
    });

    it('disables the submit button while creation is pending', () => {
      mockUseGetCategories({ data: [] });
      mockUseCreateCategory({ isPending: true });

      render(<CategoryPage />);

      expect(screen.getByRole('button', { name: /adding/i })).toBeDisabled();
    });
  });
});
