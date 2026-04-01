---
applyTo: "web/src/**/*.{ts,tsx}"
---

# TypeScript / React Language Instructions
# Auto-loaded for all .ts/.tsx files in /web/src. Layered on top of copilot-instructions.md.

## Component Style

```tsx
// ✅ Correct — named export, arrow function, no React.FC
interface TodoItemProps {
  todo: Todo;
  onToggle: (id: number) => void;
  onDelete: (id: number) => void;
}

export const TodoItem = ({ todo, onToggle, onDelete }: TodoItemProps) => {
  return (
    <div>
      <span>{todo.title}</span>
      <button onClick={() => onToggle(todo.id)}>Toggle</button>
      <button onClick={() => onDelete(todo.id)}>Delete</button>
    </div>
  );
};

// ❌ Wrong — class component, React.FC, default export, inline props type
export default class TodoItem extends React.Component<{ todo: any }> {}
```

## Props & Types

- Props as named interfaces — never inline types in component signatures.
- All interfaces in `src/types/` — one file per domain (`todo.ts`, `category.ts`).
- Export all types from `src/types/index.ts` barrel file.
- `interface` for object shapes. `type` for unions, intersections, primitives.
- No `any` type. Use `unknown` + type narrowing if type is truly dynamic.

```typescript
// src/types/todo.ts
export interface Todo {
  id: number;
  title: string;
  description: string | null;
  isCompleted: boolean;
  categoryId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface TodoCreate {
  title: string;
  description?: string;
  categoryId?: number;
}

export interface TodoUpdate {
  title?: string;
  description?: string;
  isCompleted?: boolean;
  categoryId?: number | null;
}
```

## React Query (Server State)

```typescript
// src/hooks/useTodos.ts — one file per domain

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { todoService } from '@/services/todoService';
import type { TodoCreate, TodoUpdate } from '@/types';

export const useTodos = () =>
  useQuery({
    queryKey: ['todos'],
    queryFn: todoService.getAll,
  });

export const useTodo = (id: number) =>
  useQuery({
    queryKey: ['todos', id],
    queryFn: () => todoService.getById(id),
    enabled: !!id,
  });

export const useCreateTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TodoCreate) => todoService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

export const useUpdateTodo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TodoUpdate }) =>
      todoService.update(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
      queryClient.invalidateQueries({ queryKey: ['todos', id] });
    },
  });
};
```

## Axios Service Layer

```typescript
// src/services/api.ts — single Axios instance
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// src/services/todoService.ts — one file per domain
import { api } from './api';
import type { Todo, TodoCreate, TodoUpdate } from '@/types';

export const todoService = {
  getAll: async (): Promise<Todo[]> => {
    const { data } = await api.get<Todo[]>('/todos');
    return data; // always unwrap — never return AxiosResponse
  },
  getById: async (id: number): Promise<Todo> => {
    const { data } = await api.get<Todo>(`/todos/${id}`);
    return data;
  },
  create: async (payload: TodoCreate): Promise<Todo> => {
    const { data } = await api.post<Todo>('/todos', payload);
    return data;
  },
  update: async (id: number, payload: TodoUpdate): Promise<Todo> => {
    const { data } = await api.put<Todo>(`/todos/${id}`, payload);
    return data;
  },
  delete: async (id: number): Promise<void> => {
    await api.delete(`/todos/${id}`);
  },
};
```

## Error & Loading States

```tsx
// Every component using useQuery MUST handle all three states
export const TodoList = () => {
  const { data: todos, isLoading, isError, error } = useTodos();

  if (isLoading) return <div role="status">Loading todos...</div>;
  if (isError) return <div role="alert">Error: {(error as Error).message}</div>;
  if (!todos?.length) return <div>No todos yet. Create one!</div>;

  return (
    <ul>
      {todos.map((todo) => (
        <TodoItem key={todo.id} todo={todo} />
      ))}
    </ul>
  );
};
```

## State Management Rules

- **Server state**: React Query only — fetched data, cache, sync.
- **UI state**: `useState` — modals open/close, form input values, toggles.
- No global state library (Redux, Zustand) needed for this app.
- Derive state from existing state where possible — don't duplicate.

## Zod — Runtime Validation

```typescript
// Use Zod for validating API responses when shape is uncertain
import { z } from 'zod';

const TodoSchema = z.object({
  id: z.number(),
  title: z.string().min(1).max(255),
  isCompleted: z.boolean(),
  createdAt: z.string(),
});

export type Todo = z.infer<typeof TodoSchema>;
```

## Exports & File Organization

- Named exports everywhere. Default exports only for page files if router requires.
- Barrel exports from `src/types/index.ts`.
- Keep components, hooks, services in separate files — never mix concerns.
- File names: `PascalCase` for components (`TodoItem.tsx`), `camelCase` for others.

## Styling

- CSS Modules or Tailwind utility classes only.
- No inline `style={{ }}` props (except truly dynamic values like computed widths).
- Component-specific styles in `ComponentName.module.css` alongside the component.

## Testing (Vitest + RTL)

```tsx
// Co-located test file: TodoItem.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TodoItem } from './TodoItem';

describe('TodoItem', () => {
  const mockTodo = { id: 1, title: 'Test todo', isCompleted: false };

  it('renders todo title', () => {
    render(<TodoItem todo={mockTodo} onToggle={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText('Test todo')).toBeInTheDocument();
  });

  it('calls onDelete when delete button clicked', async () => {
    const onDelete = vi.fn();
    render(<TodoItem todo={mockTodo} onToggle={vi.fn()} onDelete={onDelete} />);
    await userEvent.click(screen.getByRole('button', { name: /delete/i }));
    expect(onDelete).toHaveBeenCalledWith(1);
  });
});
```
