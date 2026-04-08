import { useEffect, useState } from 'react';

import { useCreateTodo } from '@/hooks/useTodos';
import type { Category, CreateTodoDto, Todo, UpdateTodoDto } from '@/types';

interface TodoFormProps {
  editingTodo?: Todo | null;
  onSuccess?: () => void;
  onCancel?: () => void;
  onUpdate?: (id: number, payload: UpdateTodoDto) => void;
  categories?: Category[];
  isCategoriesLoading?: boolean;
  isCategoriesError?: boolean;
}

export const TodoForm = ({
  editingTodo,
  onSuccess,
  onCancel,
  onUpdate,
  categories,
  isCategoriesLoading = false,
  isCategoriesError = false,
}: TodoFormProps) => {
  const isEditing = editingTodo != null;
  const hasCategories = categories !== undefined;

  const [title, setTitle] = useState(editingTodo?.title ?? '');
  const [description, setDescription] = useState(editingTodo?.description ?? '');
  const [categoryId, setCategoryId] = useState<number | null>(editingTodo?.category_id ?? null);

  useEffect(() => {
    setTitle(editingTodo?.title ?? '');
    setDescription(editingTodo?.description ?? '');
    setCategoryId(editingTodo?.category_id ?? null);
  }, [editingTodo]);

  const { mutate: createTodo, isPending, isError, error } = useCreateTodo();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const trimmedTitle = title.trim();
    if (!trimmedTitle) return;

    const trimmedDescription = description.trim() || null;

    if (isEditing && onUpdate) {
      onUpdate(
        editingTodo.id,
        {
          title: trimmedTitle,
          description: trimmedDescription,
          ...(hasCategories && { category_id: categoryId }),
        },
      );
      onSuccess?.();
    } else {
      const payload: CreateTodoDto = {
        title: trimmedTitle,
        description: trimmedDescription,
        ...(hasCategories && { category_id: categoryId }),
      };

      createTodo(payload, {
        onSuccess: () => {
          setTitle('');
          setDescription('');
          setCategoryId(null);
          onSuccess?.();
        },
      });
    }
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

      {hasCategories && (
        <div className="flex flex-col gap-1">
          <label htmlFor="todo-category" className="text-sm font-medium text-gray-700">
            Category
          </label>
          {isCategoriesError ? (
            <p role="alert" className="text-sm text-red-600">
              Failed to load categories.
            </p>
          ) : (
            <select
              id="todo-category"
              value={categoryId ?? ''}
              onChange={(e) =>
                setCategoryId(e.target.value ? Number(e.target.value) : null)
              }
              disabled={isPending || isCategoriesLoading}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100"
            >
              <option value="">No category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}

      <div className="flex justify-end gap-2">
        {isEditing && onCancel && (
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
          disabled={isPending || !title.trim()}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isPending ? (isEditing ? 'Saving…' : 'Adding…') : isEditing ? 'Save Changes' : 'Add Todo'}
        </button>
      </div>
    </form>
  );
};
