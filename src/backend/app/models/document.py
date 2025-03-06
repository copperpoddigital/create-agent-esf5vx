import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, UUID, ForeignKey  # sqlalchemy 2.0.0+
from sqlalchemy.orm import relationship  # sqlalchemy 2.0.0+
from sqlalchemy.sql import func  # sqlalchemy 2.0.0+

from ..db.base_class import Base
from .user import User

# Define document status enum
DocumentStatus = enum.Enum('DocumentStatus', ['processing', 'available', 'error', 'deleted'])  # standard library

class Document(Base):
    """
    SQLAlchemy ORM model representing a document in the system.
    
    Contains document metadata such as title, filename, size, upload date, status,
    and file path, along with relationships to the uploader and document chunks.
    """
    
    # Primary key
    id = Column(UUID, primary_key=True, index=True)
    
    # Document metadata
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    upload_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.processing, nullable=False)
    file_path = Column(String(255), nullable=False)
    
    # Relationships
    uploader_id = Column(UUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    uploader = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __init__(self):
        """
        Default constructor for the Document class
        
        Initialize the Document object with default values
        Set status to 'processing' by default
        Set upload_date to current timestamp by default
        """
        # Default values will be set by SQLAlchemy from the Column defaults
        pass
    
    def __repr__(self):
        """
        String representation of the Document object
        
        Returns:
            str: String representation with title and status
        """
        return f"Document(title={self.title}, status={self.status.name})"
    
    def update_status(self, new_status):
        """
        Updates the document status
        
        Args:
            new_status (DocumentStatus): The new status to set
        """
        self.status = new_status
    
    def is_available(self):
        """
        Checks if the document is available for search and retrieval
        
        Returns:
            bool: True if document status is 'available', False otherwise
        """
        return self.status == DocumentStatus.available
    
    def is_deleted(self):
        """
        Checks if the document has been marked as deleted
        
        Returns:
            bool: True if document status is 'deleted', False otherwise
        """
        return self.status == DocumentStatus.deleted