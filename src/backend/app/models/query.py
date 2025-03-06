from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, Index  # sqlalchemy 2.0.0+
from sqlalchemy.orm import relationship  # sqlalchemy 2.0.0+
from sqlalchemy.dialects.postgresql import JSONB  # sqlalchemy 2.0.0+
from sqlalchemy.sql import func  # sqlalchemy 2.0.0+

from ..db.base_class import Base
from .user import User


class Query(Base):
    """
    SQLAlchemy ORM model representing a user query and its AI-generated response.
    
    This model stores search queries, AI-generated responses, and references to the
    context documents that were used to generate the response. It supports the
    vector search and query results retrieval features of the system.
    """
    
    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    
    # Foreign key to user who made the query
    user_id = Column(UUID, ForeignKey(User.id), nullable=False, index=True)
    
    # Query content
    query_text = Column(Text, nullable=False)
    query_time = Column(DateTime, default=func.now(), nullable=False, index=True)
    response_text = Column(Text, nullable=False)
    
    # Document context used for response generation
    context_documents = Column(JSONB, nullable=False)
    
    # Reference to vector embedding in FAISS
    embedding_id = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="queries")
    feedback = relationship("Feedback", back_populates="query", cascade="all, delete-orphan")
    
    # Indexes for performance optimization
    __table_args__ = (
        Index('idx_query_user_id', user_id),
        Index('idx_query_time', query_time),
    )
    
    def __init__(self):
        """
        Default constructor for the Query class.
        
        Initialize the Query object with default values.
        Set query_time to current timestamp by default.
        """
        # Default values will be set by SQLAlchemy from the Column defaults
        pass
    
    def __repr__(self):
        """
        String representation of the Query object.
        
        Returns:
            str: String representation with query ID and text preview.
        """
        return f"Query(id={self.id}, text={self.get_query_preview(30)})"
    
    def get_query_preview(self, max_length=50):
        """
        Returns a preview of the query text (first N characters).
        
        Args:
            max_length (int): Maximum length of the preview text. Defaults to 50.
            
        Returns:
            str: Preview of the query text, truncated if necessary.
        """
        if not self.query_text:
            return ""
        
        if len(self.query_text) <= max_length:
            return self.query_text
        
        return f"{self.query_text[:max_length]}..."
    
    def get_response_preview(self, max_length=100):
        """
        Returns a preview of the response text (first N characters).
        
        Args:
            max_length (int): Maximum length of the preview text. Defaults to 100.
            
        Returns:
            str: Preview of the response text, truncated if necessary.
        """
        if not self.response_text:
            return ""
        
        if len(self.response_text) <= max_length:
            return self.response_text
        
        return f"{self.response_text[:max_length]}..."
    
    def has_feedback(self):
        """
        Checks if the query has received any feedback.
        
        Returns:
            bool: True if query has feedback, False otherwise.
        """
        return len(self.feedback) > 0