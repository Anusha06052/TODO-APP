name: api-endpoint-generation
description: >
  Auto-triggered when generating FastAPI endpoints. Generates all three layers
  (Routes → Services → Repositories) together with correct schemas, DI wiring,
  status codes, error handling, docstrings, and Alembic migration guidance.

trigger:
  - "generate endpoint"
  - "create endpoint"
  - "add endpoint"
  - "generate crud"
  - "create crud"
  - "add route"
  - "generate api for"

instructions: |
  Generate complete, production-ready FastAPI endpoint sets following the 3-layer architecture.

  ## Required Information
  Ask for missing details before generating:
  - Resource name (singular + plural): e.g., Todo / todos, Category / categories
  - Operations needed: GET list, GET by id, POST, PUT, DELETE (PATCH optional)
  - Request fields with types and validation constraints
  - Response fields
  - Business rules and validation logic (e.g., "title must be unique", "cannot delete if todos assigned")
  - Error cases and expected HTTP status codes

  ## Generation Order (always follow this sequence)

  1. SQLAlchemy model (app/models/<resource>.py)
      - DeclarativeBase, Mapped[], mapped_column()
      - Include created_at, updated_at with server_default/onupdate

  2. Pydantic schemas (app/schemas/<resource>.py)
      - <Resource>Base — shared fields with Field() validators
      - <Resource>Create — inherits Base
      - <Resource>Update — all fields Optional
      - <Resource>Response — includes id, timestamps, model_config = ConfigDict(from_attributes=True)

  3. Repository (app/repositories/<resource>_repository.py)
      - Class <Resource>Repository(session: AsyncSession)
      - Methods: get_all(), get_by_id(), create(), update(), delete()
      - All async, use select()/update()/delete() (not legacy Query API)
      - Return ORM model or None (no HTTPException here)
      - flush() after add — let service commit()

  4. Service (app/services/<resource>_service.py)
      - Class <Resource>Service(repository: <Resource>Repository)
      - Methods mirror repository but enforce business rules
      - Raise HTTPException(404) when not found
      - Raise HTTPException(409) for conflicts/duplicates
      - Call session.commit() then session.refresh() after writes
      - Log operations at INFO level

  5. Router (app/routes/<resource>_router.py)
      - APIRouter(prefix="/api/v1/<resources>", tags=["<resources>"])
      - GET /          → list, 200, list[<Resource>Response]
      - GET /{id}      → get one, 200, <Resource>Response, 404
      - POST /         → create, 201, <Resource>Response, 422
      - PUT /{id}      → update, 200, <Resource>Response, 404, 422
      - DELETE /{id}   → delete, 204, None, 404

  6. DI wiring functions (add to router file or separate deps.py)
      ```python
      def get_<resource>_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> <Resource>Repository:
          return <Resource>Repository(session)

      def get_<resource>_service(repo: Annotated[<Resource>Repository, Depends(get_<resource>_repository)]) -> <Resource>Service:
          return <Resource>Service(repo)
      ```

  7. Register in app/main.py
      ```python
      app.include_router(<resource>_router)
      ```

  8. Note if Alembic migration is needed (always is for new models)

  ## Code Quality Checklist
  - All functions: async def + full type hints + Google-style docstrings
  - Status codes use `from fastapi import status`: `status.HTTP_201_CREATED`
  - Response models declared on every router decorator
  - Summary and description on each router decorator
  - No SQLAlchemy in routes. No HTTPException in repositories.
  - All write operations commit in service layer (not repository)

  ## Output Summary
  After generating, provide:
  - Files created/modified list
  - Endpoint table (method, path, status codes)
  - Business rules implemented
  - Migration command needed
  - Next steps (tests to write)
