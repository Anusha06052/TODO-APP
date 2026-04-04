import logging # Standard library logging for debug and error messages
from collections.abc import AsyncGenerator # For type hinting the async generator returned by get_db()

from pydantic import ValidationError # For catching errors when constructing the database URL from settings
from sqlalchemy.ext.asyncio import ( 
    AsyncSession, # AsyncSession class for managing database sessions in an async context
    async_sessionmaker, # Factory for creating async sessions
    create_async_engine, # Function to create an async engine
) # SQLAlchemy async components for database connection and session management

from app.config import get_settings # Function to retrieve application settings, including database configuration

logger = logging.getLogger(__name__) # Logger for this module, used to log warnings and errors related to database configuration

try:
    _settings = get_settings() # Retrieve application settings, which includes database connection parameters
    _database_url: str = _settings.database_url # Construct the database URL from settings; this may raise a ValidationError if required settings are missing
except ValidationError as exc: # Log a warning if the database URL cannot be constructed due to missing environment variables, and re-raise the exception to prevent the application from starting with an invalid configuration
    logger.warning(
        "DATABASE_URL could not be constructed — one or more required environment "
        "variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) are not set. "
        "Check your .env file.\n%s",
        exc,
    ) # Log the specific validation error for debugging purposes
    raise # Re-raise the exception to prevent the application from starting with an invalid database configuration

engine = create_async_engine(
    _database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
) # Create an async engine with connection pooling and pre-ping enabled

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
) # Create an async session factory bound to the engine


async def get_db() -> AsyncGenerator[AsyncSession, None]: # Async generator function that yields a database session for use in FastAPI endpoints, ensuring proper cleanup after the request is processed
    """Yield an async database session for use with FastAPI Depends().

    Opens a new :class:`AsyncSession` for the duration of a single request
    and guarantees the session is returned to the connection pool in a
    ``finally`` block, regardless of whether the handler raises an exception.

    This function is intended to be used exclusively as a FastAPI dependency::

        async def my_endpoint(
            db: Annotated[AsyncSession, Depends(get_db)],
        ) -> ...:
            ...

    Yields:
        AsyncSession: An active SQLAlchemy async session bound to the
            application connection pool.

    Raises:
        SQLAlchemyError: Any database-level error is propagated to the caller
            so FastAPI's exception handlers can translate it into an appropriate
            HTTP response.
    """
    session: AsyncSession = async_session() # Create a new async session for the request; this may raise SQLAlchemyError if the database connection fails
    try:
        yield session # Yield the session to the caller (e.g., a FastAPI endpoint) for use in database operations; control will return to this function after the request is processed, allowing for cleanup in the finally block
    finally:
        await session.close() # Ensure the session is closed and returned to the connection pool, even if an error occurred during request processing
