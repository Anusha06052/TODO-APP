import { useState } from 'react';

import { Link } from 'react-router-dom';

import { TodoForm } from '@/components/TodoForm';
import TodoList from '@/components/TodoList';
import type { Todo } from '@/types';

const TodoPage = () => {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleFormSuccess = () => {
    setEditingTodo(null);
  };

  const handleCancel = () => {
    setEditingTodo(null);
  };

  return (
    <main className="mx-auto max-w-2xl px-4 py-10">
      <div className="mb-8 flex items-baseline justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My Todos</h1>
        <Link
          to="/categories"
          className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
        >
          Manage categories →
        </Link>
      </div>

      <section
        aria-label={editingTodo ? 'Edit todo' : 'Add a new todo'}
        className="mb-8"
      >
        {editingTodo && (
          <p className="mb-2 text-sm font-medium text-indigo-600">
            Editing: <span className="font-semibold">{editingTodo.title}</span>
          </p>
        )}
        <TodoForm
          editingTodo={editingTodo}
          onSuccess={handleFormSuccess}
          onCancel={handleCancel}
        />
      </section>

      <section aria-label="Todo list">
        <TodoList onEdit={handleEdit} />
      </section>
    </main>
  );
};

export default TodoPage;
