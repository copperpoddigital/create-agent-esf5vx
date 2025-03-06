from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, UUID4  # version 2.0.0+

from .document import Document


class DocumentChunkBase(BaseModel):
    """Base Pydantic model for document chunk data with common attributes."""
    document_id: UUID4
    chunk_index: int
    content: str
    token_count: int
    embedding_id: Optional[str] = None


class DocumentChunkCreate(DocumentChunkBase):
    """Schema for document chunk creation with required fields."""
    pass


class DocumentChunkUpdate(BaseModel):
    """Schema for document chunk updates with all fields optional."""
    content: Optional[str] = None
    token_count: Optional[int] = None
    embedding_id: Optional[str] = None


class DocumentChunkInDBBase(DocumentChunkBase):
    """Base schema for document chunk data from database including ID."""
    id: UUID4
    
    model_config = ConfigDict(from_attributes=True)


class DocumentChunk(DocumentChunkInDBBase):
    """Schema for document chunk data returned to clients."""
    document: Optional[Document] = None

    def get_content_preview(self, max_length: int = 100) -> str:
        """
        Returns a preview of the chunk content.
        
        Args:
            max_length: Maximum length of the preview before truncation
            
        Returns:
            A truncated version of the content with ellipsis if longer than max_length
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."


class DocumentChunkWithSimilarity(DocumentChunk):
    """Schema for document chunk with similarity score for search results."""
    similarity_score: float