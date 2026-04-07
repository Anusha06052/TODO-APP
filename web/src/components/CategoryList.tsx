import { useGetCategories } from '@/hooks/useCategories';

import { CategoryItem } from './CategoryItem';

const CategoryList = () => {
  const { data: categories, isLoading, isError } = useGetCategories();

  if (isLoading) {
    return (
      <p className="text-center text-sm text-gray-500" role="status">
        Loading categories…
      </p>
    );
  }

  if (isError) {
    return (
      <p className="text-center text-sm text-red-500" role="alert">
        Failed to load categories. Please try again.
      </p>
    );
  }

  if (!Array.isArray(categories) || categories.length === 0) {
    return (
      <p className="text-center text-sm text-gray-400">
        No categories yet. Add one above!
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="Category list">
      {categories.map((category) => (
        <CategoryItem key={category.id} category={category} />
      ))}
    </ul>
  );
};

export default CategoryList;
