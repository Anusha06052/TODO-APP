import { TodoForm } from '@/components/TodoForm';
import TodoList from '@/components/TodoList';

const TodoPage = () => {
  return (
    <main className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-8 text-2xl font-bold text-gray-900">My Todos</h1>

      <section aria-label="Add a new todo" className="mb-8">
        <TodoForm />
      </section>

      <section aria-label="Todo list">
        <TodoList />
      </section>
    </main>
  );
};

export default TodoPage;
