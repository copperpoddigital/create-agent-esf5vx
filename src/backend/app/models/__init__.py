"""
Initialization file for the models package that exports all SQLAlchemy ORM models
for the Document Management and AI Chatbot System.

This module serves several important purposes:
1. Prevents circular imports by centralizing model imports in a single location
2. Provides a convenient way to import all models from a single import statement
3. Creates a clear API boundary for the models package

By importing models from this module (e.g., `from app.models import User`),
application code avoids direct dependencies on individual model files, making
the codebase more maintainable and reducing the risk of circular imports.
"""

# Import User model and related enums
from .user import User, UserRole

# Import Document model and related enums
from .document import Document, DocumentStatus

# Import DocumentChunk model
from .document_chunk import DocumentChunk

# Import Query model
from .query import Query

# Import Feedback model
from .feedback import Feedback

# Explicit exports (these are automatically exported, but listing them makes
# available exports explicit to developers)
__all__ = [
    "User", 
    "UserRole",
    "Document", 
    "DocumentStatus",
    "DocumentChunk",
    "Query",
    "Feedback"
]