"""
Central import file for SQLAlchemy ORM models.

This file serves as a single import point for all database models in the
Document Management and AI Chatbot System. By importing all models here,
we prevent circular import issues and provide a centralized location for
database initialization, migrations, and other database operations.

This approach is especially useful for Alembic migrations, as it ensures
all models are discovered and included in auto-generated migrations.
"""

# Import the declarative base class
from .base_class import Base

# Import all models to ensure they are registered with the declarative base
from ..models.user import User
from ..models.document import Document
from ..models.document_chunk import DocumentChunk
from ..models.query import Query
from ..models.feedback import Feedback

# This file is used by Alembic for migrations and other database operations
# It provides a centralized import point to avoid circular import issues
# All models should be imported here to ensure they're properly registered