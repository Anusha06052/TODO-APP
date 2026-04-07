import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { TodoItem } from '@/components/TodoItem';
import TodoList from '@/components/TodoList';
import { useGetTodos } from '@/hooks/useTodos';
import type { Todo } from '@/types';

vi.mock('@/hooks/useTodos');
vi.mock('@/components/TodoItem');

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

// ─── Helpers ─────────────────────────────────────────────────────────────────

const mockUseGetTodos = (overrides: Partial<ReturnType<typeof useGetTodos>> = {}) => {
  vi.mocked(useGetTodos).mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: false,
    ...overrides,
  } as ReturnType<typeof useGetTodos>);
};

// ─── Tests ───────────────────────────────────────────────────────────────────

const onEdit = vi.fn();

describe('TodoList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    onEdit.mockReset();
    vi.mocked(TodoItem).mockImplementation(({ todo }) => (
      <li data-testid="todo-item">{todo.title}</li>
    ));
  });

  describe('loading state', () => {
    it('renders a loading indicator while fetching', () => {
      mockUseGetTodos({ isLoading: true });

      render(<TodoList onEdit={onEdit} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('error state', () => {
    it('renders an error message when the request fails', () => {
      mockUseGetTodos({ isError: true });

      render(<TodoList onEdit={onEdit} />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('renders "No todos yet" message when todos array is empty', () => {
      mockUseGetTodos({ data: [] });

      render(<TodoList onEdit={onEdit} />);

      expect(screen.getByText(/no todos yet/i)).toBeInTheDocument();
    });
  });

  describe('happy path', () => {
    it('renders correct number of TodoItem components when todos provided', () => {
      const todos = [
        createTodo({ id: 1, title: 'Todo 1' }),
        createTodo({ id: 2, title: 'Todo 2' }),
        createTodo({ id: 3, title: 'Todo 3' }),
      ];
      mockUseGetTodos({ data: todos });

      render(<TodoList onEdit={onEdit} />);

      expect(screen.getAllByTestId('todo-item')).toHaveLength(3);
    });

    it('passes the correct todo prop to each TodoItem', () => {
      const todos = [
        createTodo({ id: 1, title: 'Todo 1' }),
        createTodo({ id: 2, title: 'Todo 2' }),
      ];
      mockUseGetTodos({ data: todos });

      render(<TodoList onEdit={onEdit} />);

      expect(vi.mocked(TodoItem)).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({ todo: todos[0] }),
        expect.anything(),
      );
      expect(vi.mocked(TodoItem)).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({ todo: todos[1] }),
        expect.anything(),
      );
    });
  });
});
