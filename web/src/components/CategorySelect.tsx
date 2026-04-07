import { useGetCategories } from '@/hooks/useCategories';

interface CategorySelectProps {
  /** The currently selected category ID, or `null` for no category. */
  value: number | null;
  /** Called with the new category ID when the user picks one, or `null` to clear. */
  onChange: (categoryId: number | null) => void;
  /** Whether the select is disabled (e.g. while a parent form is submitting). */
  disabled?: boolean;
  /** Forwarded as the `id` attribute so a parent `<label htmlFor>` can associate correctly. */
  id?: string;
}

/**
 * Dropdown that lists all available categories fetched from the API.
 * Renders loading / error states inline while the data resolves.
 *
 * @example
 * <label htmlFor="todo-category">Category</label>
 * <CategorySelect
 *   id="todo-category"
 *   value={categoryId}
 *   onChange={setCategoryId}
 * />
 */
export const CategorySelect = ({
  value,
  onChange,
  disabled = false,
  id,
}: CategorySelectProps) => {
  const { data: categories, isLoading, isError } = useGetCategories();

  if (isLoading) {
    return (
      <select
        id={id}
        disabled
        aria-busy="true"
        className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm disabled:cursor-not-allowed disabled:bg-gray-100 w-full"
      >
        <option>Loading categories…</option>
      </select>
    );
  }

  if (isError) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Failed to load categories.
      </p>
    );
  }

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const raw = e.target.value;
    onChange(raw === '' ? null : Number(raw));
  };

  return (
    <select
      id={id}
      value={value ?? ''}
      onChange={handleChange}
      disabled={disabled}
      className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100 w-full"
    >
      <option value="">No category</option>
      {categories?.map((category) => (
        <option key={category.id} value={category.id}>
          {category.name}
        </option>
      ))}
    </select>
  );
};
