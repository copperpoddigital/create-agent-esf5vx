"""
CRUD module for the Document Management and AI Chatbot System.

This module initializes and exports CRUD (Create, Read, Update, Delete) operation classes 
and instances for the Document Management and AI Chatbot System. This module serves as the 
central access point for database operations across the application, providing a clean interface 
to interact with different entity models.

The module follows a consistent pattern where each entity has:
1. A specialized CRUD class extending the base CRUDBase class
2. A singleton instance of that class for application-wide use

This approach ensures consistent data access patterns while providing entity-specific
operations where needed. Both synchronous and asynchronous database operations are
supported throughout the CRUD implementations.
"""

# Import the base CRUD class for type hints and exports
from .base import CRUDBase

# Import User CRUD operations
from .crud_user import CRUDUser, user

# Import Document CRUD operations
from .crud_document import CRUDDocument, document

# Import DocumentChunk CRUD operations
from .crud_document_chunk import CRUDDocumentChunk, document_chunk

# Import Query CRUD operations
from .crud_query import CRUDQuery, crud_query

# Import Feedback CRUD operations
from .crud_feedback import CRUDFeedback, feedback

# Export all CRUD classes and instances for use throughout the application
__all__ = [
    # Base class
    "CRUDBase",
    
    # User operations
    "CRUDUser",
    "user",
    
    # Document operations
    "CRUDDocument",
    "document",
    
    # Document chunk operations
    "CRUDDocumentChunk",
    "document_chunk",
    
    # Query operations
    "CRUDQuery",
    "crud_query",
    
    # Feedback operations
    "CRUDFeedback",
    "feedback",
]