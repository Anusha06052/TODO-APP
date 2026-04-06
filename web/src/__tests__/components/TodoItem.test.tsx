import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { TodoItem } from '@/components/TodoItem';
import { useDeleteTodo, useUpdateTodo } from '@/hooks/useTodos';
import type { Todo } from '@/types';

vi.mock('@/hooks/useTodos');

// ─── Factories ───────────────────────────────────────────────────────────────

const createTodo = (overrides: Partial<Todo> = {}): Todo => ({
  id: 1,
  title: 'Test todo',
  description: null,
  is_completed: false,
  created_at: '2026-04-06T00:00:00Z',
  updated_at: '2026-04-06T00:00:00Z',
  ...overrides,
});

// ─── Hook mocks ──────────────────────────────────────────────────────────────

const onToggle = vi.fn();
const onDelete = vi.fn();

const setupHooks = (
  updateOverrides: Partial<ReturnType<typeof useUpdateTodo>> = {},
  deleteOverrides: Partial<ReturnType<typeof useDeleteTodo>> = {},
) => {
  vi.mocked(useUpdateTodo).mockReturnValue({
    mutate: onToggle,
    isPending: false,
    ...updateOverrides,
  } as ReturnType<typeof useUpdateTodo>);

  vi.mocked(useDeleteTodo).mockReturnValue({
    mutate: onDelete,
    isPending: false,
    ...deleteOverrides,
  } as ReturnType<typeof useDeleteTodo>);
};

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('TodoItem', () => {
  beforeEach(() => {
    onToggle.mockReset();
    onDelete.mockReset();
    setupHooks();
  });

  describe('rendering', () => {
    it('renders the todo title', () => {
      render(<TodoItem todo={createTodo({ title: 'Buy milk' })} />);

      expect(screen.getByText('Buy milk')).toBeInTheDocument();
    });

    it('renders the description when provided', () => {
      render(<TodoItem todo={createTodo({ description: 'From the shop' })} />);

      expect(screen.getByText('From the shop')).toBeInTheDocument();
    });

    it('does not render description when null', () => {
      render(<TodoItem todo={createTodo({ description: null })} />);

      expect(screen.queryByText('From the shop')).not.toBeInTheDocument();
    });

    it('renders the checkbox unchecked when todo is not completed', () => {
      render(<TodoItem todo={createTodo({ is_completed: false })} />);

      expect(screen.getByRole('checkbox')).not.toBeChecked();
    });

    it('renders the checkbox checked when todo is completed', () => {
      render(<TodoItem todo={createTodo({ is_completed: true })} />);

      expect(screen.getByRole('checkbox')).toBeChecked();
    });

    it('renders the delete button', () => {
      render(<TodoItem todo={createTodo()} />);

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });

    it('applies line-through style on title when todo is completed', () => {
      render(<TodoItem todo={createTodo({ title: 'Done task', is_completed: true })} />);

      expect(screen.getByText('Done task')).toHaveClass('line-through');
    });
  });

  describe('interactions', () => {
    it('calls onToggle with toggled is_completed when checkbox is clicked on an incomplete todo', async () => {
      const user = userEvent.setup();
      const todo = createTodo({ id: 42, is_completed: false });
      render(<TodoItem todo={todo} />);

      await user.click(screen.getByRole('checkbox'));

      expect(onToggle).toHaveBeenCalledOnce();
      expect(onToggle).toHaveBeenCalledWith({ id: 42, payload: { is_completed: true } });
    });

    it('calls onToggle with toggled is_completed when checkbox is clicked on a completed todo', async () => {
      const user = userEvent.setup();
      const todo = createTodo({ id: 7, is_completed: true });
      render(<TodoItem todo={todo} />);

      await user.click(screen.getByRole('checkbox'));

      expect(onToggle).toHaveBeenCalledOnce();
      expect(onToggle).toHaveBeenCalledWith({ id: 7, payload: { is_completed: false } });
    });

    it('calls onDelete with the todo id when the delete button is clicked', async () => {
      const user = userEvent.setup();
      const todo = createTodo({ id: 42 });
      render(<TodoItem todo={todo} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      expect(onDelete).toHaveBeenCalledOnce();
      expect(onDelete).toHaveBeenCalledWith(42);
    });
  });

  describe('pending state', () => {
    it('disables the checkbox and delete button when an update is pending', () => {
      setupHooks({ isPending: true });
      render(<TodoItem todo={createTodo()} />);

      expect(screen.getByRole('checkbox')).toBeDisabled();
      expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled();
    });

    it('disables the checkbox and delete button when a delete is pending', () => {
      setupHooks({}, { isPending: true });
      render(<TodoItem todo={createTodo()} />);

      expect(screen.getByRole('checkbox')).toBeDisabled();
      expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled();
    });

    it('does not call onToggle when the checkbox is clicked while pending', async () => {
      const user = userEvent.setup();
      setupHooks({ isPending: true });
      render(<TodoItem todo={createTodo()} />);

      await user.click(screen.getByRole('checkbox'));

      expect(onToggle).not.toHaveBeenCalled();
    });

    it('does not call onDelete when the delete button is clicked while pending', async () => {
      const user = userEvent.setup();
      setupHooks({}, { isPending: true });
      render(<TodoItem todo={createTodo()} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      expect(onDelete).not.toHaveBeenCalled();
    });
  });
});
