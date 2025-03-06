"""
Migrations package for the Document Management and AI Chatbot System.

This package organizes database schema migrations using Alembic and SQLAlchemy.
It provides a namespace for migration scripts and ensures proper versioning
of database schema changes.

Migration scripts are typically generated using Alembic commands:
    alembic revision --autogenerate -m "description"

Each migration script defines both upgrade and downgrade paths to ensure
that schema changes can be applied and reverted reliably.
"""

# Version of the migrations package
__version__ = "0.1.0"