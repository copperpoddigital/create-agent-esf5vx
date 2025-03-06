"""
Database session management module that configures SQLAlchemy engine and session factories
for the Document Management and AI Chatbot System.

This module provides both synchronous and asynchronous database connection handling with
proper connection pooling, session management, and transaction control.
"""

import logging
import contextlib
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session  # SQLAlchemy 2.0.0+
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # SQLAlchemy 2.0.0+
from sqlalchemy.ext.asyncio import async_sessionmaker  # SQLAlchemy 2.0.0+

from ..core.config import db_settings

# Set up module logger
logger = logging.getLogger(__name__)

# Create synchronous SQLAlchemy engine with connection pooling
logger.info("Initializing synchronous database engine with connection pooling")
engine = create_engine(
    db_settings.SQLALCHEMY_DATABASE_URI,
    pool_size=db_settings.POOL_SIZE,
    max_overflow=db_settings.MAX_OVERFLOW,
    pool_timeout=db_settings.POOL_TIMEOUT,
    echo=db_settings.ECHO_SQL
)

# Create synchronous session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create asynchronous SQLAlchemy engine with connection pooling
logger.info("Initializing asynchronous database engine with connection pooling")
async_engine = create_async_engine(
    db_settings.SQLALCHEMY_DATABASE_URI.replace('postgresql://', 'postgresql+asyncpg://'),
    pool_size=db_settings.POOL_SIZE,
    max_overflow=db_settings.MAX_OVERFLOW,
    pool_timeout=db_settings.POOL_TIMEOUT,
    echo=db_settings.ECHO_SQL
)

# Create asynchronous session factory
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


@contextlib.contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session and ensures proper cleanup.
    
    Use this function with the `with` statement to ensure that the session
    is properly closed and that any exceptions are properly handled.
    
    Yields:
        Session: Database session that will be automatically closed
    
    Example:
        with get_db() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        logger.debug("Creating new database session")
        yield db
    except Exception as e:
        logger.exception("Exception occurred during database session usage: %s", str(e))
        db.rollback()
        raise
    finally:
        logger.debug("Closing database session")
        db.close()


@contextlib.asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that provides an async database session and ensures proper cleanup.
    
    Use this function with the `async with` statement to ensure that the session
    is properly closed and that any exceptions are properly handled.
    
    Yields:
        AsyncSession: Async database session that will be automatically closed
    
    Example:
        async with get_async_db() as db:
            result = await db.execute(select(Model))
    """
    db = AsyncSessionLocal()
    try:
        logger.debug("Creating new async database session")
        yield db
    except Exception as e:
        logger.exception("Exception occurred during async database session usage: %s", str(e))
        await db.rollback()
        raise
    finally:
        logger.debug("Closing async database session")
        await db.close()


def get_db_dependency() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session for route handlers.
    
    This function is designed to be used as a FastAPI dependency to inject
    a database session into route handlers.
    
    Yields:
        Session: Database session for dependency injection
    
    Example:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db_dependency)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        logger.debug("Creating new database session for dependency")
        yield db
    finally:
        logger.debug("Closing database session from dependency")
        db.close()


async def get_async_db_dependency() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session for async route handlers.
    
    This function is designed to be used as a FastAPI dependency to inject
    an async database session into async route handlers.
    
    Yields:
        AsyncSession: Async database session for dependency injection
    
    Example:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_async_db_dependency)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    db = AsyncSessionLocal()
    try:
        logger.debug("Creating new async database session for dependency")
        yield db
    finally:
        logger.debug("Closing async database session from dependency")
        await db.close()