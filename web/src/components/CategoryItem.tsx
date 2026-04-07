import { useState } from 'react';

import { useDeleteCategory, useUpdateCategory } from '@/hooks/useCategories';
import type { Category } from '@/types';

interface CategoryItemProps {
  category: Category;
}

export const CategoryItem = ({ category }: CategoryItemProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(category.name);
  const [editDescription, setEditDescription] = useState(category.description ?? '');

  const { mutate: updateCategory, isPending: isUpdating, isError: isUpdateError, error: updateError } =
    useUpdateCategory();
  const { mutate: deleteCategory, isPending: isDeleting } = useDeleteCategory();

  const isPending = isUpdating || isDeleting;

  const handleEditStart = () => {
    setEditName(category.name);
    setEditDescription(category.description ?? '');
    setIsEditing(true);
  };

  const handleEditCancel = () => {
    setIsEditing(false);
  };

  const handleEditSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const trimmedName = editName.trim();
    if (!trimmedName) return;

    updateCategory(
      {
        id: category.id,
        payload: {
          name: trimmedName,
          description: editDescription.trim() || null,
        },
      },
      {
        onSuccess: () => {
          setIsEditing(false);
        },
      },
    );
  };

  const handleDelete = () => {
    deleteCategory(category.id);
  };

  const updateErrorMessage =
    isUpdateError && updateError instanceof Error ? updateError.message : null;

  if (isEditing) {
    return (
      <li className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 shadow-sm">
        <form onSubmit={handleEditSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label
              htmlFor={`category-name-${category.id}`}
              className="text-sm font-medium text-gray-700"
            >
              Name <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id={`category-name-${category.id}`}
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              required
              disabled={isUpdating}
              aria-label="Category name"
              className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label
              htmlFor={`category-description-${category.id}`}
              className="text-sm font-medium text-gray-700"
            >
              Description
            </label>
            <textarea
              id={`category-description-${category.id}`}
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows={2}
              disabled={isUpdating}
              aria-label="Category description"
              className="resize-none rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100"
            />
          </div>

          {updateErrorMessage && (
            <p role="alert" className="text-sm text-red-600">
              {updateErrorMessage}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={handleEditCancel}
              disabled={isUpdating}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUpdating || !editName.trim()}
              className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isUpdating ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </li>
    );
  }

  return (
    <li className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-800">{category.name}</p>
        {category.description && (
          <p className="mt-0.5 text-sm text-gray-500">{category.description}</p>
        )}
      </div>

      <button
        type="button"
        onClick={handleEditStart}
        disabled={isPending}
        aria-label={`Edit "${category.name}"`}
        className="shrink-0 rounded p-1 text-gray-400 hover:bg-indigo-50 hover:text-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
        </svg>
      </button>

      <button
        type="button"
        onClick={handleDelete}
        disabled={isPending}
        aria-label={`Delete "${category.name}"`}
        className="shrink-0 rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </li>
  );
};
