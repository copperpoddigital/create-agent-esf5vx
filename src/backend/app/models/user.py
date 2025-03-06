import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, UUID  # sqlalchemy 2.0.0+
from sqlalchemy.orm import relationship  # sqlalchemy 2.0.0+
from sqlalchemy.sql import func  # sqlalchemy 2.0.0+

from ..db.base_class import Base

# Define UserRole enum
UserRole = enum.Enum('UserRole', ['admin', 'regular'])  # standard library

class User(Base):
    """
    SQLAlchemy ORM model representing a user in the system.
    
    Contains user authentication information, role-based permissions, and
    relationships to documents, queries, and feedback.
    """
    
    # Primary key
    id = Column(UUID, primary_key=True, index=True)
    
    # User authentication information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User status and permissions
    role = Column(Enum(UserRole), nullable=False, default=UserRole.regular)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships to other models
    # One-to-many relationship with Document model
    documents = relationship("Document", back_populates="uploader", cascade="all, delete-orphan")
    
    # One-to-many relationship with Query model
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    
    # One-to-many relationship with Feedback model
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self):
        """
        Default constructor for the User class
        
        Initialize the User object with default values
        Set is_active to True by default
        Set role to 'regular' by default
        Set created_at to current timestamp by default
        """
        # Default values will be set by SQLAlchemy from the Column defaults
        pass
    
    def __repr__(self):
        """
        String representation of the User object
        
        Returns:
            str: String representation with username and role
        """
        return f"User(username={self.username}, role={self.role.name})"
    
    def is_admin(self):
        """
        Checks if the user has admin role
        
        Returns:
            bool: True if user has admin role, False otherwise
        """
        return self.role == UserRole.admin
    
    def update_last_login(self):
        """
        Updates the last_login timestamp to current time
        """
        self.last_login = func.now()