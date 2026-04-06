import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  useCreateTodo,
  useDeleteTodo,
  useGetTodos,
  useUpdateTodo,
} from '@/hooks/useTodos';
import TodoPage from '@/pages/TodoPage';
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

// ─── Mock helpers ─────────────────────────────────────────────────────────────

const mockCreateMutate = vi.fn();
const mockUpdateMutate = vi.fn();
const mockDeleteMutate = vi.fn();

const mockUseGetTodos = (overrides: Partial<ReturnType<typeof useGetTodos>> = {}) => {
  vi.mocked(useGetTodos).mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: false,
    ...overrides,
  } as ReturnType<typeof useGetTodos>);
};

const mockUseCreateTodo = (overrides: Partial<ReturnType<typeof useCreateTodo>> = {}) => {
  vi.mocked(useCreateTodo).mockReturnValue({
    mutate: mockCreateMutate,
    isPending: false,
    isError: false,
    error: undefined,
    ...overrides,
  } as ReturnType<typeof useCreateTodo>);
};

const mockUseUpdateTodo = (overrides: Partial<ReturnType<typeof useUpdateTodo>> = {}) => {
  vi.mocked(useUpdateTodo).mockReturnValue({
    mutate: mockUpdateMutate,
    isPending: false,
    ...overrides,
  } as ReturnType<typeof useUpdateTodo>);
};

const mockUseDeleteTodo = (overrides: Partial<ReturnType<typeof useDeleteTodo>> = {}) => {
  vi.mocked(useDeleteTodo).mockReturnValue({
    mutate: mockDeleteMutate,
    isPending: false,
    ...overrides,
  } as ReturnType<typeof useDeleteTodo>);
};

const setupDefaultMocks = () => {
  mockUseGetTodos();
  mockUseCreateTodo();
  mockUseUpdateTodo();
  mockUseDeleteTodo();
};

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('TodoPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  // ─── Page structure ───────────────────────────────────────────────────────

  describe('page structure', () => {
    it('renders the page heading', () => {
      render(<TodoPage />);

      expect(screen.getByRole('heading', { name: /my todos/i })).toBeInTheDocument();
    });

    it('renders the "Add a new todo" landmark section', () => {
      render(<TodoPage />);

      expect(screen.getByRole('region', { name: /add a new todo/i })).toBeInTheDocument();
    });

    it('renders the todo list landmark section', () => {
      render(<TodoPage />);

      expect(screen.getByRole('region', { name: /todo list/i })).toBeInTheDocument();
    });

    it('renders the title input and submit button inside the form section', () => {
      render(<TodoPage />);

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add todo/i })).toBeInTheDocument();
    });
  });

  // ─── Loading state ────────────────────────────────────────────────────────

  describe('loading state', () => {
    it('renders a loading indicator while todos are being fetched', () => {
      mockUseGetTodos({ isLoading: true });

      render(<TodoPage />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('does not render any todo items while loading', () => {
      mockUseGetTodos({ isLoading: true });

      render(<TodoPage />);

      expect(screen.queryByRole('listitem')).not.toBeInTheDocument();
    });
  });

  // ─── Error state ──────────────────────────────────────────────────────────

  describe('error state', () => {
    it('renders an error alert when the todos request fails', () => {
      mockUseGetTodos({ isError: true });

      render(<TodoPage />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('still renders the form when the list fails to load', () => {
      mockUseGetTodos({ isError: true });

      render(<TodoPage />);

      expect(screen.getByRole('button', { name: /add todo/i })).toBeInTheDocument();
    });
  });

  // ─── Empty state ──────────────────────────────────────────────────────────

  describe('empty state', () => {
    it('renders the empty-state message when the todos list is empty', () => {
      mockUseGetTodos({ data: [] });

      render(<TodoPage />);

      expect(screen.getByText(/no todos yet/i)).toBeInTheDocument();
    });
  });

  // ─── Happy path — list ────────────────────────────────────────────────────

  describe('populated list', () => {
    it('renders a list item for every todo returned by the hook', () => {
      const todos = [
        createTodo({ id: 1, title: 'Buy milk' }),
        createTodo({ id: 2, title: 'Walk the dog' }),
        createTodo({ id: 3, title: 'Write tests' }),
      ];
      mockUseGetTodos({ data: todos });

      render(<TodoPage />);

      expect(screen.getAllByRole('listitem')).toHaveLength(3);
    });

    it('renders each todo title in the list', () => {
      const todos = [
        createTodo({ id: 1, title: 'Buy milk' }),
        createTodo({ id: 2, title: 'Walk the dog' }),
      ];
      mockUseGetTodos({ data: todos });

      render(<TodoPage />);

      expect(screen.getByText('Buy milk')).toBeInTheDocument();
      expect(screen.getByText('Walk the dog')).toBeInTheDocument();
    });

    it('renders a completed todo with a checked checkbox', () => {
      const todos = [createTodo({ id: 1, title: 'Done task', is_completed: true })];
      mockUseGetTodos({ data: todos });

      render(<TodoPage />);

      expect(screen.getByRole('checkbox', { name: /done task/i })).toBeChecked();
    });

    it('renders an incomplete todo with an unchecked checkbox', () => {
      const todos = [createTodo({ id: 1, title: 'Pending task', is_completed: false })];
      mockUseGetTodos({ data: todos });

      render(<TodoPage />);

      expect(screen.getByRole('checkbox', { name: /pending task/i })).not.toBeChecked();
    });
  });

  // ─── Form submission ──────────────────────────────────────────────────────

  describe('form submission', () => {
    it('calls createTodo mutate with the trimmed title when the form is submitted', async () => {
      const user = userEvent.setup();
      render(<TodoPage />);

      await user.type(screen.getByLabelText(/title/i), '  Buy milk  ');
      await user.click(screen.getByRole('button', { name: /add todo/i }));

      expect(mockCreateMutate).toHaveBeenCalledOnce();
      expect(mockCreateMutate).toHaveBeenCalledWith(
        { title: 'Buy milk', description: null },
        expect.any(Object),
      );
    });

    it('calls createTodo mutate with both title and description when both are filled', async () => {
      const user = userEvent.setup();
      render(<TodoPage />);

      await user.type(screen.getByLabelText(/title/i), 'Buy milk');
      await user.type(screen.getByLabelText(/description/i), '  Whole fat  ');
      await user.click(screen.getByRole('button', { name: /add todo/i }));

      expect(mockCreateMutate).toHaveBeenCalledWith(
        { title: 'Buy milk', description: 'Whole fat' },
        expect.any(Object),
      );
    });

    it('does not call createTodo mutate when the title field is empty', async () => {
      const user = userEvent.setup();
      render(<TodoPage />);

      await user.keyboard('{Enter}');

      expect(mockCreateMutate).not.toHaveBeenCalled();
    });

    it('disables the form inputs while a create mutation is pending', () => {
      mockUseCreateTodo({ isPending: true, mutate: mockCreateMutate });
      render(<TodoPage />);

      expect(screen.getByLabelText(/title/i)).toBeDisabled();
    });

    it('renders an inline error alert inside the form area when the create mutation fails', () => {
      mockUseCreateTodo({
        isPending: false,
        isError: true,
        error: new Error('Server error'),
        mutate: mockCreateMutate,
      });
      render(<TodoPage />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  // ─── Todo interactions ────────────────────────────────────────────────────

  describe('todo interactions', () => {
    it('calls updateTodo mutate with toggled is_completed when the checkbox is clicked', async () => {
      const user = userEvent.setup();
      const todo = createTodo({ id: 42, title: 'Buy milk', is_completed: false });
      mockUseGetTodos({ data: [todo] });

      render(<TodoPage />);

      await user.click(screen.getByRole('checkbox', { name: /buy milk/i }));

      expect(mockUpdateMutate).toHaveBeenCalledOnce();
      expect(mockUpdateMutate).toHaveBeenCalledWith({
        id: 42,
        payload: { is_completed: true },
      });
    });

    it('calls updateTodo mutate with is_completed false when a completed todo is unchecked', async () => {
      const user = userEvent.setup();
      const todo = createTodo({ id: 7, title: 'Done task', is_completed: true });
      mockUseGetTodos({ data: [todo] });

      render(<TodoPage />);

      await user.click(screen.getByRole('checkbox', { name: /done task/i }));

      expect(mockUpdateMutate).toHaveBeenCalledWith({
        id: 7,
        payload: { is_completed: false },
      });
    });

    it('calls deleteTodo mutate with the correct todo id when the delete button is clicked', async () => {
      const user = userEvent.setup();
      const todo = createTodo({ id: 99, title: 'Buy milk' });
      mockUseGetTodos({ data: [todo] });

      render(<TodoPage />);

      await user.click(screen.getByRole('button', { name: /delete "buy milk"/i }));

      expect(mockDeleteMutate).toHaveBeenCalledOnce();
      expect(mockDeleteMutate).toHaveBeenCalledWith(99);
    });

    it('disables the todo checkbox and delete button while an update is pending', () => {
      mockUseUpdateTodo({ isPending: true, mutate: mockUpdateMutate });
      const todo = createTodo({ id: 1, title: 'Buy milk' });
      mockUseGetTodos({ data: [todo] });

      render(<TodoPage />);

      expect(screen.getByRole('checkbox', { name: /buy milk/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /delete "buy milk"/i })).toBeDisabled();
    });

    it('disables the todo checkbox and delete button while a delete is pending', () => {
      mockUseDeleteTodo({ isPending: true, mutate: mockDeleteMutate });
      const todo = createTodo({ id: 1, title: 'Buy milk' });
      mockUseGetTodos({ data: [todo] });

      render(<TodoPage />);

      expect(screen.getByRole('checkbox', { name: /buy milk/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /delete "buy milk"/i })).toBeDisabled();
    });
  });
});
