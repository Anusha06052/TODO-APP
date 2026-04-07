import { useGetTodos } from '@/hooks/useTodos';
import type { Todo } from '@/types';

import { TodoItem } from './TodoItem';

interface TodoListProps {
  onEdit: (todo: Todo) => void;
}

const TodoList = ({ onEdit }: TodoListProps) => {
  const { data: todos, isLoading, isError } = useGetTodos();

  if (isLoading) {
    return (
      <p className="text-center text-sm text-gray-500" role="status">
        Loading todos…
      </p>
    );
  }

  if (isError) {
    return (
      <p className="text-center text-sm text-red-500" role="alert">
        Failed to load todos. Please try again.
      </p>
    );
  }

  if (!Array.isArray(todos) || todos.length === 0) {
    return (
      <p className="text-center text-sm text-gray-400">
        No todos yet. Add one above!
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="Todo list">
      {todos.map((todo) => (
        <TodoItem key={todo.id} todo={todo} onEdit={onEdit} />
      ))}
    </ul>
  );
};

export default TodoList;
