from __future__ import annotations  # Enable postponed evaluation of annotations

from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, UUID4, validator  # version 2.0.0+

from .query import Query  # Import Query schema for relationships


class FeedbackBase(BaseModel):
    """Base Pydantic model for feedback data with common attributes."""
    rating: int = Field(..., description="Feedback rating from 1 to 5")
    comments: Optional[str] = Field(None, description="Additional feedback comments")
    
    @validator('rating')
    def validate_rating(cls, rating: int) -> int:
        """
        Validates that the rating is between 1 and 5.
        
        Args:
            rating: The rating value to validate
            
        Returns:
            int: The validated rating
            
        Raises:
            ValueError: If rating is not between 1 and 5
        """
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating


class FeedbackCreate(FeedbackBase):
    """Schema for feedback submission with query ID and rating."""
    query_id: UUID4 = Field(..., description="ID of the query being rated")


class FeedbackInDBBase(FeedbackBase):
    """Base schema for feedback data from database including ID and timestamps."""
    id: UUID4 = Field(..., description="Unique identifier for the feedback")
    user_id: UUID4 = Field(..., description="ID of the user who provided the feedback")
    query_id: UUID4 = Field(..., description="ID of the query being rated")
    feedback_time: datetime = Field(..., description="Timestamp when feedback was submitted")
    
    @classmethod
    def model_config(cls):
        return ConfigDict(from_attributes=True)


class Feedback(FeedbackInDBBase):
    """Schema for feedback data returned to clients."""
    
    def is_positive(self) -> bool:
        """
        Checks if the feedback rating is positive (4 or 5).
        
        Returns:
            bool: True if rating is 4 or 5, False otherwise
        """
        return self.rating >= 4
    
    def is_negative(self) -> bool:
        """
        Checks if the feedback rating is negative (1 or 2).
        
        Returns:
            bool: True if rating is 1 or 2, False otherwise
        """
        return self.rating <= 2
    
    def is_neutral(self) -> bool:
        """
        Checks if the feedback rating is neutral (3).
        
        Returns:
            bool: True if rating is 3, False otherwise
        """
        return self.rating == 3
    
    def has_comments(self) -> bool:
        """
        Checks if the feedback includes comments.
        
        Returns:
            bool: True if comments field is not empty, False otherwise
        """
        return self.comments is not None and len(self.comments) > 0


class FeedbackWithQuery(Feedback):
    """Schema for feedback data including associated query information."""
    query: Query = Field(..., description="The query that received this feedback")


class FeedbackFilter(BaseModel):
    """Schema for filtering feedback data."""
    user_id: Optional[UUID4] = Field(None, description="Filter by user ID")
    query_id: Optional[UUID4] = Field(None, description="Filter by query ID")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    min_rating: Optional[int] = Field(None, description="Filter by minimum rating")
    max_rating: Optional[int] = Field(None, description="Filter by maximum rating")
    
    @validator('min_rating', 'max_rating')
    def validate_rating_range(cls, value: Optional[int], values: Dict[str, Any]) -> Optional[int]:
        """
        Validates that min_rating and max_rating are valid.
        
        Args:
            value: The rating value to validate
            values: Dictionary of values already validated
            
        Returns:
            Optional[int]: The validated rating value
            
        Raises:
            ValueError: If rating is not between 1 and 5
        """
        if value is not None and (value < 1 or value > 5):
            raise ValueError("Rating must be between 1 and 5")
        return value


class FeedbackStats(BaseModel):
    """Schema for feedback statistics."""
    average_rating: float = Field(..., description="Average rating score")
    total_feedback: int = Field(..., description="Total number of feedback entries")
    rating_distribution: Dict[int, int] = Field(..., description="Count of each rating value")
    positive_percentage: Optional[float] = Field(None, description="Percentage of positive ratings (4-5)")
    negative_percentage: Optional[float] = Field(None, description="Percentage of negative ratings (1-2)")
    neutral_percentage: Optional[float] = Field(None, description="Percentage of neutral ratings (3)")
    
    @validator('positive_percentage', 'negative_percentage', 'neutral_percentage', always=True)
    def calculate_percentages(cls, value: Optional[float], values: Dict[str, Any]) -> Optional[float]:
        """
        Calculates percentage breakdowns of feedback ratings.
        
        Args:
            value: The current value (ignored as we'll calculate it)
            values: Dictionary of values already validated
            
        Returns:
            Optional[float]: Calculated percentage
        """
        # If we don't have distribution or total, can't calculate
        if 'rating_distribution' not in values or 'total_feedback' not in values or values['total_feedback'] == 0:
            return None
        
        distribution = values['rating_distribution']
        total = values['total_feedback']
        
        # Find the field name we're currently validating
        current_field = None
        for field in ['positive_percentage', 'negative_percentage', 'neutral_percentage']:
            if field not in values:
                current_field = field
                break
        
        if current_field == 'positive_percentage':
            # Positive: ratings 4-5
            count = distribution.get(4, 0) + distribution.get(5, 0)
            return round((count / total) * 100, 2)
        
        elif current_field == 'negative_percentage':
            # Negative: ratings 1-2
            count = distribution.get(1, 0) + distribution.get(2, 0)
            return round((count / total) * 100, 2)
        
        elif current_field == 'neutral_percentage':
            # Neutral: rating 3
            count = distribution.get(3, 0)
            return round((count / total) * 100, 2)
        
        return value