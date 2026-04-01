name: db-migration
description: >
  Auto-triggered when modifying SQLAlchemy models or requesting Alembic migrations.
  Guides safe, reversible schema evolution. Catches data-loss risks, ordering issues,
  and SQL Server-specific constraints before migration is applied.

trigger:
  - "create migration"
  - "generate migration"
  - "alembic migration"
  - "database migration"
  - "schema change"
  - "model changed"
  - "add column"
  - "add table"

instructions: |
  Guide safe Alembic migration creation and review for async SQL Server via aioodbc.

  ## Before Generating

  Gather the following if not already known:
  - Type of change: create table / add column / alter column / drop column / add index / add FK
  - Affected tables and column names with types
  - Nullability and default value requirements
  - Whether existing data needs backfill
  - Whether this is reversible (can downgrade() undo it safely?)

  ## Safety Rules

  1. Prefer additive, backward-compatible changes first.
  2. For new non-null columns on existing tables — use staged approach:
     Step 1: Add column as nullable (no data loss risk)
     Step 2: Backfill existing rows with a default value
     Step 3: Add NOT NULL constraint in a separate migration
  3. Never DROP a column without explicit confirmation — data loss is permanent.
  4. Never DROP a table without explicit confirmation.
  5. Always implement downgrade() — even if it's just a column drop (document the data loss risk).
  6. FK constraints must be dropped BEFORE the referenced table in downgrade().
  7. For large tables: note that adding indexes and NOT NULL constraints can lock the table.

  ## Migration Workflow

  Step 1: Update SQLAlchemy model(s) in app/models/
  Step 2: Generate migration:
    `alembic revision --autogenerate -m "<description>"`
    Description format: <verb>_<what>_<to_what>
    Examples: "add_category_id_to_todos", "create_categories_table", "add_title_index_to_todos"
  Step 3: Review generated file in alembic/versions/ — autogenerate is not always correct
  Step 4: Verify upgrade() implements all intended changes
  Step 5: Verify downgrade() properly reverses all changes in correct order
  Step 6: Check SQL Server compatibility (IDENTITY columns, NVARCHAR vs VARCHAR, etc.)
  Step 7: Apply: `alembic upgrade head`
  Step 8: Verify with: `alembic current` and spot-check DB schema

  ## Review Checklist

  - [ ] Migration message describes the change clearly
  - [ ] upgrade() implements all model changes
  - [ ] downgrade() reverses all changes (correct FK drop order)
  - [ ] Non-null new columns have server_default or nullable=True
  - [ ] No accidental DROP operations from autogenerate noise
  - [ ] Foreign key names are explicit (not auto-generated) for portability
  - [ ] Data-loss risk assessed and documented in migration file docstring
  - [ ] Migration tested locally before committing

  ## SQL Server Specifics

  - Use `sa.NVARCHAR` for string columns (not VARCHAR) for Unicode support
  - IDENTITY is auto-handled by SQLAlchemy for primary keys
  - Use `op.batch_alter_table()` for column alterations on SQL Server
  - Boolean columns: use `sa.BIT` not `sa.Boolean` for SQL Server compatibility
  - Avoid column renames in a single migration — drop + add is safer

  ## Output Format

  Provide:
  1. The exact `alembic revision` command to run
  2. Expected upgrade() content (what it should do)
  3. Expected downgrade() content (what it should undo)
  4. Risk notes (data loss potential, lock risk, rollback complexity)
  5. The `alembic upgrade head` command to apply
