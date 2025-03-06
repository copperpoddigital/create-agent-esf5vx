from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_, or_, between
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from .base import CRUDBase
from ..models.feedback import Feedback
from ..models.query import Query
from ..schemas.feedback import FeedbackCreate, FeedbackFilter, FeedbackStats
from .crud_query import crud_query
from ..core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

class CRUDFeedback(CRUDBase[Feedback, FeedbackCreate, FeedbackCreate]):
    """CRUD operations for Feedback model, extending the base CRUD class with feedback-specific functionality."""
    
    def __init__(self):
        """Initialize the CRUD operations for Feedback model"""
        super().__init__(Feedback)
    
    def create_with_user(self, db: Session, user_id: UUID, obj_in: FeedbackCreate) -> Feedback:
        """
        Create a new feedback record with user association
        
        Args:
            db: Database session
            user_id: ID of the user providing feedback
            obj_in: Feedback data for creation
            
        Returns:
            Created feedback record
            
        Raises:
            HTTPException: If the query does not exist
        """
        # Verify query exists
        query = crud_query.get(db=db, id=obj_in.query_id)
        if not query:
            logger.error(f"Attempted to create feedback for non-existent query: {obj_in.query_id}")
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Create feedback data with user ID
        feedback_data = {
            "user_id": user_id,
            "query_id": obj_in.query_id,
            "rating": obj_in.rating,
            "comments": obj_in.comments
        }
        
        # Create feedback record
        feedback = super().create(db=db, obj_in=feedback_data)
        logger.info(f"Created feedback with ID: {feedback.id} for query: {obj_in.query_id}")
        return feedback
    
    async def create_with_user_async(self, db: AsyncSession, user_id: UUID, obj_in: FeedbackCreate) -> Feedback:
        """
        Asynchronously create a new feedback record with user association
        
        Args:
            db: Async database session
            user_id: ID of the user providing feedback
            obj_in: Feedback data for creation
            
        Returns:
            Created feedback record
            
        Raises:
            HTTPException: If the query does not exist
        """
        # Verify query exists
        query = await crud_query.get_async(db=db, id=obj_in.query_id)
        if not query:
            logger.error(f"Attempted to create feedback for non-existent query: {obj_in.query_id}")
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Create feedback data with user ID
        feedback_data = {
            "user_id": user_id,
            "query_id": obj_in.query_id,
            "rating": obj_in.rating,
            "comments": obj_in.comments
        }
        
        # Create feedback record
        feedback = await super().create_async(db=db, obj_in=feedback_data)
        logger.info(f"Created feedback with ID: {feedback.id} for query: {obj_in.query_id}")
        return feedback
    
    def get_by_query(self, db: Session, query_id: UUID) -> List[Feedback]:
        """
        Get all feedback for a specific query
        
        Args:
            db: Database session
            query_id: ID of the query
            
        Returns:
            List of feedback for the query
        """
        stmt = select(Feedback).where(Feedback.query_id == query_id).order_by(Feedback.feedback_time.desc())
        result = db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_query_async(self, db: AsyncSession, query_id: UUID) -> List[Feedback]:
        """
        Asynchronously get all feedback for a specific query
        
        Args:
            db: Async database session
            query_id: ID of the query
            
        Returns:
            List of feedback for the query
        """
        stmt = select(Feedback).where(Feedback.query_id == query_id).order_by(Feedback.feedback_time.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_by_user(self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Get all feedback submitted by a specific user with pagination
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of feedback submitted by the user
        """
        stmt = select(Feedback).where(Feedback.user_id == user_id).order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_user_async(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Asynchronously get all feedback submitted by a specific user with pagination
        
        Args:
            db: Async database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of feedback submitted by the user
        """
        stmt = select(Feedback).where(Feedback.user_id == user_id).order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_filtered(self, db: Session, filter_params: FeedbackFilter, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Get feedback based on filter criteria with pagination
        
        Args:
            db: Database session
            filter_params: Filter parameters for querying
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of filtered feedback
        """
        stmt = select(Feedback)
        
        # Build filter conditions
        conditions = []
        
        if filter_params.user_id:
            conditions.append(Feedback.user_id == filter_params.user_id)
        
        if filter_params.query_id:
            conditions.append(Feedback.query_id == filter_params.query_id)
        
        if filter_params.start_date:
            conditions.append(Feedback.feedback_time >= filter_params.start_date)
        
        if filter_params.end_date:
            conditions.append(Feedback.feedback_time <= filter_params.end_date)
        
        if filter_params.min_rating and filter_params.max_rating:
            conditions.append(between(Feedback.rating, filter_params.min_rating, filter_params.max_rating))
        elif filter_params.min_rating:
            conditions.append(Feedback.rating >= filter_params.min_rating)
        elif filter_params.max_rating:
            conditions.append(Feedback.rating <= filter_params.max_rating)
        
        # Apply filters
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        
        result = db.execute(stmt)
        return result.scalars().all()
    
    async def get_filtered_async(self, db: AsyncSession, filter_params: FeedbackFilter, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Asynchronously get feedback based on filter criteria with pagination
        
        Args:
            db: Async database session
            filter_params: Filter parameters for querying
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of filtered feedback
        """
        stmt = select(Feedback)
        
        # Build filter conditions
        conditions = []
        
        if filter_params.user_id:
            conditions.append(Feedback.user_id == filter_params.user_id)
        
        if filter_params.query_id:
            conditions.append(Feedback.query_id == filter_params.query_id)
        
        if filter_params.start_date:
            conditions.append(Feedback.feedback_time >= filter_params.start_date)
        
        if filter_params.end_date:
            conditions.append(Feedback.feedback_time <= filter_params.end_date)
        
        if filter_params.min_rating and filter_params.max_rating:
            conditions.append(between(Feedback.rating, filter_params.min_rating, filter_params.max_rating))
        elif filter_params.min_rating:
            conditions.append(Feedback.rating >= filter_params.min_rating)
        elif filter_params.max_rating:
            conditions.append(Feedback.rating <= filter_params.max_rating)
        
        # Apply filters
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_statistics(self, db: Session, filter_params: Optional[FeedbackFilter] = None) -> FeedbackStats:
        """
        Calculate statistics for feedback based on filter criteria
        
        Args:
            db: Database session
            filter_params: Optional filter parameters to restrict the statistics calculation
            
        Returns:
            Statistics object with average rating and distribution
        """
        # Build base query
        query = select(Feedback)
        conditions = []
        
        # Apply filters if provided
        if filter_params:
            if filter_params.user_id:
                conditions.append(Feedback.user_id == filter_params.user_id)
            
            if filter_params.query_id:
                conditions.append(Feedback.query_id == filter_params.query_id)
            
            if filter_params.start_date:
                conditions.append(Feedback.feedback_time >= filter_params.start_date)
            
            if filter_params.end_date:
                conditions.append(Feedback.feedback_time <= filter_params.end_date)
            
            if filter_params.min_rating and filter_params.max_rating:
                conditions.append(between(Feedback.rating, filter_params.min_rating, filter_params.max_rating))
            elif filter_params.min_rating:
                conditions.append(Feedback.rating >= filter_params.min_rating)
            elif filter_params.max_rating:
                conditions.append(Feedback.rating <= filter_params.max_rating)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Calculate average rating
        avg_query = select(func.avg(Feedback.rating).label("average_rating"))
        if filter_params and conditions:
            avg_query = avg_query.select_from(query.subquery())
        
        avg_result = db.execute(avg_query)
        avg_rating = avg_result.scalar() or 0.0
        
        # Calculate total count
        count_query = select(func.count(Feedback.id).label("total_feedback"))
        if filter_params and conditions:
            count_query = count_query.select_from(query.subquery())
        
        count_result = db.execute(count_query)
        total_feedback = count_result.scalar() or 0
        
        # Calculate distribution (count by rating)
        distribution_query = select(
            Feedback.rating, 
            func.count(Feedback.id).label("count")
        ).group_by(Feedback.rating)
        
        if filter_params and conditions:
            distribution_query = distribution_query.select_from(query.subquery())
        
        distribution_result = db.execute(distribution_query)
        distribution = {int(rating): int(count) for rating, count in distribution_result}
        
        # Ensure all ratings are represented in the distribution
        for rating in range(1, 6):
            if rating not in distribution:
                distribution[rating] = 0
        
        # Create statistics object
        return FeedbackStats(
            average_rating=float(avg_rating),
            total_feedback=total_feedback,
            rating_distribution=distribution
        )
    
    async def get_statistics_async(self, db: AsyncSession, filter_params: Optional[FeedbackFilter] = None) -> FeedbackStats:
        """
        Asynchronously calculate statistics for feedback based on filter criteria
        
        Args:
            db: Async database session
            filter_params: Optional filter parameters to restrict the statistics calculation
            
        Returns:
            Statistics object with average rating and distribution
        """
        # Build base query
        query = select(Feedback)
        conditions = []
        
        # Apply filters if provided
        if filter_params:
            if filter_params.user_id:
                conditions.append(Feedback.user_id == filter_params.user_id)
            
            if filter_params.query_id:
                conditions.append(Feedback.query_id == filter_params.query_id)
            
            if filter_params.start_date:
                conditions.append(Feedback.feedback_time >= filter_params.start_date)
            
            if filter_params.end_date:
                conditions.append(Feedback.feedback_time <= filter_params.end_date)
            
            if filter_params.min_rating and filter_params.max_rating:
                conditions.append(between(Feedback.rating, filter_params.min_rating, filter_params.max_rating))
            elif filter_params.min_rating:
                conditions.append(Feedback.rating >= filter_params.min_rating)
            elif filter_params.max_rating:
                conditions.append(Feedback.rating <= filter_params.max_rating)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Calculate average rating
        avg_query = select(func.avg(Feedback.rating).label("average_rating"))
        if filter_params and conditions:
            avg_query = avg_query.select_from(query.subquery())
        
        avg_result = await db.execute(avg_query)
        avg_rating = avg_result.scalar() or 0.0
        
        # Calculate total count
        count_query = select(func.count(Feedback.id).label("total_feedback"))
        if filter_params and conditions:
            count_query = count_query.select_from(query.subquery())
        
        count_result = await db.execute(count_query)
        total_feedback = count_result.scalar() or 0
        
        # Calculate distribution (count by rating)
        distribution_query = select(
            Feedback.rating, 
            func.count(Feedback.id).label("count")
        ).group_by(Feedback.rating)
        
        if filter_params and conditions:
            distribution_query = distribution_query.select_from(query.subquery())
        
        distribution_result = await db.execute(distribution_query)
        distribution = {int(rating): int(count) for rating, count in distribution_result}
        
        # Ensure all ratings are represented in the distribution
        for rating in range(1, 6):
            if rating not in distribution:
                distribution[rating] = 0
        
        # Create statistics object
        return FeedbackStats(
            average_rating=float(avg_rating),
            total_feedback=total_feedback,
            rating_distribution=distribution
        )
    
    def get_positive_feedback(self, db: Session, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Get positive feedback (rating 4-5) with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of positive feedback
        """
        stmt = select(Feedback).where(Feedback.rating >= 4).order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()
    
    async def get_positive_feedback_async(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Asynchronously get positive feedback (rating 4-5) with pagination
        
        Args:
            db: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of positive feedback
        """
        stmt = select(Feedback).where(Feedback.rating >= 4).order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_negative_feedback(self, db: Session, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Get negative feedback (rating 1-2) with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of negative feedback
        """
        stmt = select(Feedback).where(Feedback.rating <= 2).order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()
    
    async def get_negative_feedback_async(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Feedback]:
        """
        Asynchronously get negative feedback (rating 1-2) with pagination
        
        Args:
            db: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of negative feedback
        """
        stmt = select(Feedback).where(Feedback.rating <= 2).order_by(Feedback.feedback_time.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


# Singleton instance for use throughout the application
feedback = CRUDFeedback()