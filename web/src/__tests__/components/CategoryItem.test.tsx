import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CategoryItem } from '@/components/CategoryItem';
import { useDeleteCategory, useUpdateCategory } from '@/hooks/useCategories';
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

// ─── Hook mocks ──────────────────────────────────────────────────────────────

const onUpdate = vi.fn();
const onDelete = vi.fn();

const setupHooks = (
  updateOverrides: Partial<ReturnType<typeof useUpdateCategory>> = {},
  deleteOverrides: Partial<ReturnType<typeof useDeleteCategory>> = {},
) => {
  vi.mocked(useUpdateCategory).mockReturnValue({
    mutate: onUpdate,
    isPending: false,
    isError: false,
    error: null,
    ...updateOverrides,
  } as ReturnType<typeof useUpdateCategory>);

  vi.mocked(useDeleteCategory).mockReturnValue({
    mutate: onDelete,
    isPending: false,
    ...deleteOverrides,
  } as ReturnType<typeof useDeleteCategory>);
};

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('CategoryItem', () => {
  beforeEach(() => {
    onUpdate.mockReset();
    onDelete.mockReset();
    setupHooks();
  });

  // ── Rendering (read mode) ─────────────────────────────────────────────────

  describe('rendering', () => {
    it('renders the category name', () => {
      render(<CategoryItem category={createCategory({ name: 'Personal' })} />);

      expect(screen.getByText('Personal')).toBeInTheDocument();
    });

    it('renders the description when provided', () => {
      render(<CategoryItem category={createCategory({ description: 'My personal tasks' })} />);

      expect(screen.getByText('My personal tasks')).toBeInTheDocument();
    });

    it('does not render a description element when description is null', () => {
      render(<CategoryItem category={createCategory({ description: null })} />);

      expect(screen.queryByText('My personal tasks')).not.toBeInTheDocument();
    });

    it('renders the edit button', () => {
      render(<CategoryItem category={createCategory()} />);

      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });

    it('renders the delete button', () => {
      render(<CategoryItem category={createCategory()} />);

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });

    it('does not render the inline form in read mode', () => {
      render(<CategoryItem category={createCategory()} />);

      expect(screen.queryByRole('textbox', { name: /category name/i })).not.toBeInTheDocument();
    });
  });

  // ── Edit mode ─────────────────────────────────────────────────────────────

  describe('entering edit mode', () => {
    it('shows the name input pre-filled when edit is clicked', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ name: 'Work' })} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));

      expect(screen.getByRole('textbox', { name: /category name/i })).toHaveValue('Work');
    });

    it('shows the description textarea pre-filled when edit is clicked', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ description: 'Office tasks' })} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));

      expect(screen.getByRole('textbox', { name: /category description/i })).toHaveValue(
        'Office tasks',
      );
    });

    it('shows Save and Cancel buttons in edit mode', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory()} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('hides the edit and delete buttons while in edit mode', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory()} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));

      expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    });
  });

  // ── Cancel edit ───────────────────────────────────────────────────────────

  describe('cancelling edit', () => {
    it('returns to read mode when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory()} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(screen.queryByRole('textbox', { name: /category name/i })).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });

    it('does not call updateCategory when Cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory()} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onUpdate).not.toHaveBeenCalled();
    });
  });

  // ── Save edit ─────────────────────────────────────────────────────────────

  describe('saving edits', () => {
    it('calls updateCategory with the new name on submit', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ id: 5, name: 'Work' })} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      const nameInput = screen.getByRole('textbox', { name: /category name/i });
      await user.clear(nameInput);
      await user.type(nameInput, 'Personal');
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onUpdate).toHaveBeenCalledOnce();
      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ id: 5, payload: expect.objectContaining({ name: 'Personal' }) }),
        expect.any(Object),
      );
    });

    it('trims whitespace from the name before submitting', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ id: 3, name: 'Work' })} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      const nameInput = screen.getByRole('textbox', { name: /category name/i });
      await user.clear(nameInput);
      await user.type(nameInput, '  Trimmed  ');
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ payload: expect.objectContaining({ name: 'Trimmed' }) }),
        expect.any(Object),
      );
    });

    it('passes null description when the description field is empty', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ description: 'Old desc' })} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      const descInput = screen.getByRole('textbox', { name: /category description/i });
      await user.clear(descInput);
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ payload: expect.objectContaining({ description: null }) }),
        expect.any(Object),
      );
    });

    it('disables the Save button when name input is empty', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ name: 'Work' })} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      await user.clear(screen.getByRole('textbox', { name: /category name/i }));

      expect(screen.getByRole('button', { name: /save/i })).toBeDisabled();
    });
  });

  // ── Delete ────────────────────────────────────────────────────────────────

  describe('deleting', () => {
    it('calls deleteCategory with the category id when delete is clicked', async () => {
      const user = userEvent.setup();
      render(<CategoryItem category={createCategory({ id: 9 })} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      expect(onDelete).toHaveBeenCalledOnce();
      expect(onDelete).toHaveBeenCalledWith(9);
    });
  });

  // ── Pending state ─────────────────────────────────────────────────────────

  describe('pending state', () => {
    it('disables edit and delete buttons while an update is pending', () => {
      setupHooks({ isPending: true });
      render(<CategoryItem category={createCategory()} />);

      expect(screen.getByRole('button', { name: /edit/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled();
    });

    it('disables edit and delete buttons while a delete is pending', () => {
      setupHooks({}, { isPending: true });
      render(<CategoryItem category={createCategory()} />);

      expect(screen.getByRole('button', { name: /edit/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled();
    });

    it('shows "Saving…" on the submit button while updating', async () => {
      const user = userEvent.setup();
      const category = createCategory();
      const { rerender } = render(<CategoryItem category={category} />);

      // Enter edit mode while idle
      await user.click(screen.getByRole('button', { name: /edit/i }));

      // Simulate update in-flight
      setupHooks({ isPending: true });
      rerender(<CategoryItem category={category} />);

      expect(screen.getByRole('button', { name: /saving/i })).toBeInTheDocument();
    });
  });

  // ── Error state ───────────────────────────────────────────────────────────

  describe('error state', () => {
    it('shows an error message when update fails', async () => {
      const user = userEvent.setup();
      setupHooks({ isError: true, error: new Error('Name already taken') });
      render(<CategoryItem category={createCategory()} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));

      expect(screen.getByRole('alert')).toHaveTextContent('Name already taken');
    });
  });
});
