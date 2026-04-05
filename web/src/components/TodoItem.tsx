import { useDeleteTodo, useUpdateTodo } from '@/hooks/useTodos';
import type { Todo } from '@/types';

interface TodoItemProps {
  todo: Todo;
}

export const TodoItem = ({ todo }: TodoItemProps) => {
  const { mutate: updateTodo, isPending: isUpdating } = useUpdateTodo();
  const { mutate: deleteTodo, isPending: isDeleting } = useDeleteTodo();

  const isPending = isUpdating || isDeleting;

  const handleToggle = () => {
    updateTodo({ id: todo.id, payload: { is_completed: !todo.is_completed } });
  };

  const handleDelete = () => {
    deleteTodo(todo.id);
  };

  return (
    <li className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <input
        type="checkbox"
        id={`todo-toggle-${todo.id}`}
        checked={todo.is_completed}
        onChange={handleToggle}
        disabled={isPending}
        aria-label={`Mark "${todo.title}" as ${todo.is_completed ? 'incomplete' : 'complete'}`}
        className="mt-1 h-4 w-4 cursor-pointer rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 disabled:cursor-not-allowed"
      />

      <div className="min-w-0 flex-1">
        <label
          htmlFor={`todo-toggle-${todo.id}`}
          className={`block cursor-pointer text-sm font-medium ${
            todo.is_completed ? 'text-gray-400 line-through' : 'text-gray-800'
          }`}
        >
          {todo.title}
        </label>

        {todo.description && (
          <p className={`mt-0.5 text-sm ${todo.is_completed ? 'text-gray-300' : 'text-gray-500'}`}>
            {todo.description}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={handleDelete}
        disabled={isPending}
        aria-label={`Delete "${todo.title}"`}
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
