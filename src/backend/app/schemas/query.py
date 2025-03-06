from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, UUID4  # version 2.0.0+

from .document_chunk import DocumentChunkWithSimilarity


class QueryBase(BaseModel):
    """Base Pydantic model for query data with common attributes."""
    query_text: str


class QueryCreate(QueryBase):
    """Schema for query submission with optional search parameters."""
    max_results: Optional[int] = None
    similarity_threshold: Optional[float] = None


class QueryInDBBase(QueryBase):
    """Base schema for query data from database including ID and timestamps."""
    id: UUID4
    user_id: UUID4
    query_time: datetime
    response_text: str
    context_documents: Dict[str, Any]
    embedding_id: Optional[str] = None
    
    @classmethod
    def model_config(cls):
        return ConfigDict(from_attributes=True)


class Query(QueryInDBBase):
    """Schema for query data returned to clients."""
    
    def get_query_preview(self, max_length: int = 100) -> str:
        """
        Returns a preview of the query text.
        
        Args:
            max_length: Maximum length of the preview before truncation
            
        Returns:
            Preview of the query text
        """
        if len(self.query_text) <= max_length:
            return self.query_text
        return self.query_text[:max_length] + "..."
    
    def get_response_preview(self, max_length: int = 100) -> str:
        """
        Returns a preview of the response text.
        
        Args:
            max_length: Maximum length of the preview before truncation
            
        Returns:
            Preview of the response text
        """
        if len(self.response_text) <= max_length:
            return self.response_text
        return self.response_text[:max_length] + "..."


class QueryResponse(BaseModel):
    """Schema for query response with AI-generated answer and relevant documents."""
    query_id: UUID4
    query_text: str
    response_text: str
    relevant_documents: List[DocumentChunkWithSimilarity]


class FeedbackSchema(BaseModel):
    """Simple schema for feedback data used within the query module."""
    rating: int
    comments: Optional[str] = None
    
    @classmethod
    def model_config(cls):
        return ConfigDict(from_attributes=True)


class QueryWithFeedback(Query):
    """Schema for query data including associated feedback."""
    feedback: List[FeedbackSchema] = []


class QueryFilter(BaseModel):
    """Schema for filtering query data."""
    user_id: Optional[UUID4] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_term: Optional[str] = None