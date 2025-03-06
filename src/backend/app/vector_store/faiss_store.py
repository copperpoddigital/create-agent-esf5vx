"""
Implementation of the FAISS vector store for the Document Management and AI Chatbot System.

This module provides a concrete implementation of the VectorStore abstract base class
using Facebook AI Similarity Search (FAISS) for efficient storage and retrieval of
high-dimensional vector embeddings.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np  # version 1.24.0+
import faiss  # version 1.7.4+

from .base import VectorStore
from ..core.settings import vector_settings
from ..utils.vector_utils import normalize_vector, validate_vector_dimensions

# Configure logger
logger = logging.getLogger(__name__)

class FAISSStore(VectorStore):
    """
    Concrete implementation of the VectorStore abstract base class using FAISS
    for efficient vector storage and similarity search.
    """
    
    def __init__(self, index_path: Optional[str] = None, vector_dimension: Optional[int] = None):
        """
        Initializes the FAISS vector store with configuration settings.
        
        Args:
            index_path: Path where the vector index will be stored
            vector_dimension: Dimension of vectors to be stored
        """
        # Call parent constructor
        super().__init__(index_path, vector_dimension)
        
        # Initialize ID mapping dictionaries
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: Dict[int, str] = {}
        self._next_index: int = 0
        self._index = None
        
        # Create or load FAISS index
        if os.path.exists(self._index_path + ".faiss"):
            self.load()
        else:
            self._index = self._create_index()
            logger.info(f"Created new FAISS index with dimension {self._vector_dimension}")
        
        logger.info(f"Initialized FAISS store with {self.count()} vectors")

    def _create_index(self) -> faiss.Index:
        """
        Creates a new FAISS index based on configuration settings.
        
        Returns:
            Newly created FAISS index
        """
        index_type = vector_settings.INDEX_TYPE
        dimension = self._vector_dimension
        
        if index_type == "Flat":
            # Flat index for exact search (slower but more accurate)
            index = faiss.IndexFlatIP(dimension)
            logger.info(f"Created Flat index with dimension {dimension}")
        elif index_type == "IVFFlat":
            # IVF index for approximate search (faster with slight accuracy trade-off)
            nlist = vector_settings.NLIST
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            
            # Train the index with random vectors if no data available
            if not index.is_trained:
                logger.info(f"Training IVFFlat index with {2 * nlist} random vectors")
                train_data = np.random.random((2 * nlist, dimension)).astype(np.float32)
                train_data = normalize_vector(train_data)
                index.train(train_data)
            
            # Set nprobe parameter for search
            index.nprobe = vector_settings.NPROBE
            logger.info(f"Created IVFFlat index with dimension {dimension}, nlist={nlist}, nprobe={index.nprobe}")
        elif index_type == "HNSW":
            # HNSW index for efficient approximate search
            m = 32  # Number of connections per layer
            ef_construction = 200  # Size of the dynamic list for constructing the graph
            index = faiss.IndexHNSWFlat(dimension, m, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efConstruction = ef_construction
            index.hnsw.efSearch = 128  # Size of the dynamic list for searching
            logger.info(f"Created HNSW index with dimension {dimension}, m={m}, efConstruction={ef_construction}")
        else:
            # Fallback to flat index if unsupported type
            logger.warning(f"Unsupported index type: {index_type}, falling back to Flat index")
            index = faiss.IndexFlatIP(dimension)
        
        return index

    def add_vectors(self, vectors: List[np.ndarray], ids: List[str]) -> bool:
        """
        Adds vectors to the FAISS index with their corresponding IDs.
        
        Args:
            vectors: List of vectors to add
            ids: List of IDs corresponding to the vectors
            
        Returns:
            True if vectors were added successfully, False otherwise
        """
        if not self._validate_inputs(vectors, ids):
            return False
        
        try:
            # Normalize vectors for consistent similarity calculation
            normalized_vectors = [normalize_vector(v) for v in vectors]
            
            # Convert to FAISS-compatible format
            vectors_array = self._convert_to_faiss_format(normalized_vectors)
            
            # Get starting index for new vectors
            start_idx = self._next_index
            
            # Add vectors to FAISS index
            self._index.add(vectors_array)
            
            # Update ID mappings
            for i, vec_id in enumerate(ids):
                idx = start_idx + i
                self._id_to_index[vec_id] = idx
                self._index_to_id[idx] = vec_id
            
            # Update next index
            self._next_index += len(vectors)
            
            logger.info(f"Added {len(vectors)} vectors to FAISS index")
            return True
        except Exception as e:
            logger.error(f"Error adding vectors to FAISS index: {str(e)}")
            return False

    def search(self, query_vector: np.ndarray, top_k: Optional[int] = None, 
               threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Searches for similar vectors in the FAISS index.
        
        Args:
            query_vector: Vector to search for
            top_k: Number of results to return
            threshold: Similarity threshold for filtering results
            
        Returns:
            List of dictionaries containing id, vector, and similarity score
        """
        if not validate_vector_dimensions(query_vector, self._vector_dimension):
            logger.error(f"Query vector has invalid dimensions: {query_vector.shape}")
            return []
        
        # Set default values if not provided
        if top_k is None:
            top_k = vector_settings.DEFAULT_TOP_K
        
        if threshold is None:
            threshold = vector_settings.SIMILARITY_THRESHOLD
        
        try:
            # Normalize query vector
            query_vector = normalize_vector(query_vector)
            
            # Ensure query vector has correct shape and data type
            query_vector = query_vector.reshape(1, -1).astype(np.float32)
            
            # Perform similarity search
            scores, indices = self._index.search(query_vector, top_k)
            
            # Convert to list of dictionaries with IDs
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                # Skip results with index -1 (can happen if not enough vectors in the index)
                if idx == -1:
                    continue
                
                # Skip results below threshold
                if score < threshold:
                    continue
                
                # Get ID for this index
                vec_id = self._index_to_id.get(int(idx))
                if vec_id is None:
                    logger.warning(f"No ID found for index {idx}")
                    continue
                
                # Get the actual vector if possible
                vector = None
                try:
                    # Attempt to reconstruct vector from index
                    vector = self._index.reconstruct(int(idx))
                except Exception as e:
                    logger.warning(f"Could not reconstruct vector: {str(e)}")
                
                results.append({
                    "id": vec_id,
                    "score": float(score),
                    "vector": vector.tolist() if vector is not None else None,
                    "index": int(idx)
                })
            
            logger.info(f"Search found {len(results)} results for query vector")
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {str(e)}")
            return []

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Deletes vectors from the FAISS index by their IDs.
        
        Args:
            ids: List of IDs of vectors to delete
            
        Returns:
            True if vectors were deleted successfully, False otherwise
        """
        if not ids:
            logger.warning("No IDs provided for deletion")
            return False
        
        try:
            # Get internal indices for the IDs to delete
            indices_to_delete = set()
            for vec_id in ids:
                if vec_id in self._id_to_index:
                    indices_to_delete.add(self._id_to_index[vec_id])
                else:
                    logger.warning(f"ID {vec_id} not found for deletion")
            
            if not indices_to_delete:
                logger.warning("No valid IDs found for deletion")
                return False
            
            # Get indices to keep
            indices_to_keep = [i for i in range(self._next_index) if i not in indices_to_delete]
            
            # Rebuild index with only the vectors to keep
            success = self._rebuild_index(indices_to_keep)
            
            logger.info(f"Deleted {len(indices_to_delete)} vectors from FAISS index")
            return success
        except Exception as e:
            logger.error(f"Error deleting vectors from FAISS index: {str(e)}")
            return False

    def get_vector(self, id: str) -> Optional[np.ndarray]:
        """
        Retrieves a vector from the FAISS index by its ID.
        
        Args:
            id: ID of the vector to retrieve
            
        Returns:
            The vector if found, None otherwise
        """
        if id not in self._id_to_index:
            logger.warning(f"Vector ID {id} not found")
            return None
        
        try:
            # Get internal index for this ID
            idx = self._id_to_index[id]
            
            # Reconstruct vector from index
            vector = self._index.reconstruct(int(idx))
            return vector
        except Exception as e:
            logger.error(f"Error retrieving vector: {str(e)}")
            return None

    def contains(self, id: str) -> bool:
        """
        Checks if a vector ID exists in the FAISS index.
        
        Args:
            id: ID to check
            
        Returns:
            True if the vector ID exists, False otherwise
        """
        return id in self._id_to_index

    def count(self) -> int:
        """
        Returns the number of vectors in the FAISS index.
        
        Returns:
            Number of vectors in the index
        """
        return len(self._id_to_index)

    def save(self, path: Optional[str] = None) -> bool:
        """
        Saves the FAISS index and ID mappings to disk.
        
        Args:
            path: Path where to save the vector store. If None, uses the index_path.
            
        Returns:
            True if the store was saved successfully, False otherwise
        """
        # Use provided path or default
        save_path = path or self._index_path
        
        # Ensure directory exists
        if not self._ensure_directory_exists(save_path):
            return False
        
        try:
            # Save FAISS index
            faiss.write_index(self._index, f"{save_path}.faiss")
            
            # Save ID mappings
            np.save(f"{save_path}_id_to_index.npy", [self._id_to_index, self._index_to_id, self._next_index])
            
            logger.info(f"FAISS index saved to {save_path}.faiss")
            return True
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            return False

    def load(self, path: Optional[str] = None) -> bool:
        """
        Loads the FAISS index and ID mappings from disk.
        
        Args:
            path: Path from where to load the vector store. If None, uses the index_path.
            
        Returns:
            True if the store was loaded successfully, False otherwise
        """
        # Use provided path or default
        load_path = path or self._index_path
        
        # Check if index file exists
        index_file = f"{load_path}.faiss"
        if not os.path.exists(index_file):
            logger.warning(f"FAISS index file not found at {index_file}")
            return False
        
        try:
            # Load FAISS index
            self._index = faiss.read_index(index_file)
            
            # Load ID mappings
            mapping_file = f"{load_path}_id_to_index.npy"
            if os.path.exists(mapping_file):
                mappings = np.load(mapping_file, allow_pickle=True)
                self._id_to_index = mappings[0].item()
                self._index_to_id = mappings[1].item()
                self._next_index = mappings[2].item()
            else:
                logger.warning(f"ID mappings file not found at {mapping_file}")
                self._id_to_index = {}
                self._index_to_id = {}
                self._next_index = 0
            
            logger.info(f"FAISS index loaded from {index_file} with {self.count()} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            return False

    def clear(self) -> bool:
        """
        Clears all vectors from the FAISS index.
        
        Returns:
            True if the index was cleared successfully, False otherwise
        """
        try:
            # Create a new index with the same configuration
            self._index = self._create_index()
            
            # Reset ID mappings
            self._id_to_index = {}
            self._index_to_id = {}
            self._next_index = 0
            
            logger.info("FAISS index cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing FAISS index: {str(e)}")
            return False

    def _convert_to_faiss_format(self, vectors: List[np.ndarray]) -> np.ndarray:
        """
        Converts a list of vectors to the format required by FAISS.
        
        Args:
            vectors: List of vectors to convert
            
        Returns:
            Vectors in FAISS-compatible format
        """
        # Stack vectors into a single numpy array
        vectors_array = np.vstack(vectors)
        
        # Ensure array has correct data type (float32)
        vectors_array = vectors_array.astype(np.float32)
        
        return vectors_array

    def _rebuild_index(self, indices_to_keep: List[int]) -> bool:
        """
        Rebuilds the FAISS index after vector deletion.
        
        Args:
            indices_to_keep: List of indices to keep in the new index
            
        Returns:
            True if the index was rebuilt successfully, False otherwise
        """
        try:
            # Create a new index with the same configuration
            new_index = self._create_index()
            
            # Extract vectors to keep from current index
            vectors_to_keep = []
            for idx in indices_to_keep:
                try:
                    vector = self._index.reconstruct(int(idx))
                    vectors_to_keep.append(vector)
                except Exception as e:
                    logger.warning(f"Could not reconstruct vector at index {idx}: {str(e)}")
            
            if vectors_to_keep:
                # Convert to FAISS-compatible format
                vectors_array = np.vstack(vectors_to_keep).astype(np.float32)
                
                # Add vectors to new index
                new_index.add(vectors_array)
            
            # Update ID mappings
            new_id_to_index = {}
            new_index_to_id = {}
            for new_idx, old_idx in enumerate(indices_to_keep):
                vec_id = self._index_to_id.get(old_idx)
                if vec_id is not None:
                    new_id_to_index[vec_id] = new_idx
                    new_index_to_id[new_idx] = vec_id
            
            # Replace old index and mappings with new ones
            self._index = new_index
            self._id_to_index = new_id_to_index
            self._index_to_id = new_index_to_id
            self._next_index = len(indices_to_keep)
            
            return True
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {str(e)}")
            return False