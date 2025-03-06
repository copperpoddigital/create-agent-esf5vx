"""
API module implementing query and vector search endpoints for the Document Management and AI Chatbot System.

This module provides endpoints to submit search queries, retrieve query results, and 
manage query history. It implements the vector search workflow for processing 
queries and generating AI responses based on document content.
"""

from typing import List, Optional  # standard library
from uuid import UUID  # standard library
import logging  # standard library

from fastapi import APIRouter, Depends, HTTPException, status, Query as QueryParam, Path  # version 0.95.0+
from sqlalchemy.orm import Session  # SQLAlchemy 2.0.0+

from ....api.dependencies import (
    get_db_dependency,
    get_current_user,
    get_optional_current_user,
)
from ....schemas.query import (
    QueryCreate,
    QueryResponse,
    Query,
    QueryFilter,
    QueryWithFeedback,
)
from ....crud.crud_query import crud_query
from ....services.vector_search import VectorSearchService
from ....services.llm_service import LLMService
from ....models.user import User

# Create router for query endpoints
router = APIRouter(prefix="/query", tags=["query"])

# Set up logger
logger = logging.getLogger(__name__)

# Initialize services
vector_search_service = VectorSearchService()
llm_service = LLMService()

@router.post("/", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def submit_query(
    query_data: QueryCreate,
    db: Session = Depends(get_db_dependency),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> QueryResponse:
    """
    Endpoint to submit a search query and receive AI-generated response with relevant documents.
    
    Args:
        query_data: Query data containing the query text and optional parameters
        db: Database session
        current_user: Current authenticated user or None if anonymous
        
    Returns:
        QueryResponse: AI-generated response with relevant documents
    """
    logger.info(f"Submitting query: {query_data.query_text}")
    
    # Validate query text is not empty
    if not query_data.query_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text cannot be empty",
        )
    
    # Get search parameters from request or use defaults
    max_results = query_data.max_results
    similarity_threshold = query_data.similarity_threshold
    
    # Perform vector search
    search_results = vector_search_service.search(
        query_text=query_data.query_text,
        db=db,
        top_k=max_results,
        threshold=similarity_threshold,
    )
    
    # Generate AI response based on search results
    query_response = llm_service.create_query_response(
        query_text=query_data.query_text,
        relevant_documents=search_results,
    )
    
    # Store query and response in database if user is authenticated
    if current_user:
        crud_query.create_from_query_response(
            db=db,
            user_id=current_user.id,
            query_response=query_response,
        )
    
    return query_response

@router.get("/{query_id}", response_model=Query, status_code=status.HTTP_200_OK)
def get_query(
    query_id: UUID = Path(..., description="ID of the query to retrieve"),
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
) -> Query:
    """
    Endpoint to retrieve a specific query by ID.
    
    Args:
        query_id: ID of the query to retrieve
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Query: Query data including response
    """
    # Retrieve query from database
    query = crud_query.get(db=db, id=query_id)
    
    # Check if query exists
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found",
        )
    
    # Check if user has permission to access this query
    if str(query.user_id) != str(current_user.id) and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this query",
        )
    
    return query

@router.get("/{query_id}/feedback", response_model=QueryWithFeedback, status_code=status.HTTP_200_OK)
def get_query_with_feedback(
    query_id: UUID = Path(..., description="ID of the query to retrieve with feedback"),
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
) -> QueryWithFeedback:
    """
    Endpoint to retrieve a specific query with its feedback.
    
    Args:
        query_id: ID of the query to retrieve
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        QueryWithFeedback: Query data including feedback
    """
    # Retrieve query with feedback from database
    query = crud_query.get_with_feedback(db=db, query_id=query_id)
    
    # Check if query exists
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found",
        )
    
    # Check if user has permission to access this query
    if str(query.user_id) != str(current_user.id) and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this query",
        )
    
    return query

@router.get("/", response_model=List[Query], status_code=status.HTTP_200_OK)
def list_queries(
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
    skip: int = QueryParam(0, description="Number of records to skip"),
    limit: int = QueryParam(100, description="Maximum number of records to return"),
    search_term: Optional[str] = QueryParam(None, description="Search term to filter queries by content"),
) -> List[Query]:
    """
    Endpoint to list queries with pagination and filtering.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        skip: Number of records to skip
        limit: Maximum number of records to return
        search_term: Optional search term to filter queries by content
        
    Returns:
        List[Query]: List of queries matching filter criteria
    """
    # Create filter with user_id (only admins can see all queries)
    filter_params = QueryFilter(
        user_id=None if current_user.is_admin() else current_user.id,
        search_term=search_term,
    )
    
    # Retrieve queries from database
    queries = crud_query.get_by_filter(
        db=db,
        filter_params=filter_params,
        skip=skip,
        limit=limit,
    )
    
    return queries

@router.get("/me", response_model=List[Query], status_code=status.HTTP_200_OK)
def list_user_queries(
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
    skip: int = QueryParam(0, description="Number of records to skip"),
    limit: int = QueryParam(100, description="Maximum number of records to return"),
) -> List[Query]:
    """
    Endpoint to list queries for the current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[Query]: List of user's queries
    """
    # Retrieve user's queries from database
    queries = crud_query.get_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    
    return queries