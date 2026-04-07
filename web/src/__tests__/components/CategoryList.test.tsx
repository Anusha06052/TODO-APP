import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CategoryItem } from '@/components/CategoryItem';
import CategoryList from '@/components/CategoryList';
import { useGetCategories } from '@/hooks/useCategories';
import type { Category } from '@/types';

vi.mock('@/hooks/useCategories');
vi.mock('@/components/CategoryItem');

// ─── Factories ───────────────────────────────────────────────────────────────

const createCategory = (overrides: Partial<Category> = {}): Category => ({
  id: 1,
  name: 'Work',
  description: null,
  created_at: '2026-04-07T00:00:00Z',
  updated_at: '2026-04-07T00:00:00Z',
  ...overrides,
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

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

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('CategoryList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(CategoryItem).mockImplementation(({ category }) => (
      <li data-testid="category-item">{category.name}</li>
    ));
  });

  describe('loading state', () => {
    it('renders a loading indicator while fetching', () => {
      mockUseGetCategories({ isLoading: true });

      render(<CategoryList />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('error state', () => {
    it('renders an error message when the request fails', () => {
      mockUseGetCategories({ isError: true });

      render(<CategoryList />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('renders "No categories yet" message when list is empty', () => {
      mockUseGetCategories({ data: [] });

      render(<CategoryList />);

      expect(screen.getByText(/no categories yet/i)).toBeInTheDocument();
    });
  });

  describe('happy path', () => {
    it('renders the correct number of CategoryItem components', () => {
      const categories = [
        createCategory({ id: 1, name: 'Work' }),
        createCategory({ id: 2, name: 'Personal' }),
        createCategory({ id: 3, name: 'Health' }),
      ];
      mockUseGetCategories({ data: categories });

      render(<CategoryList />);

      expect(screen.getAllByTestId('category-item')).toHaveLength(3);
    });

    it('passes the correct category prop to each CategoryItem', () => {
      const categories = [
        createCategory({ id: 1, name: 'Work' }),
        createCategory({ id: 2, name: 'Personal' }),
      ];
      mockUseGetCategories({ data: categories });

      render(<CategoryList />);

      expect(vi.mocked(CategoryItem)).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({ category: categories[0] }),
        expect.anything(),
      );
      expect(vi.mocked(CategoryItem)).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({ category: categories[1] }),
        expect.anything(),
      );
    });
  });
});
