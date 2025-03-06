"""
Implements API endpoints for user feedback on AI-generated responses in the Document Management and AI Chatbot System.
This module provides routes for submitting feedback, retrieving feedback data, and triggering reinforcement learning
based on accumulated feedback.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.dependencies import (
    get_current_active_user,
    get_db_dependency,
    get_async_db_dependency,
    require_role,
)
from ....schemas.feedback import (
    FeedbackCreate,
    Feedback,
    FeedbackFilter,
    FeedbackStats,
)
from ....crud.crud_feedback import feedback
from ....services.feedback_processor import process_feedback_batch
from ....core.logging import get_logger
from ....models.user import User

# Set up router and logger
router = APIRouter()
logger = get_logger(__name__)

@router.post("/", response_model=Feedback, status_code=status.HTTP_201_CREATED)
@router.post("/submit", response_model=Feedback, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_dependency),
) -> Feedback:
    """
    Submit feedback for a specific query response.
    
    Args:
        feedback_in: Feedback creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created feedback record
    """
    logger.info(f"User {current_user.id} submitting feedback for query {feedback_in.query_id}")
    try:
        # Create feedback with user association
        feedback_record = feedback.create_with_user(
            db=db,
            user_id=current_user.id,
            obj_in=feedback_in
        )
        return feedback_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@router.post("/async", response_model=Feedback, status_code=status.HTTP_201_CREATED)
async def submit_feedback_async(
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db_dependency),
) -> Feedback:
    """
    Submit feedback for a specific query response (async version).
    
    Args:
        feedback_in: Feedback creation data
        current_user: Current authenticated user
        db: Async database session
        
    Returns:
        Created feedback record
    """
    logger.info(f"User {current_user.id} submitting feedback asynchronously for query {feedback_in.query_id}")
    try:
        # Create feedback with user association asynchronously
        feedback_record = await feedback.create_with_user_async(
            db=db,
            user_id=current_user.id,
            obj_in=feedback_in
        )
        return feedback_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback asynchronously: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )

@router.get("/{feedback_id}", response_model=Feedback)
def get_feedback(
    feedback_id: UUID = Path(..., description="The ID of the feedback to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_dependency),
) -> Feedback:
    """
    Get feedback by ID.
    
    Args:
        feedback_id: UUID of the feedback to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feedback record if found
    """
    try:
        # Retrieve feedback
        feedback_record = feedback.get(db=db, id=feedback_id)
        if not feedback_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Check if user has permission to access this feedback
        # Users can only see their own feedback unless they're admins
        if feedback_record.user_id != current_user.id and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this feedback"
            )
        
        return feedback_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback {feedback_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )

@router.get("/query/{query_id}", response_model=List[Feedback])
def get_feedback_by_query(
    query_id: UUID = Path(..., description="The ID of the query"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_dependency),
) -> List[Feedback]:
    """
    Get all feedback for a specific query.
    
    Args:
        query_id: UUID of the query
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of feedback for the query
    """
    try:
        # First, check if the query exists and if the user has permission to access it
        from ....crud.crud_query import crud_query
        query = crud_query.get(db=db, id=query_id)
        
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )
        
        # For non-admin users, check if they own the query
        if not current_user.is_admin() and query.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access feedback for this query"
            )
        
        # Get all feedback for the query
        feedback_records = feedback.get_by_query(db=db, query_id=query_id)
        
        return feedback_records
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback for query {query_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )

@router.get("/user/me", response_model=List[Feedback])
def get_user_feedback(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_dependency),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> List[Feedback]:
    """
    Get all feedback submitted by the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        List of feedback submitted by the user
    """
    try:
        feedback_records = feedback.get_by_user(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        return feedback_records
    except Exception as e:
        logger.error(f"Error retrieving user feedback for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user feedback"
        )

@router.post("/filter", response_model=List[Feedback])
def get_filtered_feedback(
    filter_params: FeedbackFilter,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_dependency),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> List[Feedback]:
    """
    Get feedback based on filter criteria.
    
    Args:
        filter_params: Filter parameters
        current_user: Current authenticated user
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        List of filtered feedback
    """
    try:
        # For non-admin users, restrict to viewing their own feedback
        if not current_user.is_admin():
            # Force user_id filter to current user
            filter_params.user_id = current_user.id
        
        feedback_records = feedback.get_filtered(
            db=db,
            filter_params=filter_params,
            skip=skip,
            limit=limit
        )
        return feedback_records
    except Exception as e:
        logger.error(f"Error retrieving filtered feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve filtered feedback"
        )

@router.post("/statistics", response_model=FeedbackStats)
def get_feedback_statistics(
    filter_params: Optional[FeedbackFilter] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_dependency),
) -> FeedbackStats:
    """
    Get statistics for feedback based on filter criteria.
    
    Args:
        filter_params: Optional filter parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feedback statistics
    """
    try:
        # For non-admin users, restrict to statistics for their own feedback
        if not current_user.is_admin():
            if filter_params is None:
                filter_params = FeedbackFilter()
            # Force user_id filter to current user
            filter_params.user_id = current_user.id
        
        statistics = feedback.get_statistics(db=db, filter_params=filter_params)
        return statistics
    except Exception as e:
        logger.error(f"Error retrieving feedback statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback statistics"
        )

@router.post("/reinforce", response_model=dict)
@router.post("/reinforcement-learning", response_model=dict)
def trigger_reinforcement_learning(
    current_user: User = Depends(require_role(["admin"])),
) -> dict:
    """
    Trigger reinforcement learning based on accumulated feedback.
    
    This endpoint requires admin role.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Status of reinforcement learning process
    """
    logger.info(f"Admin user {current_user.id} triggering reinforcement learning process")
    
    try:
        # Process feedback batch
        success = process_feedback_batch()
        
        if success:
            return {
                "status": "success",
                "message": "Reinforcement learning process completed successfully"
            }
        else:
            return {
                "status": "skipped",
                "message": "Reinforcement learning process skipped (insufficient data or too soon after previous update)"
            }
    except Exception as e:
        logger.error(f"Error in reinforcement learning process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete reinforcement learning process"
        )