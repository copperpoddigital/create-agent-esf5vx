"""
Database module for the Document Management and AI Chatbot System.

This module serves as the entry point for database-related functionality,
providing access to the SQLAlchemy base class, session management, and
database initialization functions.

This centralized approach simplifies database access throughout the application
and provides a consistent interface for both synchronous and asynchronous
database operations.
"""

# Import the SQLAlchemy declarative base class
from .base_class import Base

# Import SQLAlchemy engine and session management
from .session import (
    engine,
    SessionLocal,
    async_engine,
    AsyncSessionLocal,
    get_db,
    get_async_db,
    get_db_dependency,
    get_async_db_dependency,
)

# Import database initialization functions
from .init_db import init_db, init_test_db, create_tables

# Export all imported items for easier access
__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "async_engine",
    "AsyncSessionLocal",
    "get_db",
    "get_async_db",
    "get_db_dependency",
    "get_async_db_dependency",
    "init_db",
    "init_test_db",
    "create_tables",
]