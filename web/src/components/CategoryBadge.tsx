import { useGetCategory } from '@/hooks/useCategories';

interface CategoryBadgeProps {
  categoryId: number;
}

/**
 * Displays the name of a category as a styled badge.
 * Fetches the category by ID and renders loading / error states inline.
 *
 * @example
 * <CategoryBadge categoryId={3} />
 */
export const CategoryBadge = ({ categoryId }: CategoryBadgeProps) => {
  const { data: category, isLoading, isError } = useGetCategory(categoryId);

  if (isLoading) {
    return (
      <span className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-400">
        …
      </span>
    );
  }

  if (isError || !category) {
    return null;
  }

  return (
    <span className="inline-block rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
      {category.name}
    </span>
  );
};
