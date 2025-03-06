from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional, List, Dict
from datetime import datetime

from pydantic import BaseModel, Field, validator, ConfigDict, UUID4  # version 2.0.0+

from ..models.document import DocumentStatus
from .user import User
from ..core.config import document_settings


class DocumentBase(BaseModel):
    """Base Pydantic model for document data with common attributes."""
    title: str
    filename: str
    size_bytes: int
    upload_date: Optional[datetime] = None
    status: Optional[DocumentStatus] = None
    file_path: Optional[str] = None

    @validator('title')
    def validate_title(cls, title: str) -> str:
        """
        Validates document title length and format.
        
        Args:
            title: The document title to validate
            
        Returns:
            The validated title
            
        Raises:
            ValueError: If title is empty or too long
        """
        if not title:
            raise ValueError("Document title cannot be empty")
        
        if len(title) < 3:
            raise ValueError("Document title must be at least 3 characters long")
            
        if len(title) > 255:
            raise ValueError("Document title must be at most 255 characters long")
            
        return title

    @validator('size_bytes')
    def validate_size(cls, size_bytes: int) -> int:
        """
        Validates document size against maximum allowed size.
        
        Args:
            size_bytes: The document size in bytes
            
        Returns:
            The validated size in bytes
            
        Raises:
            ValueError: If size is negative or exceeds maximum allowed size
        """
        if size_bytes <= 0:
            raise ValueError("Document size must be greater than 0")
            
        max_size_bytes = document_settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        if size_bytes > max_size_bytes:
            raise ValueError(f"Document size exceeds maximum allowed size of {document_settings.MAX_DOCUMENT_SIZE_MB}MB")
            
        return size_bytes


class DocumentCreate(DocumentBase):
    """Schema for document creation with required fields."""
    uploader_id: UUID4


class DocumentUpdate(BaseModel):
    """Schema for document updates with all fields optional."""
    title: Optional[str] = None
    status: Optional[DocumentStatus] = None


class DocumentInDBBase(DocumentBase):
    """Base schema for document data from database including ID."""
    id: UUID4
    uploader_id: UUID4
    
    model_config = ConfigDict(from_attributes=True)


class Document(DocumentInDBBase):
    """Schema for document data returned to clients."""
    uploader: Optional[User] = None


class DocumentWithChunks(Document):
    """Schema for document data including its chunks."""
    chunks: List['DocumentChunk'] = []  # Forward reference to DocumentChunk schema


class DocumentFilter(BaseModel):
    """Schema for document filtering parameters."""
    title: Optional[str] = None
    status: Optional[DocumentStatus] = None
    uploader_id: Optional[UUID4] = None
    upload_date_from: Optional[datetime] = None
    upload_date_to: Optional[datetime] = None