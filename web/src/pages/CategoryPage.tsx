import { CategoryForm } from '@/components/CategoryForm';
import CategoryList from '@/components/CategoryList';

const CategoryPage = () => {
  return (
    <main className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-8 text-2xl font-bold text-gray-900">Categories</h1>

      <section aria-label="Add a new category" className="mb-8">
        <CategoryForm />
      </section>

      <section aria-label="Category list">
        <CategoryList />
      </section>
    </main>
  );
};

export default CategoryPage;
