import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CategoryForm } from '@/components/CategoryForm';
import { useCreateCategory } from '@/hooks/useCategories';

vi.mock('@/hooks/useCategories');

const mockMutate = vi.fn();

const mockUseCreateCategory = (
  overrides: Partial<ReturnType<typeof useCreateCategory>> = {},
) => {
  vi.mocked(useCreateCategory).mockReturnValue({
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: null,
    ...overrides,
  } as ReturnType<typeof useCreateCategory>);
};

describe('CategoryForm', () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockUseCreateCategory();
  });

  // ── Rendering ─────────────────────────────────────────────────────────────

  describe('rendering', () => {
    it('renders the name input, description textarea, and submit button', () => {
      render(<CategoryForm />);

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /add category/i }),
      ).toBeInTheDocument();
    });

    it('submit button is disabled when the name field is empty', () => {
      render(<CategoryForm />);

      expect(
        screen.getByRole('button', { name: /add category/i }),
      ).toBeDisabled();
    });

    it('does not render the cancel button when onCancel is not provided', () => {
      render(<CategoryForm />);

      expect(
        screen.queryByRole('button', { name: /cancel/i }),
      ).not.toBeInTheDocument();
    });

    it('renders the cancel button when onCancel is provided', () => {
      render(<CategoryForm onCancel={vi.fn()} />);

      expect(
        screen.getByRole('button', { name: /cancel/i }),
      ).toBeInTheDocument();
    });

    it('does not show an error alert when there is no error', () => {
      render(<CategoryForm />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // ── Validation ────────────────────────────────────────────────────────────

  describe('validation', () => {
    it('enables the submit button once name text is entered', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      await user.type(screen.getByLabelText(/name/i), 'Work');

      expect(
        screen.getByRole('button', { name: /add category/i }),
      ).toBeEnabled();
    });

    it('keeps submit button disabled when name contains only whitespace', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      await user.type(screen.getByLabelText(/name/i), '   ');

      expect(
        screen.getByRole('button', { name: /add category/i }),
      ).toBeDisabled();
    });

    it('does not call mutate when name is whitespace-only and form is submitted', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, '   ');
      await user.keyboard('{Enter}');

      expect(mockMutate).not.toHaveBeenCalled();
    });
  });

  // ── Submission ────────────────────────────────────────────────────────────

  describe('submission', () => {
    it('calls mutate with trimmed name and null description when description is omitted', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      await user.type(screen.getByLabelText(/name/i), '  Work  ');
      await user.click(screen.getByRole('button', { name: /add category/i }));

      expect(mockMutate).toHaveBeenCalledOnce();
      expect(mockMutate).toHaveBeenCalledWith(
        { name: 'Work', description: null },
        expect.any(Object),
      );
    });

    it('calls mutate with name and trimmed description when both fields are filled', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      await user.type(screen.getByLabelText(/name/i), 'Work');
      await user.type(
        screen.getByLabelText(/description/i),
        '  Work-related tasks  ',
      );
      await user.click(screen.getByRole('button', { name: /add category/i }));

      expect(mockMutate).toHaveBeenCalledOnce();
      expect(mockMutate).toHaveBeenCalledWith(
        { name: 'Work', description: 'Work-related tasks' },
        expect.any(Object),
      );
    });

    it('calls mutate with null description when description contains only whitespace', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      await user.type(screen.getByLabelText(/name/i), 'Work');
      await user.type(screen.getByLabelText(/description/i), '   ');
      await user.click(screen.getByRole('button', { name: /add category/i }));

      expect(mockMutate).toHaveBeenCalledOnce();
      expect(mockMutate).toHaveBeenCalledWith(
        { name: 'Work', description: null },
        expect.any(Object),
      );
    });
  });

  // ── Success behaviour ─────────────────────────────────────────────────────

  describe('success behaviour', () => {
    beforeEach(() => {
      mockMutate.mockImplementation(
        (_payload: unknown, options?: { onSuccess?: () => void }) => {
          options?.onSuccess?.();
        },
      );
    });

    it('clears both inputs after a successful mutation', async () => {
      const user = userEvent.setup();
      render(<CategoryForm />);

      await user.type(screen.getByLabelText(/name/i), 'Work');
      await user.type(screen.getByLabelText(/description/i), 'Work tasks');
      await user.click(screen.getByRole('button', { name: /add category/i }));

      expect(screen.getByLabelText(/name/i)).toHaveValue('');
      expect(screen.getByLabelText(/description/i)).toHaveValue('');
    });

    it('calls the onSuccess prop after a successful mutation', async () => {
      const onSuccess = vi.fn();
      const user = userEvent.setup();
      render(<CategoryForm onSuccess={onSuccess} />);

      await user.type(screen.getByLabelText(/name/i), 'Work');
      await user.click(screen.getByRole('button', { name: /add category/i }));

      expect(onSuccess).toHaveBeenCalledOnce();
    });
  });

  // ── Pending state ─────────────────────────────────────────────────────────

  describe('pending state', () => {
    it('shows "Adding…" label and disables the submit button while pending', () => {
      mockUseCreateCategory({ isPending: true });
      render(<CategoryForm />);

      expect(
        screen.getByRole('button', { name: /adding/i }),
      ).toBeDisabled();
    });

    it('disables the name input while pending', () => {
      mockUseCreateCategory({ isPending: true });
      render(<CategoryForm />);

      expect(screen.getByLabelText(/name/i)).toBeDisabled();
    });

    it('disables the description textarea while pending', () => {
      mockUseCreateCategory({ isPending: true });
      render(<CategoryForm />);

      expect(screen.getByLabelText(/description/i)).toBeDisabled();
    });

    it('disables the cancel button while pending', () => {
      mockUseCreateCategory({ isPending: true });
      render(<CategoryForm onCancel={vi.fn()} />);

      expect(
        screen.getByRole('button', { name: /cancel/i }),
      ).toBeDisabled();
    });
  });

  // ── Error state ───────────────────────────────────────────────────────────

  describe('error state', () => {
    it('displays the error message in an alert when the mutation fails', () => {
      mockUseCreateCategory({
        isError: true,
        error: new Error('Failed to create category'),
      });
      render(<CategoryForm />);

      expect(screen.getByRole('alert')).toHaveTextContent(
        'Failed to create category',
      );
    });

    it('does not show an alert when isError is true but error is not an Error instance', () => {
      mockUseCreateCategory({ isError: true, error: undefined });
      render(<CategoryForm />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // ── Cancel behaviour ──────────────────────────────────────────────────────

  describe('cancel behaviour', () => {
    it('calls onCancel when the cancel button is clicked', async () => {
      const onCancel = vi.fn();
      const user = userEvent.setup();
      render(<CategoryForm onCancel={onCancel} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onCancel).toHaveBeenCalledOnce();
    });
  });
});
