import { useState } from 'react';

import { useCreateCategory } from '@/hooks/useCategories';

interface CategoryFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export const CategoryForm = ({ onSuccess, onCancel }: CategoryFormProps) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const { mutate: createCategory, isPending, isError, error } = useCreateCategory();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const trimmedName = name.trim();
    if (!trimmedName) return;

    createCategory(
      {
        name: trimmedName,
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          setName('');
          setDescription('');
          onSuccess?.();
        },
      },
    );
  };

  const errorMessage = isError && error instanceof Error ? error.message : null;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <label htmlFor="category-name" className="text-sm font-medium text-gray-700">
          Name <span aria-hidden="true" className="text-red-500">*</span>
        </label>
        <input
          id="category-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Category name"
          required
          disabled={isPending}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="category-description" className="text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          id="category-description"
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

      <div className="flex justify-end gap-2">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isPending}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isPending || !name.trim()}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isPending ? 'Adding…' : 'Add Category'}
        </button>
      </div>
    </form>
  );
};
