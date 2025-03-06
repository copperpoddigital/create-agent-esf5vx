import logging
from uuid import UUID
from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CRUDBase
from ..models.document_chunk import DocumentChunk
from ..schemas.document_chunk import DocumentChunkCreate, DocumentChunkUpdate
from ..utils.vector_utils import generate_embedding_id

# Set up module logger
logger = logging.getLogger(__name__)

class CRUDDocumentChunk(CRUDBase[DocumentChunk, DocumentChunkCreate, DocumentChunkUpdate]):
    """
    CRUD operations for document chunks. Extends the base CRUD class with specific functionality
    for document chunk management, including methods for retrieving chunks by document ID,
    updating embedding IDs, and batch operations.
    """

    def __init__(self):
        """Initialize the document chunk CRUD operations with the DocumentChunk model"""
        super().__init__(DocumentChunk)
    
    def get_by_document_id(
        self, db: Session, document_id: UUID
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a specific document
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            List of document chunks belonging to the document
        """
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_document_id_async(
        self, db: AsyncSession, document_id: UUID
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a specific document asynchronously
        
        Args:
            db: Async database session
            document_id: Document ID
            
        Returns:
            List of document chunks belonging to the document
        """
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    def get_by_embedding_id(
        self, db: Session, embedding_id: str
    ) -> Optional[DocumentChunk]:
        """
        Get a document chunk by its embedding ID
        
        Args:
            db: Database session
            embedding_id: Embedding ID
            
        Returns:
            The document chunk with the specified embedding ID or None if not found
        """
        stmt = select(DocumentChunk).where(DocumentChunk.embedding_id == embedding_id)
        result = db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_embedding_id_async(
        self, db: AsyncSession, embedding_id: str
    ) -> Optional[DocumentChunk]:
        """
        Get a document chunk by its embedding ID asynchronously
        
        Args:
            db: Async database session
            embedding_id: Embedding ID
            
        Returns:
            The document chunk with the specified embedding ID or None if not found
        """
        stmt = select(DocumentChunk).where(DocumentChunk.embedding_id == embedding_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    def update_embedding_id(
        self, db: Session, chunk_id: UUID, embedding_id: str
    ) -> Optional[DocumentChunk]:
        """
        Update the embedding ID for a document chunk
        
        Args:
            db: Database session
            chunk_id: Document chunk ID
            embedding_id: New embedding ID
            
        Returns:
            The updated document chunk or None if not found
        """
        chunk = self.get(db=db, id=chunk_id)
        if chunk:
            chunk.update_embedding_id(embedding_id)
            db.commit()
            db.refresh(chunk)
        return chunk
    
    async def update_embedding_id_async(
        self, db: AsyncSession, chunk_id: UUID, embedding_id: str
    ) -> Optional[DocumentChunk]:
        """
        Update the embedding ID for a document chunk asynchronously
        
        Args:
            db: Async database session
            chunk_id: Document chunk ID
            embedding_id: New embedding ID
            
        Returns:
            The updated document chunk or None if not found
        """
        chunk = await self.get_async(db=db, id=chunk_id)
        if chunk:
            chunk.update_embedding_id(embedding_id)
            await db.commit()
            await db.refresh(chunk)
        return chunk
    
    def create_batch(
        self, db: Session, objs_in: List[DocumentChunkCreate]
    ) -> List[DocumentChunk]:
        """
        Create multiple document chunks in a batch operation
        
        Args:
            db: Database session
            objs_in: List of document chunk creation objects
            
        Returns:
            List of created document chunks
        """
        created_chunks = []
        for obj_in in objs_in:
            chunk = self.create(db=db, obj_in=obj_in)
            created_chunks.append(chunk)
        return created_chunks
    
    async def create_batch_async(
        self, db: AsyncSession, objs_in: List[DocumentChunkCreate]
    ) -> List[DocumentChunk]:
        """
        Create multiple document chunks in a batch operation asynchronously
        
        Args:
            db: Async database session
            objs_in: List of document chunk creation objects
            
        Returns:
            List of created document chunks
        """
        created_chunks = []
        for obj_in in objs_in:
            chunk = await self.create_async(db=db, obj_in=obj_in)
            created_chunks.append(chunk)
        return created_chunks
    
    def remove_by_document_id(
        self, db: Session, document_id: UUID
    ) -> int:
        """
        Remove all chunks for a specific document
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            Number of chunks deleted
        """
        chunks = self.get_by_document_id(db=db, document_id=document_id)
        deleted_count = 0
        for chunk in chunks:
            self.remove(db=db, id=chunk.id)
            deleted_count += 1
        return deleted_count
    
    async def remove_by_document_id_async(
        self, db: AsyncSession, document_id: UUID
    ) -> int:
        """
        Remove all chunks for a specific document asynchronously
        
        Args:
            db: Async database session
            document_id: Document ID
            
        Returns:
            Number of chunks deleted
        """
        chunks = await self.get_by_document_id_async(db=db, document_id=document_id)
        deleted_count = 0
        for chunk in chunks:
            await self.remove_async(db=db, id=chunk.id)
            deleted_count += 1
        return deleted_count
    
    def get_chunks_without_embeddings(
        self, db: Session, limit: int = 100
    ) -> List[DocumentChunk]:
        """
        Get document chunks that don't have embedding IDs assigned
        
        Args:
            db: Database session
            limit: Maximum number of chunks to retrieve
            
        Returns:
            List of document chunks without embedding IDs
        """
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding_id == None)
            .limit(limit)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_chunks_without_embeddings_async(
        self, db: AsyncSession, limit: int = 100
    ) -> List[DocumentChunk]:
        """
        Get document chunks that don't have embedding IDs assigned asynchronously
        
        Args:
            db: Async database session
            limit: Maximum number of chunks to retrieve
            
        Returns:
            List of document chunks without embedding IDs
        """
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding_id == None)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    def get_chunk_by_document_and_index(
        self, db: Session, document_id: UUID, chunk_index: int
    ) -> Optional[DocumentChunk]:
        """
        Get a specific chunk by document ID and chunk index
        
        Args:
            db: Database session
            document_id: Document ID
            chunk_index: Chunk index within the document
            
        Returns:
            The document chunk with the specified document ID and index or None if not found
        """
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.chunk_index == chunk_index
        )
        result = db.execute(stmt)
        return result.scalars().first()
    
    async def get_chunk_by_document_and_index_async(
        self, db: AsyncSession, document_id: UUID, chunk_index: int
    ) -> Optional[DocumentChunk]:
        """
        Get a specific chunk by document ID and chunk index asynchronously
        
        Args:
            db: Async database session
            document_id: Document ID
            chunk_index: Chunk index within the document
            
        Returns:
            The document chunk with the specified document ID and index or None if not found
        """
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.chunk_index == chunk_index
        )
        result = await db.execute(stmt)
        return result.scalars().first()

# Create a singleton instance for usage throughout the application
document_chunk = CRUDDocumentChunk()