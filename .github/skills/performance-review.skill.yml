name: performance-review
description: >
  Auto-triggered when asked about performance. Reviews backend (FastAPI/SQLAlchemy)
  and frontend (React/React Query) for bottlenecks, N+1 queries, missing indexes,
  unnecessary re-renders, and network inefficiencies. Reports findings by severity.

trigger:
  - "performance review"
  - "is this performant"
  - "check performance"
  - "performance audit"
  - "optimize this"
  - "n+1"
  - "slow query"

instructions: |
  Review the codebase for performance risks. Separate measured findings from inferred risks.
  Always ask for baseline metrics if absent (p95 latency, query time, render timings).

  ## Backend Performance (api/)

  ### Database — Highest Impact
  - N+1 query detection:
    Bad:  `for todo in todos: category = repo.get_category(todo.category_id)`
    Good: Use joinedload() or selectinload() in a single query
  - Missing indexes on foreign keys (category_id on todos, etc.)
  - SELECT * when only specific columns needed — use .with_only_columns()
  - Full table scans on filtered endpoints — check WHERE clause indexes
  - Missing pagination on list endpoints that could return large datasets
  - Unoptimized ORDER BY on un-indexed columns

  ### API Layer
  - Over-fetching: returning full objects when only IDs/names are needed
  - Repeated expensive computation inside a loop — extract and cache
  - Missing pagination/filtering parameters on GET list endpoints
  - Synchronous blocking calls inside async functions

  ### SQLAlchemy Specifics
  - Using lazy loading in async context (raises MissingGreenlet error)
  - Missing `selectinload()` / `joinedload()` for related models
  - Repeated session.execute() for data that could be fetched in one query

  ---

  ## Frontend Performance (web/)

  ### React Rendering
  - Unnecessary re-renders: check if component re-renders when props haven't changed
  - Missing React.memo() on expensive pure components
  - Unstable function references passed as props (should use useCallback)
  - Unstable object references passed as props (should use useMemo)

  ### React Query Usage
  - Missing staleTime configuration (causes unnecessary refetches)
  - Missing cacheTime tuning for infrequently changing data
  - Duplicate requests for the same query key from multiple components
  - useQuery inside a loop — use parallel queries or batch fetch instead

  ### Network
  - Waterfall requests — sequential awaits where parallel would work
  - Fetching full entity list when only a subset is needed
  - No request deduplication awareness (React Query handles this, but verify queryKey consistency)

  ### Bundle
  - Large dependencies imported fully when tree-shaking would suffice
  - Missing code splitting on page-level routes (React.lazy / Suspense)

  ---

  ## Output Format

  Report findings in priority order:

  | Severity | Area | File:Line | Evidence | Recommendation | Expected Impact |
  |----------|------|-----------|----------|----------------|-----------------|

  Severity levels: High / Medium / Low

  After findings:
  1. Top 3 highest-impact fixes
  2. Metrics to measure improvement (what to benchmark before and after)
  3. Items that need profiling data before deciding (don't over-optimize blindly)
