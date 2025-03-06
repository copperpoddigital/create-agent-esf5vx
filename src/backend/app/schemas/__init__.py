"""
Centralized schemas module for the Document Management and AI Chatbot System.

This module provides a clean import interface for all data validation schemas used throughout 
the application, importing and re-exporting schemas from their specific modules.
"""

# Authentication token schemas
from .token import (
    Token,
    TokenPayload,
    TokenData,
    TokenRequest,
    RefreshTokenRequest,
)

# User data schemas
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDBBase,
    UserInDB,
    User,
)

# Document data schemas
from .document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentInDBBase,
    Document,
    DocumentWithChunks,
    DocumentFilter,
)

# Document chunk data schemas
from .document_chunk import (
    DocumentChunkBase,
    DocumentChunkCreate,
    DocumentChunkUpdate,
    DocumentChunkInDBBase,
    DocumentChunk,
    DocumentChunkWithSimilarity,
)

# Query data schemas
from .query import (
    QueryBase,
    QueryCreate,
    QueryInDBBase,
    Query,
    QueryResponse,
    FeedbackSchema,
    QueryWithFeedback,
    QueryFilter,
)

# Feedback data schemas
from .feedback import (
    FeedbackBase,
    FeedbackCreate,
    FeedbackInDBBase,
    Feedback,
    FeedbackWithQuery,
    FeedbackFilter,
    FeedbackStats,
)

# Export all schemas for easy imports from other modules
__all__ = [
    # Authentication token schemas
    "Token", "TokenPayload", "TokenData", "TokenRequest", "RefreshTokenRequest",
    
    # User data schemas
    "UserBase", "UserCreate", "UserUpdate", "UserInDBBase", "UserInDB", "User",
    
    # Document data schemas
    "DocumentBase", "DocumentCreate", "DocumentUpdate", "DocumentInDBBase", 
    "Document", "DocumentWithChunks", "DocumentFilter",
    
    # Document chunk data schemas
    "DocumentChunkBase", "DocumentChunkCreate", "DocumentChunkUpdate", 
    "DocumentChunkInDBBase", "DocumentChunk", "DocumentChunkWithSimilarity",
    
    # Query data schemas
    "QueryBase", "QueryCreate", "QueryInDBBase", "Query", "QueryResponse", 
    "FeedbackSchema", "QueryWithFeedback", "QueryFilter",
    
    # Feedback data schemas
    "FeedbackBase", "FeedbackCreate", "FeedbackInDBBase", "Feedback", 
    "FeedbackWithQuery", "FeedbackFilter", "FeedbackStats",
]