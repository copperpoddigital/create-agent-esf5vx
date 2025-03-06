from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CRUDBase
from ..models.query import Query
from ..schemas.query import QueryCreate, QueryResponse, QueryFilter
from ..core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

class CRUDQuery(CRUDBase[Query, QueryCreate, QueryCreate]):
    """CRUD operations for Query model, extending the base CRUD class with query-specific functionality."""
    
    def __init__(self):
        """Initialize the CRUD operations for Query model"""
        super().__init__(Query)
    
    def create_with_response(
        self, db: Session, user_id: UUID, query_text: str, 
        response_text: str, context_documents: dict, embedding_id: Optional[str] = None
    ) -> Query:
        """
        Create a new query record with response and context documents
        
        Args:
            db: Database session
            user_id: ID of the user who made the query
            query_text: The text of the query
            response_text: The AI-generated response text
            context_documents: Dictionary containing document context used for response
            embedding_id: Optional ID of the query vector embedding in FAISS
            
        Returns:
            Created query record
        """
        query_data = {
            "user_id": user_id,
            "query_text": query_text,
            "response_text": response_text,
            "context_documents": context_documents,
            "embedding_id": embedding_id
        }
        
        query = self.create(db=db, obj_in=query_data)
        logger.info(f"Created new query record with ID: {query.id}")
        return query

    async def create_with_response_async(
        self, db: AsyncSession, user_id: UUID, query_text: str, 
        response_text: str, context_documents: dict, embedding_id: Optional[str] = None
    ) -> Query:
        """
        Asynchronously create a new query record with response and context documents
        
        Args:
            db: Async database session
            user_id: ID of the user who made the query
            query_text: The text of the query
            response_text: The AI-generated response text
            context_documents: Dictionary containing document context used for response
            embedding_id: Optional ID of the query vector embedding in FAISS
            
        Returns:
            Created query record
        """
        query_data = {
            "user_id": user_id,
            "query_text": query_text,
            "response_text": response_text,
            "context_documents": context_documents,
            "embedding_id": embedding_id
        }
        
        query = await self.create_async(db=db, obj_in=query_data)
        logger.info(f"Created new query record with ID: {query.id}")
        return query
    
    def get_by_user(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Query]:
        """
        Get queries for a specific user with pagination
        
        Args:
            db: Database session
            user_id: ID of the user whose queries to retrieve
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of queries for the user
        """
        stmt = select(Query).where(Query.user_id == user_id).order_by(Query.query_time.desc()).offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_async(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Query]:
        """
        Asynchronously get queries for a specific user with pagination
        
        Args:
            db: Async database session
            user_id: ID of the user whose queries to retrieve
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of queries for the user
        """
        stmt = select(Query).where(Query.user_id == user_id).order_by(Query.query_time.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_by_filter(self, db: Session, filter_params: QueryFilter, skip: int = 0, limit: int = 100) -> List[Query]:
        """
        Get queries based on filter criteria with pagination
        
        Args:
            db: Database session
            filter_params: Filter parameters for querying
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of filtered queries
        """
        stmt = select(Query)
        
        # Build filter conditions
        conditions = []
        
        if filter_params.user_id:
            conditions.append(Query.user_id == filter_params.user_id)
        
        if filter_params.start_date:
            conditions.append(Query.query_time >= filter_params.start_date)
        
        if filter_params.end_date:
            conditions.append(Query.query_time <= filter_params.end_date)
        
        if filter_params.search_term:
            conditions.append(Query.query_text.ilike(f"%{filter_params.search_term}%"))
        
        # Apply filters
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Query.query_time.desc()).offset(skip).limit(limit)
        
        result = db.execute(stmt)
        return result.scalars().all()

    async def get_by_filter_async(self, db: AsyncSession, filter_params: QueryFilter, skip: int = 0, limit: int = 100) -> List[Query]:
        """
        Asynchronously get queries based on filter criteria with pagination
        
        Args:
            db: Async database session
            filter_params: Filter parameters for querying
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of filtered queries
        """
        stmt = select(Query)
        
        # Build filter conditions
        conditions = []
        
        if filter_params.user_id:
            conditions.append(Query.user_id == filter_params.user_id)
        
        if filter_params.start_date:
            conditions.append(Query.query_time >= filter_params.start_date)
        
        if filter_params.end_date:
            conditions.append(Query.query_time <= filter_params.end_date)
        
        if filter_params.search_term:
            conditions.append(Query.query_text.ilike(f"%{filter_params.search_term}%"))
        
        # Apply filters
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Query.query_time.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_with_feedback(self, db: Session, query_id: UUID) -> Optional[Query]:
        """
        Get a query with its associated feedback
        
        Args:
            db: Database session
            query_id: ID of the query to retrieve
            
        Returns:
            Query with feedback or None if not found
        """
        stmt = select(Query).options(joinedload(Query.feedback)).where(Query.id == query_id)
        result = db.execute(stmt)
        return result.scalars().first()

    async def get_with_feedback_async(self, db: AsyncSession, query_id: UUID) -> Optional[Query]:
        """
        Asynchronously get a query with its associated feedback
        
        Args:
            db: Async database session
            query_id: ID of the query to retrieve
            
        Returns:
            Query with feedback or None if not found
        """
        stmt = select(Query).options(joinedload(Query.feedback)).where(Query.id == query_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    def create_from_query_response(
        self, db: Session, user_id: UUID, query_response: QueryResponse, embedding_id: Optional[str] = None
    ) -> Query:
        """
        Create a query record from a QueryResponse object
        
        Args:
            db: Database session
            user_id: ID of the user who made the query
            query_response: The QueryResponse object containing query, response, and documents
            embedding_id: Optional ID of the query vector embedding in FAISS
            
        Returns:
            Created query record
        """
        # Extract data from QueryResponse
        query_text = query_response.query_text
        response_text = query_response.response_text
        
        # Convert relevant_documents to context_documents format
        context_documents = {
            "documents": [
                {
                    "id": str(doc.document_id),
                    "chunk_index": doc.chunk_index,
                    "content": doc.content,
                    "similarity_score": doc.similarity_score
                } for doc in query_response.relevant_documents
            ]
        }
        
        # Create the query record
        return self.create_with_response(
            db=db,
            user_id=user_id,
            query_text=query_text,
            response_text=response_text,
            context_documents=context_documents,
            embedding_id=embedding_id
        )

    async def create_from_query_response_async(
        self, db: AsyncSession, user_id: UUID, query_response: QueryResponse, embedding_id: Optional[str] = None
    ) -> Query:
        """
        Asynchronously create a query record from a QueryResponse object
        
        Args:
            db: Async database session
            user_id: ID of the user who made the query
            query_response: The QueryResponse object containing query, response, and documents
            embedding_id: Optional ID of the query vector embedding in FAISS
            
        Returns:
            Created query record
        """
        # Extract data from QueryResponse
        query_text = query_response.query_text
        response_text = query_response.response_text
        
        # Convert relevant_documents to context_documents format
        context_documents = {
            "documents": [
                {
                    "id": str(doc.document_id),
                    "chunk_index": doc.chunk_index,
                    "content": doc.content,
                    "similarity_score": doc.similarity_score
                } for doc in query_response.relevant_documents
            ]
        }
        
        # Create the query record
        return await self.create_with_response_async(
            db=db,
            user_id=user_id,
            query_text=query_text,
            response_text=response_text,
            context_documents=context_documents,
            embedding_id=embedding_id
        )


# Singleton instance for use throughout the application
crud_query = CRUDQuery()