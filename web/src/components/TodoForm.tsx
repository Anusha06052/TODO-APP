import { useState } from 'react';

import { useCreateTodo } from '@/hooks/useTodos';
import type { CreateTodoDto } from '@/types';

interface TodoFormProps {
  onSuccess?: () => void;
}

export const TodoForm = ({ onSuccess }: TodoFormProps) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const { mutate: createTodo, isPending, isError, error } = useCreateTodo();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const trimmedTitle = title.trim();
    if (!trimmedTitle) return;

    const payload: CreateTodoDto = {
      title: trimmedTitle,
      description: description.trim() || null,
    };

    createTodo(payload, {
      onSuccess: () => {
        setTitle('');
        setDescription('');
        onSuccess?.();
      },
    });
  };

  const errorMessage =
    isError && error instanceof Error ? error.message : null;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <label htmlFor="todo-title" className="text-sm font-medium text-gray-700">
          Title <span aria-hidden="true" className="text-red-500">*</span>
        </label>
        <input
          id="todo-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          required
          disabled={isPending}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="todo-description" className="text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          id="todo-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add an optional description…"
          rows={3}
          disabled={isPending}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100 resize-none"
        />
      </div>

      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}

      <button
        type="submit"
        disabled={isPending || !title.trim()}
        className="self-end rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isPending ? 'Adding…' : 'Add Todo'}
      </button>
    </form>
  );
};
