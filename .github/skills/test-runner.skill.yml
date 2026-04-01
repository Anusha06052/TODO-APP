name: test-runner
description: >
  Auto-triggered when asked to run tests. Detects context (backend or frontend),
  runs the correct test suite, and reports results with suggested fixes for failures.

trigger:
  - "run tests"
  - "run the tests"
  - "run pytest"
  - "run vitest"
  - "check tests"
  - "are tests passing"
  - "test results"

instructions: |
  Determine which test suite to run based on context, execute it, and report results.

  ## Detection Rules

  Run BACKEND tests if:
  - User is working in /api or mentions Python/backend/pytest
  - Changed files are in api/

  Run FRONTEND tests if:
  - User is working in /web or mentions React/TypeScript/vitest
  - Changed files are in web/

  If unclear, ask: "Should I run backend tests (pytest) or frontend tests (vitest)?"

  ## Backend Test Execution

  Bash / macOS / Linux:
    cd api && python -m pytest -v --tb=short

  PowerShell / Windows:
    Set-Location api; python -m pytest -v --tb=short

  Windows fallback (if `python` not in PATH):
    Set-Location api; py -m pytest -v --tb=short

  With coverage:
    cd api && python -m pytest --cov=app --cov-report=term-missing -v

  ## Frontend Test Execution

  Bash:
    cd web && npx vitest run

  PowerShell:
    Set-Location web; npx vitest run

  With coverage:
    cd web && npx vitest run --coverage

  ## Reporting Format

  After execution, always report:

  ```
  Test Suite: [Backend pytest | Frontend vitest]
  ─────────────────────────────────────────────
  Total:   X tests
  Passed:  X ✅
  Failed:  X ❌
  Skipped: X ⏭️
  Duration: X.XXs
  ```

  For each FAILURE, report:
  - Test name (full path)
  - File and line number
  - Error message (brief)
  - Suggested fix (concrete — which file/function to change)

  ## Rules
  - Never modify test files to make them pass — report the failure and suggest a source code fix.
  - If tests fail due to missing dependencies: suggest the install command.
  - If tests fail due to missing environment variables: point to .env.example.
  - If tests fail due to missing DB: suggest running `alembic upgrade head` first.
  - Run from repo root — use shell-native directory switching (Set-Location or cd).
