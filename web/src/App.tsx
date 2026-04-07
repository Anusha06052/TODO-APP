import { NavLink, Navigate, Route, Routes } from 'react-router-dom';

import CategoryPage from '@/pages/CategoryPage';
import TodoPage from '@/pages/TodoPage';

const App = () => {
  return (
    <>
      <nav className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-2xl gap-6 px-4 py-3">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `text-sm font-medium transition-colors ${
                isActive ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-800'
              }`
            }
          >
            Todos
          </NavLink>
          <NavLink
            to="/categories"
            className={({ isActive }) =>
              `text-sm font-medium transition-colors ${
                isActive ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-800'
              }`
            }
          >
            Categories
          </NavLink>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<TodoPage />} />
        <Route path="/categories" element={<CategoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

export default App;
