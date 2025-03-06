from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CRUDBase
from ..models.document import Document, DocumentStatus
from ..schemas.document import DocumentCreate, DocumentUpdate, DocumentFilter

logger = logging.getLogger(__name__)

class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    """
    CRUD operations for Document entities, extending the generic CRUDBase class with 
    document-specific functionality.
    """
    
    def __init__(self):
        """Initialize the CRUD operations for Document model"""
        super().__init__(Document)
    
    def get_by_title(self, db: Session, title: str) -> Optional[Document]:
        """
        Get a document by its title
        
        Args:
            db: Database session
            title: Title of the document to search for
            
        Returns:
            Document with the specified title or None if not found
        """
        try:
            stmt = select(self.model).where(self.model.title == title)
            result = db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting document by title: {str(e)}")
            raise
    
    def get_by_uploader(self, db: Session, uploader_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents uploaded by a specific user
        
        Args:
            db: Database session
            uploader_id: UUID of the uploader
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents uploaded by the specified user
        """
        try:
            stmt = select(self.model).where(self.model.uploader_id == uploader_id).offset(skip).limit(limit)
            result = db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting documents by uploader: {str(e)}")
            raise
    
    def get_by_status(self, db: Session, status: DocumentStatus, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents with a specific status
        
        Args:
            db: Database session
            status: Status of the documents to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents with the specified status
        """
        try:
            stmt = select(self.model).where(self.model.status == status).offset(skip).limit(limit)
            result = db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting documents by status: {str(e)}")
            raise
    
    def update_status(self, db: Session, document: Document, status: DocumentStatus) -> Document:
        """
        Update the status of a document
        
        Args:
            db: Database session
            document: Document to update
            status: New status to set
            
        Returns:
            Updated document
        """
        try:
            document.update_status(status)
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating document status: {str(e)}")
            raise
    
    def get_multi_with_filter(
        self, db: Session, filter_params: Optional[DocumentFilter] = None, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get multiple documents with filtering options
        
        Args:
            db: Database session
            filter_params: Optional filter criteria
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents matching the filter criteria
        """
        try:
            stmt = select(self.model)
            
            if filter_params:
                if filter_params.title:
                    stmt = stmt.where(self.model.title.ilike(f'%{filter_params.title}%'))
                
                if filter_params.status:
                    stmt = stmt.where(self.model.status == filter_params.status)
                    
                if filter_params.uploader_id:
                    stmt = stmt.where(self.model.uploader_id == filter_params.uploader_id)
                    
                if filter_params.upload_date_from:
                    stmt = stmt.where(self.model.upload_date >= filter_params.upload_date_from)
                    
                if filter_params.upload_date_to:
                    stmt = stmt.where(self.model.upload_date <= filter_params.upload_date_to)
            
            stmt = stmt.offset(skip).limit(limit)
            result = db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting documents with filter: {str(e)}")
            raise
    
    def count_with_filter(self, db: Session, filter_params: Optional[DocumentFilter] = None) -> int:
        """
        Count documents matching filter criteria
        
        Args:
            db: Database session
            filter_params: Optional filter criteria
            
        Returns:
            Count of documents matching the filter criteria
        """
        try:
            stmt = select(func.count()).select_from(self.model)
            
            if filter_params:
                if filter_params.title:
                    stmt = stmt.where(self.model.title.ilike(f'%{filter_params.title}%'))
                
                if filter_params.status:
                    stmt = stmt.where(self.model.status == filter_params.status)
                    
                if filter_params.uploader_id:
                    stmt = stmt.where(self.model.uploader_id == filter_params.uploader_id)
                    
                if filter_params.upload_date_from:
                    stmt = stmt.where(self.model.upload_date >= filter_params.upload_date_from)
                    
                if filter_params.upload_date_to:
                    stmt = stmt.where(self.model.upload_date <= filter_params.upload_date_to)
            
            result = db.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting documents with filter: {str(e)}")
            raise
    
    def soft_delete(self, db: Session, id: UUID) -> Optional[Document]:
        """
        Mark a document as deleted without removing it from the database
        
        Args:
            db: Database session
            id: UUID of the document to soft delete
            
        Returns:
            The soft-deleted document or None if not found
        """
        try:
            document = self.get(db=db, id=id)
            if document:
                document.update_status(DocumentStatus.deleted)
                db.add(document)
                db.commit()
                db.refresh(document)
            return document
        except Exception as e:
            db.rollback()
            logger.error(f"Error soft deleting document: {str(e)}")
            raise
    
    # Asynchronous methods
    async def get_by_title_async(self, db: AsyncSession, title: str) -> Optional[Document]:
        """
        Get a document by its title asynchronously
        
        Args:
            db: Async database session
            title: Title of the document to search for
            
        Returns:
            Document with the specified title or None if not found
        """
        try:
            stmt = select(self.model).where(self.model.title == title)
            result = await db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting document by title asynchronously: {str(e)}")
            raise
    
    async def get_by_uploader_async(self, db: AsyncSession, uploader_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents uploaded by a specific user asynchronously
        
        Args:
            db: Async database session
            uploader_id: UUID of the uploader
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents uploaded by the specified user
        """
        try:
            stmt = select(self.model).where(self.model.uploader_id == uploader_id).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting documents by uploader asynchronously: {str(e)}")
            raise
    
    async def get_by_status_async(self, db: AsyncSession, status: DocumentStatus, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents with a specific status asynchronously
        
        Args:
            db: Async database session
            status: Status of the documents to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents with the specified status
        """
        try:
            stmt = select(self.model).where(self.model.status == status).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting documents by status asynchronously: {str(e)}")
            raise
    
    async def update_status_async(self, db: AsyncSession, document: Document, status: DocumentStatus) -> Document:
        """
        Update the status of a document asynchronously
        
        Args:
            db: Async database session
            document: Document to update
            status: New status to set
            
        Returns:
            Updated document
        """
        try:
            document.update_status(status)
            db.add(document)
            await db.commit()
            await db.refresh(document)
            return document
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating document status asynchronously: {str(e)}")
            raise
    
    async def get_multi_with_filter_async(
        self, db: AsyncSession, filter_params: Optional[DocumentFilter] = None, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get multiple documents with filtering options asynchronously
        
        Args:
            db: Async database session
            filter_params: Optional filter criteria
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of documents matching the filter criteria
        """
        try:
            stmt = select(self.model)
            
            if filter_params:
                if filter_params.title:
                    stmt = stmt.where(self.model.title.ilike(f'%{filter_params.title}%'))
                
                if filter_params.status:
                    stmt = stmt.where(self.model.status == filter_params.status)
                    
                if filter_params.uploader_id:
                    stmt = stmt.where(self.model.uploader_id == filter_params.uploader_id)
                    
                if filter_params.upload_date_from:
                    stmt = stmt.where(self.model.upload_date >= filter_params.upload_date_from)
                    
                if filter_params.upload_date_to:
                    stmt = stmt.where(self.model.upload_date <= filter_params.upload_date_to)
            
            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting documents with filter asynchronously: {str(e)}")
            raise
    
    async def count_with_filter_async(self, db: AsyncSession, filter_params: Optional[DocumentFilter] = None) -> int:
        """
        Count documents matching filter criteria asynchronously
        
        Args:
            db: Async database session
            filter_params: Optional filter criteria
            
        Returns:
            Count of documents matching the filter criteria
        """
        try:
            stmt = select(func.count()).select_from(self.model)
            
            if filter_params:
                if filter_params.title:
                    stmt = stmt.where(self.model.title.ilike(f'%{filter_params.title}%'))
                
                if filter_params.status:
                    stmt = stmt.where(self.model.status == filter_params.status)
                    
                if filter_params.uploader_id:
                    stmt = stmt.where(self.model.uploader_id == filter_params.uploader_id)
                    
                if filter_params.upload_date_from:
                    stmt = stmt.where(self.model.upload_date >= filter_params.upload_date_from)
                    
                if filter_params.upload_date_to:
                    stmt = stmt.where(self.model.upload_date <= filter_params.upload_date_to)
            
            result = await db.execute(stmt)
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting documents with filter asynchronously: {str(e)}")
            raise
    
    async def soft_delete_async(self, db: AsyncSession, id: UUID) -> Optional[Document]:
        """
        Mark a document as deleted without removing it from the database asynchronously
        
        Args:
            db: Async database session
            id: UUID of the document to soft delete
            
        Returns:
            The soft-deleted document or None if not found
        """
        try:
            document = await self.get_async(db=db, id=id)
            if document:
                document.update_status(DocumentStatus.deleted)
                db.add(document)
                await db.commit()
                await db.refresh(document)
            return document
        except Exception as e:
            await db.rollback()
            logger.error(f"Error soft deleting document asynchronously: {str(e)}")
            raise


# Create instance for export
document = CRUDDocument()