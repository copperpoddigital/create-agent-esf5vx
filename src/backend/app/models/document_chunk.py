from sqlalchemy import Column, String, Integer, Text, UUID, ForeignKey, Index, UniqueConstraint  # sqlalchemy 2.0.0+
from sqlalchemy.orm import relationship  # sqlalchemy 2.0.0+

from ..db.base_class import Base
from .document import Document


class DocumentChunk(Base):
    """
    SQLAlchemy ORM model representing a chunk of text extracted from a document.
    
    Contains the chunk content, position in the document, token count, and reference
    to its vector embedding in FAISS. This model is used for storing document chunks
    after text extraction and enabling similarity search based on vector embeddings.
    """
    
    # Primary key
    id = Column(UUID, primary_key=True, index=True)
    
    # Foreign key relationship to Document
    document_id = Column(UUID, ForeignKey(Document.id, ondelete="CASCADE"), nullable=False)
    
    # Chunk metadata
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    
    # Reference to vector embedding in FAISS
    embedding_id = Column(String(100), nullable=False)
    
    # Relationship to the parent document
    document = relationship("Document", back_populates="chunks")
    
    # Indexes and constraints
    __table_args__ = (
        Index("ix_document_chunk_document_id", "document_id"),
        Index("ix_document_chunk_embedding_id", "embedding_id"),
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_document_id_chunk_index"),
    )
    
    def __init__(self):
        """
        Default constructor for the DocumentChunk class
        
        Initialize the DocumentChunk object with default values
        """
        # Default values will be set by SQLAlchemy
        pass
    
    def __repr__(self):
        """
        String representation of the DocumentChunk object
        
        Returns:
            str: String representation with document_id and chunk_index
        """
        return f"DocumentChunk(document_id={self.document_id}, chunk_index={self.chunk_index})"
    
    def update_embedding_id(self, embedding_id: str) -> None:
        """
        Updates the embedding ID reference after vector generation
        
        Args:
            embedding_id (str): The new embedding ID to set
        
        Returns:
            None: No return value
        """
        self.embedding_id = embedding_id
    
    def get_content_preview(self, max_length: int = 50) -> str:
        """
        Returns a preview of the chunk content (first 50 characters)
        
        Args:
            max_length (int, optional): Maximum length of the preview. Defaults to 50.
        
        Returns:
            str: Preview of the chunk content
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."