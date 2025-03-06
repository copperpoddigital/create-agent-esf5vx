from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, DateTime, UUID, ForeignKey, CheckConstraint, Index  # SQLAlchemy 2.0.0+
from sqlalchemy.orm import relationship  # SQLAlchemy 2.0.0+
from sqlalchemy.sql import func  # SQLAlchemy 2.0.0+

from ..db.base_class import Base
from .user import User
from .query import Query


class Feedback(Base):
    """
    SQLAlchemy ORM model representing user feedback on AI-generated responses.
    Contains the rating, optional comments, timestamp, and relationships to the user who provided the feedback and the query being rated.
    """
    
    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    
    # Foreign keys
    query_id = Column(UUID, ForeignKey(Query.id), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    
    # Feedback data
    rating = Column(Integer, nullable=False)
    comments = Column(Text, nullable=True)
    
    # Timestamp
    feedback_time = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    query = relationship("Query", back_populates="feedback")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('rating BETWEEN 1 AND 5', name='valid_rating'),
        Index('idx_feedback_query_id', query_id),
        Index('idx_feedback_user_id', user_id),
    )
    
    def __init__(self):
        """
        Default constructor for the Feedback class
        
        Initialize the Feedback object with default values
        Set feedback_time to current timestamp by default
        """
        # Default values will be set by SQLAlchemy from the Column defaults
        pass
    
    def __repr__(self):
        """
        String representation of the Feedback object
        
        Returns:
            str: String representation with feedback ID and rating
        """
        return f"Feedback(id={self.id}, rating={self.rating})"
    
    def is_positive(self):
        """
        Checks if the feedback rating is positive (4 or 5)
        
        Returns:
            bool: True if rating is 4 or 5, False otherwise
        """
        return self.rating >= 4
    
    def is_negative(self):
        """
        Checks if the feedback rating is negative (1 or 2)
        
        Returns:
            bool: True if rating is 1 or 2, False otherwise
        """
        return self.rating <= 2
    
    def is_neutral(self):
        """
        Checks if the feedback rating is neutral (3)
        
        Returns:
            bool: True if rating is 3, False otherwise
        """
        return self.rating == 3
    
    def has_comments(self):
        """
        Checks if the feedback includes comments
        
        Returns:
            bool: True if comments field is not empty, False otherwise
        """
        return self.comments is not None and self.comments.strip() != ""