"""
Vector utilities for document embeddings and similarity search.

This module provides utility functions for vector operations including normalization,
similarity calculation, serialization/deserialization, and other vector-related
operations used throughout the Document Management and AI Chatbot System.
"""

import numpy as np  # version 1.24.0+
import logging
import uuid
import base64
from typing import List, Optional, Union, Tuple

# Import vector settings
from ..core.settings import settings

# Create a shorthand reference to vector search settings for convenience
vector_settings = settings.vector_search

# Configure logger
logger = logging.getLogger(__name__)

def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    Normalizes a vector to unit length (L2 norm) for consistent similarity calculations.
    
    Args:
        vector (np.ndarray): The vector to normalize
        
    Returns:
        np.ndarray: Normalized vector with unit length
    """
    # Calculate L2 norm
    norm = np.linalg.norm(vector)
    
    # Check if norm is zero to avoid division by zero
    if norm == 0:
        logger.warning("Cannot normalize a zero vector. Returning original vector.")
        return vector
    
    # Divide vector by its norm to normalize
    normalized_vector = vector / norm
    return normalized_vector

def validate_vector_dimensions(vector: np.ndarray, expected_dim: Optional[int] = None) -> bool:
    """
    Validates that a vector has the expected dimensions.
    
    Args:
        vector (np.ndarray): The vector to validate
        expected_dim (Optional[int]): Expected dimension, defaults to vector_settings.VECTOR_DIMENSION
        
    Returns:
        bool: True if vector has valid dimensions, False otherwise
    """
    if expected_dim is None:
        expected_dim = vector_settings.VECTOR_DIMENSION
    
    # Check if vector is None
    if vector is None:
        logger.warning("Cannot validate dimensions of None vector")
        return False
    
    # Check if vector has the expected dimension
    if vector.shape[-1] != expected_dim:
        logger.warning(
            f"Vector has invalid dimensions. Expected {expected_dim}, got {vector.shape[-1]}"
        )
        return False
    
    return True

def calculate_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    """
    Calculates cosine similarity between two vectors.
    
    Args:
        vector_a (np.ndarray): First vector
        vector_b (np.ndarray): Second vector
        
    Returns:
        float: Cosine similarity score between 0 and 1
        
    Raises:
        ValueError: If vectors don't have the same dimensions
    """
    # Validate both vectors have the same dimensions
    if vector_a.shape != vector_b.shape:
        raise ValueError(
            f"Vectors must have same dimensions. Got {vector_a.shape} and {vector_b.shape}"
        )
    
    # Normalize both vectors to unit length
    vector_a_norm = normalize_vector(vector_a)
    vector_b_norm = normalize_vector(vector_b)
    
    # Calculate dot product (cosine similarity for normalized vectors)
    similarity = np.dot(vector_a_norm, vector_b_norm)
    
    # Ensure result is between 0 and 1 (to handle floating point errors)
    similarity = max(0.0, min(1.0, similarity))
    
    return float(similarity)

def generate_embedding_id() -> str:
    """
    Generates a unique identifier for a vector embedding.
    
    Returns:
        str: Unique embedding ID
    """
    # Generate a UUID using uuid.uuid4()
    embedding_id = str(uuid.uuid4())
    return embedding_id

def serialize_vector(vector: np.ndarray) -> str:
    """
    Serializes a vector to a string format for storage.
    
    Args:
        vector (np.ndarray): Vector to serialize
        
    Returns:
        str: Base64 encoded string representation of the vector
        
    Raises:
        ValueError: If vector dimensions are invalid
    """
    # Validate vector dimensions
    if not validate_vector_dimensions(vector):
        raise ValueError(f"Invalid vector dimensions: {vector.shape}")
    
    # Ensure vector is in float32 format for consistent serialization
    vector = vector.astype(np.float32)
    
    # Convert vector to bytes using numpy.ndarray.tobytes()
    vector_bytes = vector.tobytes()
    
    # Encode bytes to base64 string
    vector_b64 = base64.b64encode(vector_bytes).decode('utf-8')
    
    return vector_b64

def deserialize_vector(serialized_vector: str, vector_dim: Optional[int] = None) -> np.ndarray:
    """
    Deserializes a vector from a string format.
    
    Args:
        serialized_vector (str): Base64 encoded string representation of the vector
        vector_dim (Optional[int]): Expected vector dimension, defaults to vector_settings.VECTOR_DIMENSION
        
    Returns:
        np.ndarray: Vector reconstructed from the serialized string
        
    Raises:
        ValueError: If deserialization fails
    """
    if vector_dim is None:
        vector_dim = vector_settings.VECTOR_DIMENSION
    
    try:
        # Decode base64 string to bytes
        vector_bytes = base64.b64decode(serialized_vector)
        
        # Reconstruct numpy array from bytes
        vector = np.frombuffer(vector_bytes, dtype=np.float32)
        
        # Reshape array to correct dimensions
        if len(vector) != vector_dim:
            raise ValueError(
                f"Deserialized vector has wrong size. Expected {vector_dim}, got {len(vector)}"
            )
        
        # Validate reconstructed vector dimensions
        if not validate_vector_dimensions(vector, vector_dim):
            raise ValueError(f"Deserialized vector has invalid dimensions")
        
        return vector
    except Exception as e:
        logger.error(f"Error deserializing vector: {str(e)}")
        raise ValueError(f"Failed to deserialize vector: {str(e)}")

def batch_normalize_vectors(vectors: List[np.ndarray]) -> List[np.ndarray]:
    """
    Normalizes a batch of vectors to unit length.
    
    Args:
        vectors (List[np.ndarray]): List of vectors to normalize
        
    Returns:
        List[np.ndarray]: List of normalized vectors
        
    Raises:
        ValueError: If input is not a list of vectors
    """
    # Validate input is a list of vectors
    if not isinstance(vectors, list):
        raise ValueError("Input must be a list of vectors")
    
    # Apply normalize_vector to each vector in the list
    normalized_vectors = [normalize_vector(vector) for vector in vectors]
    return normalized_vectors

def convert_to_numpy_array(vector_data: Union[list, tuple, np.ndarray]) -> np.ndarray:
    """
    Converts various input types to numpy array with proper dimensions.
    
    Args:
        vector_data (Union[list, tuple, np.ndarray]): Vector data to convert
        
    Returns:
        np.ndarray: Numpy array with proper dimensions
        
    Raises:
        ValueError: If input cannot be converted to a valid numpy array
    """
    try:
        # Check input type
        if isinstance(vector_data, np.ndarray):
            vector = vector_data.copy()
        else:
            # Convert list or tuple to numpy array if needed
            vector = np.array(vector_data, dtype=np.float32)
        
        # Ensure array has correct data type (float32)
        if vector.dtype != np.float32:
            vector = vector.astype(np.float32)
        
        # Reshape array if necessary
        if len(vector.shape) > 1:
            vector = vector.reshape(-1)
        
        # Validate dimensions of resulting array
        if not validate_vector_dimensions(vector):
            raise ValueError(f"Converted array has invalid dimensions: {vector.shape}")
        
        return vector
    except Exception as e:
        logger.error(f"Error converting to numpy array: {str(e)}")
        raise ValueError(f"Failed to convert input to numpy array: {str(e)}")

def combine_vectors(vectors: List[np.ndarray], method: str = 'mean') -> np.ndarray:
    """
    Combines multiple vectors into a single representative vector.
    
    Args:
        vectors (List[np.ndarray]): List of vectors to combine
        method (str): Combination method: 'mean', 'max', or 'sum'
        
    Returns:
        np.ndarray: Combined vector
        
    Raises:
        ValueError: If vectors list is empty or vectors have different dimensions
    """
    if not vectors:
        raise ValueError("Cannot combine empty list of vectors")
    
    # Validate all vectors have the same dimensions
    vector_array = np.array(vectors)
    shape = vector_array.shape
    if len(shape) != 2:
        raise ValueError(f"Expected 2D array of vectors, got shape {shape}")
    
    # If method is 'mean', calculate element-wise mean of vectors
    if method == 'mean':
        combined_vector = np.mean(vector_array, axis=0)
    # If method is 'max', calculate element-wise maximum of vectors
    elif method == 'max':
        combined_vector = np.max(vector_array, axis=0)
    # If method is 'sum', calculate element-wise sum of vectors
    elif method == 'sum':
        combined_vector = np.sum(vector_array, axis=0)
    else:
        raise ValueError(f"Unsupported combination method: {method}")
    
    # Normalize the resulting combined vector
    combined_vector = normalize_vector(combined_vector)
    
    return combined_vector