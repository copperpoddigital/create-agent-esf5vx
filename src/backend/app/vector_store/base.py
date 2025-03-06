"""
Abstract base class for vector storage implementations in the Document Management and AI Chatbot System.
This module defines the interface that all vector store implementations must follow, providing a consistent
API for vector operations such as adding, searching, and deleting vectors.
"""

import abc
import os
import logging
from typing import List, Dict, Any, Optional

import numpy as np  # version 1.24.0+

from ..core.settings import vector_settings
from ..utils.vector_utils import validate_vector_dimensions

# Configure logger
logger = logging.getLogger(__name__)

class VectorStore(abc.ABC):
    """
    Abstract base class that defines the interface for vector storage implementations.
    All vector store implementations must inherit from this class and implement its abstract methods.
    """
    
    @property
    def index_path(self) -> str:
        """Get the path where the vector index is stored."""
        return self._index_path
    
    @property
    def vector_dimension(self) -> int:
        """Get the dimension of vectors in this store."""
        return self._vector_dimension
    
    def __init__(self, index_path: Optional[str] = None, vector_dimension: Optional[int] = None):
        """
        Initializes the VectorStore with configuration settings.
        
        Args:
            index_path: Path where the vector index will be stored
            vector_dimension: Dimension of vectors to be stored
        """
        self._index_path = index_path or vector_settings.VECTOR_INDEX_PATH
        self._vector_dimension = vector_dimension or vector_settings.VECTOR_DIMENSION
        logger.info(f"Initializing vector store with dimension {self._vector_dimension}")
    
    @abc.abstractmethod
    def add_vectors(self, vectors: List[np.ndarray], ids: List[str]) -> bool:
        """
        Adds vectors to the store with their corresponding IDs.
        
        Args:
            vectors: List of vectors to add
            ids: List of IDs corresponding to the vectors
            
        Returns:
            True if vectors were added successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def search(self, query_vector: np.ndarray, top_k: Optional[int] = None, 
               threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Searches for similar vectors in the store.
        
        Args:
            query_vector: Vector to search for
            top_k: Number of results to return
            threshold: Similarity threshold for filtering results
            
        Returns:
            List of dictionaries containing id, vector, and similarity score
        """
        pass
    
    @abc.abstractmethod
    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Deletes vectors from the store by their IDs.
        
        Args:
            ids: List of IDs of vectors to delete
            
        Returns:
            True if vectors were deleted successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_vector(self, id: str) -> Optional[np.ndarray]:
        """
        Retrieves a vector from the store by its ID.
        
        Args:
            id: ID of the vector to retrieve
            
        Returns:
            The vector if found, None otherwise
        """
        pass
    
    @abc.abstractmethod
    def contains(self, id: str) -> bool:
        """
        Checks if a vector ID exists in the store.
        
        Args:
            id: ID to check
            
        Returns:
            True if the vector ID exists, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def count(self) -> int:
        """
        Returns the number of vectors in the store.
        
        Returns:
            Number of vectors in the store
        """
        pass
    
    @abc.abstractmethod
    def save(self, path: Optional[str] = None) -> bool:
        """
        Saves the vector store to disk.
        
        Args:
            path: Path where to save the vector store. If None, uses the index_path.
            
        Returns:
            True if the store was saved successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def load(self, path: Optional[str] = None) -> bool:
        """
        Loads the vector store from disk.
        
        Args:
            path: Path from where to load the vector store. If None, uses the index_path.
            
        Returns:
            True if the store was loaded successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def clear(self) -> bool:
        """
        Clears all vectors from the store.
        
        Returns:
            True if the store was cleared successfully, False otherwise
        """
        pass
    
    def _validate_inputs(self, vectors: List[np.ndarray], ids: List[str]) -> bool:
        """
        Validates input vectors and IDs.
        
        Args:
            vectors: List of vectors to validate
            ids: List of IDs to validate
            
        Returns:
            True if inputs are valid, False otherwise
        """
        if vectors is None or ids is None:
            logger.error("Vectors or IDs cannot be None")
            return False
        
        if len(vectors) != len(ids):
            logger.error(f"Number of vectors ({len(vectors)}) must match number of IDs ({len(ids)})")
            return False
        
        for i, vector in enumerate(vectors):
            if not validate_vector_dimensions(vector, self._vector_dimension):
                logger.error(f"Vector at index {i} has invalid dimensions")
                return False
        
        return True
    
    def _ensure_directory_exists(self, path: str) -> bool:
        """
        Ensures that the directory for the index file exists.
        
        Args:
            path: Path to check/create
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
                return True
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {str(e)}")
                return False
        return True