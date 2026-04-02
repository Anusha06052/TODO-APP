name: test-generator
description: >
  Auto-triggered when generating tests. Enforces AAA pattern, pytest-asyncio
  for backend, Vitest + RTL for frontend. Covers happy path, edge cases,
  and error cases. Names tests descriptively and mocks all external dependencies.

trigger:
  - "generate tests"
  - "write tests"
  - "add unit tests"
  - "add tests"
  - "create test file"
  - "test coverage"
  - "create tests for"

instructions: |
  When triggered, generate tests following these standards exactly.

  ## Backend Tests (api/tests/)

  ### Setup
  - Framework: pytest + pytest-asyncio
  - File naming: test_<module>.py (e.g., test_todo_service.py, test_todo_repository.py)
  - One test file per source module, mirroring app structure
  - conftest.py for shared fixtures (test session, test client, sample data factories)

  ### Structure per test
  Always use Arrange / Act / Assert with comments:
  ```python
  async def test_create_todo_success():
      # Arrange
      mock_repo = AsyncMock(spec=TodoRepository)
      mock_repo.get_by_id.return_value = None
      mock_repo.create.return_value = Todo(id=1, title="Test", is_completed=False)
      service = TodoService(mock_repo)
      payload = TodoCreate(title="Test")

      # Act
      result = await service.create(payload)

      # Assert
      assert result.id == 1
      assert result.title == "Test"
      mock_repo.create.assert_called_once_with(payload)
  ```

  ### Naming convention
  test_<action>_<condition>_<expected_outcome>
  Examples:
  - test_create_todo_success_returns_todo
  - test_get_todo_not_found_raises_404
  - test_delete_todo_with_category_assigned_raises_409
  - test_get_all_todos_empty_returns_empty_list

  ### Service layer tests (mock the repository)
  - Use AsyncMock(spec=TodoRepository) — never use a real DB
  - Test: success case, 404 not found, 409 conflict, empty collection
  - Verify commit() is called on write operations
  - Verify HTTPException status codes match expectations

  ### Repository layer tests (mock AsyncSession)
  - Use AsyncMock(spec=AsyncSession)
  - Test that correct SQLAlchemy queries are built
  - Test that results are properly mapped/returned

  ### Route layer tests (httpx.AsyncClient)
  - Use httpx.AsyncClient with ASGI transport
  - Test each endpoint: correct status code + response shape
  - Test: 200/201/204 success, 404, 409, 422 validation error
  - Mock the service layer (not repository) for route tests

  ### Coverage targets
  - Service layer: 100% of public methods
  - Repository layer: all CRUD methods
  - Routes: all endpoints + error paths

  ---

  ## Frontend Tests (web/src/**/*.test.tsx)

  ### Setup
  - Framework: Vitest + @testing-library/react + @testing-library/user-event
  - Co-locate tests: TodoItem.test.tsx alongside TodoItem.tsx
  - vitest.setup.ts for global setup (@testing-library/jest-dom matchers)

  ### What to mock
  - Mock service functions with vi.mock('@/services/todoService')
  - Wrap components in QueryClientProvider with a fresh QueryClient per test
  - Never mock React Query internals (useQuery, useMutation)
  - Never call real API endpoints in tests

  ### Test structure per component
  ```tsx
  describe('TodoItem', () => {
    it('renders todo title correctly', () => { /* renders */ });
    it('shows completed state when todo is completed', () => { /* state */ });
    it('calls onToggle with correct id when toggle clicked', async () => { /* interaction */ });
    it('calls onDelete with correct id when delete clicked', async () => { /* interaction */ });
  });
  ```

  ### Mandatory test cases per component
  1. Renders correctly with valid props (happy path)
  2. Handles loading state (skeleton / spinner visible)
  3. Handles error state (user-friendly message visible)
  4. Handles empty state (empty list message visible)
  5. User interactions trigger correct callbacks

  ### Query selectors
  - Prefer: getByRole, getByText, getByLabelText
  - Avoid: getByTestId (use only when no semantic alternative exists)
  - Use: screen.getByRole('button', { name: /delete/i })

  ---

  ## General Rules
  - Every test must be independent — no shared mutable state between tests.
  - No test should depend on another test having run first.
  - Both positive (success) and negative (failure/error) cases required.
  - Test names must describe WHAT is tested and WHAT outcome is expected.
  - Never modify production code to make tests pass — fix the code to meet the test contract.
