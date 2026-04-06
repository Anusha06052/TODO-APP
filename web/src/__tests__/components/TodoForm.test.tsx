import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { TodoForm } from '@/components/TodoForm';
import { useCreateTodo } from '@/hooks/useTodos';

vi.mock('@/hooks/useTodos');

const mockMutate = vi.fn();

const mockUseCreateTodo = (
  overrides: Partial<ReturnType<typeof useCreateTodo>> = {},
) => {
  vi.mocked(useCreateTodo).mockReturnValue({
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: undefined,
    ...overrides,
  } as ReturnType<typeof useCreateTodo>);
};

describe('TodoForm', () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockUseCreateTodo();
  });

  describe('rendering', () => {
    it('renders the title input, description textarea, and submit button', () => {
      render(<TodoForm />);

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /add todo/i }),
      ).toBeInTheDocument();
    });

    it('submit button is disabled when the title field is empty', () => {
      render(<TodoForm />);

      expect(screen.getByRole('button', { name: /add todo/i })).toBeDisabled();
    });

    it('does not show an error alert when there is no error', () => {
      render(<TodoForm />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('validation', () => {
    it('enables the submit button once title text is entered', async () => {
      const user = userEvent.setup();
      render(<TodoForm />);

      await user.type(screen.getByLabelText(/title/i), 'Buy milk');

      expect(
        screen.getByRole('button', { name: /add todo/i }),
      ).toBeEnabled();
    });

    it('keeps submit button disabled when title contains only whitespace', async () => {
      const user = userEvent.setup();
      render(<TodoForm />);

      await user.type(screen.getByLabelText(/title/i), '   ');

      expect(screen.getByRole('button', { name: /add todo/i })).toBeDisabled();
    });

    it('does not call mutate when title is whitespace only and form is submitted', async () => {
      const user = userEvent.setup();
      render(<TodoForm />);

      // Type whitespace so the input isn't empty (HTML `required` only guards empty)
      const titleInput = screen.getByLabelText(/title/i);
      await user.type(titleInput, '   ');
      // Button is still disabled; submit via keyboard Enter to exercise the guard
      await user.keyboard('{Enter}');

      expect(mockMutate).not.toHaveBeenCalled();
    });
  });

  describe('submission', () => {
    it('calls mutate with the trimmed title and null description when description is omitted', async () => {
      const user = userEvent.setup();
      render(<TodoForm />);

      await user.type(screen.getByLabelText(/title/i), '  Buy milk  ');
      await user.click(screen.getByRole('button', { name: /add todo/i }));

      expect(mockMutate).toHaveBeenCalledOnce();
      expect(mockMutate).toHaveBeenCalledWith(
        { title: 'Buy milk', description: null },
        expect.any(Object),
      );
    });

    it('calls mutate with title and trimmed description when both fields are filled', async () => {
      const user = userEvent.setup();
      render(<TodoForm />);

      await user.type(screen.getByLabelText(/title/i), 'Buy milk');
      await user.type(
        screen.getByLabelText(/description/i),
        '  From the store  ',
      );
      await user.click(screen.getByRole('button', { name: /add todo/i }));

      expect(mockMutate).toHaveBeenCalledOnce();
      expect(mockMutate).toHaveBeenCalledWith(
        { title: 'Buy milk', description: 'From the store' },
        expect.any(Object),
      );
    });
  });

  describe('success behaviour', () => {
    beforeEach(() => {
      mockMutate.mockImplementation(
        (_payload: unknown, options?: { onSuccess?: () => void }) => {
          options?.onSuccess?.();
        },
      );
    });

    it('clears both inputs after successful mutation', async () => {
      const user = userEvent.setup();
      render(<TodoForm />);

      await user.type(screen.getByLabelText(/title/i), 'Buy milk');
      await user.type(screen.getByLabelText(/description/i), 'From the store');
      await user.click(screen.getByRole('button', { name: /add todo/i }));

      expect(screen.getByLabelText(/title/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
    });

    it('calls the onSuccess prop after a successful mutation', async () => {
      const onSuccess = vi.fn();
      const user = userEvent.setup();
      render(<TodoForm onSuccess={onSuccess} />);

      await user.type(screen.getByLabelText(/title/i), 'Buy milk');
      await user.click(screen.getByRole('button', { name: /add todo/i }));

      expect(onSuccess).toHaveBeenCalledOnce();
    });
  });

  describe('pending state', () => {
    it('shows "Adding…" label and disables the submit button while pending', () => {
      mockUseCreateTodo({ isPending: true });
      render(<TodoForm />);

      expect(
        screen.getByRole('button', { name: /adding/i }),
      ).toBeDisabled();
    });

    it('disables the title input while pending', () => {
      mockUseCreateTodo({ isPending: true });
      render(<TodoForm />);

      expect(screen.getByLabelText(/title/i)).toBeDisabled();
    });

    it('disables the description textarea while pending', () => {
      mockUseCreateTodo({ isPending: true });
      render(<TodoForm />);

      expect(screen.getByLabelText(/description/i)).toBeDisabled();
    });
  });

  describe('error state', () => {
    it('displays the error message in an alert when the mutation fails', () => {
      mockUseCreateTodo({
        isError: true,
        error: new Error('Failed to create todo'),
      });
      render(<TodoForm />);

      expect(screen.getByRole('alert')).toHaveTextContent(
        'Failed to create todo',
      );
    });

    it('does not show an alert when the error is not an Error instance', () => {
      mockUseCreateTodo({ isError: true, error: undefined });
      render(<TodoForm />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
