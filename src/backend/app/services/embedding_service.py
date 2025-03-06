"""
Service module that handles the generation and management of vector embeddings for document text.

This module provides functionality to convert document text into vector embeddings using
Sentence Transformers, store them in the FAISS vector database, and manage the lifecycle
of embeddings.
"""

import numpy as np  # numpy 1.24.0+
from sentence_transformers import SentenceTransformer  # sentence-transformers 2.2.2+
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union

from ..core.config import vector_settings, get_vector_settings
from ..utils.vector_utils import (
    normalize_vector,
    validate_vector_dimensions,
    generate_embedding_id,
    serialize_vector,
    deserialize_vector
)
from ..vector_store.faiss_store import FAISSStore
from ..models.document_chunk import DocumentChunk

# Configure logger
logger = logging.getLogger(__name__)

# Global variables to store instances for reuse
_embedding_model = None
_vector_store = None


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the Sentence Transformers embedding model, initializing it if necessary.
    
    Returns:
        SentenceTransformer: Initialized embedding model
    """
    global _embedding_model
    
    if _embedding_model is None:
        # Initialize the embedding model with a model that produces embeddings matching our vector dimension
        model_name = 'all-MiniLM-L6-v2'  # Produces 384-dimensional embeddings by default
        
        # Check if we need a different model based on configured dimension
        if vector_settings.VECTOR_DIMENSION == 768:
            model_name = 'all-mpnet-base-v2'  # 768-dimensional embeddings
        
        _embedding_model = SentenceTransformer(model_name)
        logger.info(f"Initialized embedding model: {model_name} for dimension {vector_settings.VECTOR_DIMENSION}")
    
    return _embedding_model


def get_vector_store() -> FAISSStore:
    """
    Returns the FAISS vector store, initializing it if necessary.
    
    Returns:
        FAISSStore: Initialized FAISS vector store
    """
    global _vector_store
    
    if _vector_store is None:
        # Initialize the vector store
        _vector_store = FAISSStore(
            index_path=vector_settings.VECTOR_INDEX_PATH,
            vector_dimension=vector_settings.VECTOR_DIMENSION
        )
        
        # Attempt to load existing index from disk
        try:
            _vector_store.load()
            logger.info(f"Loaded existing vector store with {_vector_store.count()} vectors")
        except Exception as e:
            logger.warning(f"Failed to load existing vector store, creating new one: {str(e)}")
        
        logger.info(f"Vector store ready with {_vector_store.count()} vectors")
    
    return _vector_store


def generate_embedding(text: str) -> np.ndarray:
    """
    Generates a vector embedding for a text string.
    
    Args:
        text (str): Text to generate embedding for
        
    Returns:
        np.ndarray: Vector embedding of the text
    """
    # Get the embedding model
    model = get_embedding_model()
    
    try:
        # Generate embedding vector
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        
        # Ensure the vector is normalized and has correct dimensions
        embedding = normalize_vector(embedding)
        
        if not validate_vector_dimensions(embedding):
            logger.error(f"Generated embedding has invalid dimensions: {embedding.shape}, expected {vector_settings.VECTOR_DIMENSION}")
            raise ValueError(f"Invalid embedding dimensions: {embedding.shape}")
        
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise


def generate_embeddings_batch(texts: List[str]) -> List[np.ndarray]:
    """
    Generates vector embeddings for a batch of text strings.
    
    Args:
        texts (List[str]): List of texts to generate embeddings for
        
    Returns:
        List[np.ndarray]: List of vector embeddings
    """
    if not texts:
        logger.warning("Empty texts list provided to generate_embeddings_batch")
        return []
        
    # Get the embedding model
    model = get_embedding_model()
    
    try:
        # Generate embeddings for all texts in batch
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Ensure embeddings is a list of vectors
        if len(texts) == 1:
            embeddings = [embeddings]
        
        # Normalize each vector and validate dimensions
        normalized_embeddings = []
        for embedding in embeddings:
            embedding = normalize_vector(embedding)
            
            if not validate_vector_dimensions(embedding):
                logger.error(f"Generated embedding has invalid dimensions: {embedding.shape}")
                raise ValueError(f"Invalid embedding dimensions: {embedding.shape}")
            
            normalized_embeddings.append(embedding)
        
        return normalized_embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings batch: {str(e)}")
        raise


async def async_generate_embedding(text: str) -> np.ndarray:
    """
    Asynchronously generates a vector embedding for a text string.
    
    Args:
        text (str): Text to generate embedding for
        
    Returns:
        np.ndarray: Vector embedding of the text
    """
    try:
        # Run generate_embedding in a thread pool
        embedding = await asyncio.to_thread(generate_embedding, text)
        return embedding
    except Exception as e:
        logger.error(f"Error in async_generate_embedding: {str(e)}")
        raise


async def async_generate_embeddings_batch(texts: List[str]) -> List[np.ndarray]:
    """
    Asynchronously generates vector embeddings for a batch of text strings.
    
    Args:
        texts (List[str]): List of texts to generate embeddings for
        
    Returns:
        List[np.ndarray]: List of vector embeddings
    """
    try:
        # Run generate_embeddings_batch in a thread pool
        embeddings = await asyncio.to_thread(generate_embeddings_batch, texts)
        return embeddings
    except Exception as e:
        logger.error(f"Error in async_generate_embeddings_batch: {str(e)}")
        raise


def store_embedding(embedding: np.ndarray) -> str:
    """
    Stores a vector embedding in the FAISS index and returns its ID.
    
    Args:
        embedding (np.ndarray): Vector embedding to store
        
    Returns:
        str: Unique embedding ID
    """
    # Generate a unique embedding ID
    embedding_id = generate_embedding_id()
    
    # Get the vector store
    vector_store = get_vector_store()
    
    try:
        # Add the embedding to the vector store
        success = vector_store.add_vectors([embedding], [embedding_id])
        
        if not success:
            logger.error("Failed to store embedding in vector store")
            raise ValueError("Failed to store embedding")
        
        # Save the updated vector store to disk
        vector_store.save()
        logger.debug(f"Stored embedding with ID: {embedding_id}")
        
        return embedding_id
    except Exception as e:
        logger.error(f"Error storing embedding: {str(e)}")
        raise


def store_embeddings_batch(embeddings: List[np.ndarray]) -> List[str]:
    """
    Stores multiple vector embeddings in the FAISS index and returns their IDs.
    
    Args:
        embeddings (List[np.ndarray]): List of vector embeddings to store
        
    Returns:
        List[str]: List of unique embedding IDs
    """
    if not embeddings:
        logger.warning("Empty embeddings list provided to store_embeddings_batch")
        return []
        
    # Generate unique embedding IDs for each embedding
    embedding_ids = [generate_embedding_id() for _ in range(len(embeddings))]
    
    # Get the vector store
    vector_store = get_vector_store()
    
    try:
        # Add the embeddings to the vector store
        success = vector_store.add_vectors(embeddings, embedding_ids)
        
        if not success:
            logger.error("Failed to store embeddings batch in vector store")
            raise ValueError("Failed to store embeddings batch")
        
        # Save the updated vector store to disk
        vector_store.save()
        logger.debug(f"Stored {len(embeddings)} embeddings in batch")
        
        return embedding_ids
    except Exception as e:
        logger.error(f"Error storing embeddings batch: {str(e)}")
        raise


def process_document_chunk(chunk: DocumentChunk) -> str:
    """
    Processes a document chunk by generating and storing its embedding.
    
    Args:
        chunk (DocumentChunk): Document chunk to process
        
    Returns:
        str: Embedding ID for the processed chunk
    """
    try:
        # Extract text content from the document chunk
        text = chunk.content
        
        # Generate embedding for the text
        embedding = generate_embedding(text)
        
        # Store the embedding
        embedding_id = store_embedding(embedding)
        
        # Update the document chunk with the embedding ID
        chunk.update_embedding_id(embedding_id)
        logger.info(f"Processed document chunk {chunk.id}, embedding ID: {embedding_id}")
        
        return embedding_id
    except Exception as e:
        logger.error(f"Error processing document chunk: {str(e)}")
        raise


def process_document_chunks(chunks: List[DocumentChunk]) -> List[str]:
    """
    Processes multiple document chunks by generating and storing their embeddings.
    
    Args:
        chunks (List[DocumentChunk]): List of document chunks to process
        
    Returns:
        List[str]: List of embedding IDs for the processed chunks
    """
    if not chunks:
        logger.warning("Empty chunks list provided to process_document_chunks")
        return []
        
    try:
        # Extract text content from each document chunk
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings for all texts
        embeddings = generate_embeddings_batch(texts)
        
        # Store the embeddings
        embedding_ids = store_embeddings_batch(embeddings)
        
        # Update each document chunk with its corresponding embedding ID
        for chunk, embedding_id in zip(chunks, embedding_ids):
            chunk.update_embedding_id(embedding_id)
        
        logger.info(f"Processed {len(chunks)} document chunks")
        return embedding_ids
    except Exception as e:
        logger.error(f"Error processing document chunks: {str(e)}")
        raise


async def async_process_document_chunks(chunks: List[DocumentChunk]) -> List[str]:
    """
    Asynchronously processes multiple document chunks by generating and storing their embeddings.
    
    Args:
        chunks (List[DocumentChunk]): List of document chunks to process
        
    Returns:
        List[str]: List of embedding IDs for the processed chunks
    """
    if not chunks:
        logger.warning("Empty chunks list provided to async_process_document_chunks")
        return []
        
    try:
        # Extract text content from each document chunk
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings asynchronously
        embeddings = await async_generate_embeddings_batch(texts)
        
        # Store the embeddings
        embedding_ids = store_embeddings_batch(embeddings)
        
        # Update each document chunk with its corresponding embedding ID
        for chunk, embedding_id in zip(chunks, embedding_ids):
            chunk.update_embedding_id(embedding_id)
        
        logger.info(f"Asynchronously processed {len(chunks)} document chunks")
        return embedding_ids
    except Exception as e:
        logger.error(f"Error in async_process_document_chunks: {str(e)}")
        raise


def search_similar(query_vector: np.ndarray, top_k: Optional[int] = None, 
                  threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Searches for vectors similar to the query vector.
    
    Args:
        query_vector (np.ndarray): Query vector
        top_k (Optional[int]): Number of results to return
        threshold (Optional[float]): Similarity threshold for filtering results
        
    Returns:
        List[Dict[str, Any]]: List of similar vectors with their IDs and similarity scores
    """
    # Get the vector store
    vector_store = get_vector_store()
    
    # Use default values from settings if not provided
    if top_k is None:
        top_k = vector_settings.DEFAULT_TOP_K
    
    if threshold is None:
        threshold = vector_settings.SIMILARITY_THRESHOLD
    
    try:
        # Perform similarity search in the vector store
        results = vector_store.search(query_vector, top_k, threshold)
        logger.debug(f"Search found {len(results)} results for query vector")
        return results
    except Exception as e:
        logger.error(f"Error in search_similar: {str(e)}")
        raise


def search_similar_by_text(query_text: str, top_k: Optional[int] = None,
                         threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Searches for vectors similar to the embedding of the query text.
    
    Args:
        query_text (str): Query text
        top_k (Optional[int]): Number of results to return
        threshold (Optional[float]): Similarity threshold for filtering results
        
    Returns:
        List[Dict[str, Any]]: List of similar vectors with their IDs and similarity scores
    """
    try:
        # Generate embedding for the query text
        query_vector = generate_embedding(query_text)
        
        # Search for similar vectors
        results = search_similar(query_vector, top_k, threshold)
        logger.info(f"Text search for '{query_text[:50]}...' found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error in search_similar_by_text: {str(e)}")
        raise


async def async_search_similar_by_text(query_text: str, top_k: Optional[int] = None,
                                    threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """
    Asynchronously searches for vectors similar to the embedding of the query text.
    
    Args:
        query_text (str): Query text
        top_k (Optional[int]): Number of results to return
        threshold (Optional[float]): Similarity threshold for filtering results
        
    Returns:
        List[Dict[str, Any]]: List of similar vectors with their IDs and similarity scores
    """
    try:
        # Generate embedding asynchronously
        query_vector = await async_generate_embedding(query_text)
        
        # Search for similar vectors
        results = search_similar(query_vector, top_k, threshold)
        logger.info(f"Async text search for '{query_text[:50]}...' found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error in async_search_similar_by_text: {str(e)}")
        raise


def delete_embedding(embedding_id: str) -> bool:
    """
    Deletes a vector embedding from the FAISS index by its ID.
    
    Args:
        embedding_id (str): ID of the embedding to delete
        
    Returns:
        bool: True if the embedding was deleted successfully, False otherwise
    """
    # Get the vector store
    vector_store = get_vector_store()
    
    try:
        # Delete the embedding from the vector store
        success = vector_store.delete_vectors([embedding_id])
        
        if success:
            # Save the updated vector store to disk
            vector_store.save()
            logger.info(f"Successfully deleted embedding: {embedding_id}")
        else:
            logger.warning(f"Failed to delete embedding: {embedding_id}")
        
        return success
    except Exception as e:
        logger.error(f"Error deleting embedding: {str(e)}")
        return False


def delete_embeddings_batch(embedding_ids: List[str]) -> bool:
    """
    Deletes multiple vector embeddings from the FAISS index by their IDs.
    
    Args:
        embedding_ids (List[str]): List of embedding IDs to delete
        
    Returns:
        bool: True if all embeddings were deleted successfully, False otherwise
    """
    if not embedding_ids:
        logger.warning("Empty embedding_ids list provided to delete_embeddings_batch")
        return True
        
    # Get the vector store
    vector_store = get_vector_store()
    
    try:
        # Delete the embeddings from the vector store
        success = vector_store.delete_vectors(embedding_ids)
        
        if success:
            # Save the updated vector store to disk
            vector_store.save()
            logger.info(f"Successfully deleted {len(embedding_ids)} embeddings")
        else:
            logger.warning(f"Failed to delete embeddings batch of size {len(embedding_ids)}")
        
        return success
    except Exception as e:
        logger.error(f"Error deleting embeddings batch: {str(e)}")
        return False


def rebuild_index() -> bool:
    """
    Rebuilds the FAISS index from scratch.
    
    Returns:
        bool: True if the index was rebuilt successfully, False otherwise
    """
    # Get the vector store
    vector_store = get_vector_store()
    
    try:
        # Clear the vector store
        success = vector_store.clear()
        
        if success:
            # Save the empty vector store to disk
            vector_store.save()
            logger.info("Successfully rebuilt FAISS index")
        else:
            logger.warning("Failed to rebuild FAISS index")
        
        return success
    except Exception as e:
        logger.error(f"Error rebuilding FAISS index: {str(e)}")
        return False


class EmbeddingService:
    """
    Service class that provides methods for generating and managing vector embeddings.
    
    This class encapsulates the functionality to:
    - Generate vector embeddings for text using Sentence Transformers
    - Store and retrieve embeddings from the FAISS vector database
    - Search for similar vectors and text
    - Process document chunks for indexing and search
    """
    
    def __init__(self):
        """
        Initializes the EmbeddingService with embedding model and vector store.
        """
        # Initialize model and vector store
        self._model = get_embedding_model()
        self._vector_store = get_vector_store()
        logger.info("Initialized EmbeddingService")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generates a vector embedding for a text string.
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            np.ndarray: Vector embedding of the text
        """
        try:
            # Generate embedding using the embedding model
            embedding = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            
            # Normalize the vector and validate dimensions
            embedding = normalize_vector(embedding)
            
            if not validate_vector_dimensions(embedding):
                logger.error(f"Generated embedding has invalid dimensions: {embedding.shape}")
                raise ValueError(f"Invalid embedding dimensions: {embedding.shape}")
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generates vector embeddings for a batch of text strings.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            
        Returns:
            List[np.ndarray]: List of vector embeddings
        """
        if not texts:
            logger.warning("Empty texts list provided to EmbeddingService.generate_embeddings_batch")
            return []
            
        try:
            # Generate embeddings for all texts in batch
            embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            
            # Ensure embeddings is a list of vectors
            if len(texts) == 1:
                embeddings = [embeddings]
            
            # Normalize each vector and validate dimensions
            normalized_embeddings = []
            for embedding in embeddings:
                embedding = normalize_vector(embedding)
                
                if not validate_vector_dimensions(embedding):
                    logger.error(f"Generated embedding has invalid dimensions: {embedding.shape}")
                    raise ValueError(f"Invalid embedding dimensions: {embedding.shape}")
                
                normalized_embeddings.append(embedding)
            
            return normalized_embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {str(e)}")
            raise
    
    def store_embedding(self, embedding: np.ndarray) -> str:
        """
        Stores a vector embedding in the FAISS index and returns its ID.
        
        Args:
            embedding (np.ndarray): Vector embedding to store
            
        Returns:
            str: Unique embedding ID
        """
        # Generate a unique embedding ID
        embedding_id = generate_embedding_id()
        
        try:
            # Add the embedding to the vector store
            success = self._vector_store.add_vectors([embedding], [embedding_id])
            
            if not success:
                logger.error("Failed to store embedding in vector store")
                raise ValueError("Failed to store embedding")
            
            # Save the updated vector store to disk
            self._vector_store.save()
            
            return embedding_id
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            raise
    
    def store_embeddings_batch(self, embeddings: List[np.ndarray]) -> List[str]:
        """
        Stores multiple vector embeddings in the FAISS index and returns their IDs.
        
        Args:
            embeddings (List[np.ndarray]): List of vector embeddings to store
            
        Returns:
            List[str]: List of unique embedding IDs
        """
        if not embeddings:
            logger.warning("Empty embeddings list provided to EmbeddingService.store_embeddings_batch")
            return []
            
        # Generate unique embedding IDs for each embedding
        embedding_ids = [generate_embedding_id() for _ in range(len(embeddings))]
        
        try:
            # Add the embeddings to the vector store
            success = self._vector_store.add_vectors(embeddings, embedding_ids)
            
            if not success:
                logger.error("Failed to store embeddings batch in vector store")
                raise ValueError("Failed to store embeddings batch")
            
            # Save the updated vector store to disk
            self._vector_store.save()
            
            return embedding_ids
        except Exception as e:
            logger.error(f"Error storing embeddings batch: {str(e)}")
            raise
    
    def process_document_chunk(self, chunk: DocumentChunk) -> str:
        """
        Processes a document chunk by generating and storing its embedding.
        
        Args:
            chunk (DocumentChunk): Document chunk to process
            
        Returns:
            str: Embedding ID for the processed chunk
        """
        try:
            # Extract text content from the document chunk
            text = chunk.content
            
            # Generate embedding for the text
            embedding = self.generate_embedding(text)
            
            # Store the embedding
            embedding_id = self.store_embedding(embedding)
            
            # Update the document chunk with the embedding ID
            chunk.update_embedding_id(embedding_id)
            
            return embedding_id
        except Exception as e:
            logger.error(f"Error processing document chunk: {str(e)}")
            raise
    
    def process_document_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """
        Processes multiple document chunks by generating and storing their embeddings.
        
        Args:
            chunks (List[DocumentChunk]): List of document chunks to process
            
        Returns:
            List[str]: List of embedding IDs for the processed chunks
        """
        if not chunks:
            logger.warning("Empty chunks list provided to EmbeddingService.process_document_chunks")
            return []
            
        try:
            # Extract text content from each document chunk
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings for all texts
            embeddings = self.generate_embeddings_batch(texts)
            
            # Store the embeddings
            embedding_ids = self.store_embeddings_batch(embeddings)
            
            # Update each document chunk with its corresponding embedding ID
            for chunk, embedding_id in zip(chunks, embedding_ids):
                chunk.update_embedding_id(embedding_id)
            
            return embedding_ids
        except Exception as e:
            logger.error(f"Error processing document chunks: {str(e)}")
            raise
    
    def search_similar(self, query_vector: np.ndarray, top_k: Optional[int] = None, 
                      threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Searches for vectors similar to the query vector.
        
        Args:
            query_vector (np.ndarray): Query vector
            top_k (Optional[int]): Number of results to return
            threshold (Optional[float]): Similarity threshold for filtering results
            
        Returns:
            List[Dict[str, Any]]: List of similar vectors with their IDs and similarity scores
        """
        # Use default values from settings if not provided
        if top_k is None:
            top_k = vector_settings.DEFAULT_TOP_K
        
        if threshold is None:
            threshold = vector_settings.SIMILARITY_THRESHOLD
        
        try:
            # Perform similarity search in the vector store
            results = self._vector_store.search(query_vector, top_k, threshold)
            return results
        except Exception as e:
            logger.error(f"Error in search_similar: {str(e)}")
            raise
    
    def search_similar_by_text(self, query_text: str, top_k: Optional[int] = None,
                             threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Searches for vectors similar to the embedding of the query text.
        
        Args:
            query_text (str): Query text
            top_k (Optional[int]): Number of results to return
            threshold (Optional[float]): Similarity threshold for filtering results
            
        Returns:
            List[Dict[str, Any]]: List of similar vectors with their IDs and similarity scores
        """
        try:
            # Generate embedding for the query text
            query_vector = self.generate_embedding(query_text)
            
            # Search for similar vectors
            results = self.search_similar(query_vector, top_k, threshold)
            return results
        except Exception as e:
            logger.error(f"Error in search_similar_by_text: {str(e)}")
            raise
    
    def delete_embedding(self, embedding_id: str) -> bool:
        """
        Deletes a vector embedding from the FAISS index by its ID.
        
        Args:
            embedding_id (str): ID of the embedding to delete
            
        Returns:
            bool: True if the embedding was deleted successfully, False otherwise
        """
        try:
            # Delete the embedding from the vector store
            success = self._vector_store.delete_vectors([embedding_id])
            
            if success:
                # Save the updated vector store to disk
                self._vector_store.save()
            else:
                logger.warning(f"Failed to delete embedding: {embedding_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting embedding: {str(e)}")
            return False
    
    def delete_embeddings_batch(self, embedding_ids: List[str]) -> bool:
        """
        Deletes multiple vector embeddings from the FAISS index by their IDs.
        
        Args:
            embedding_ids (List[str]): List of embedding IDs to delete
            
        Returns:
            bool: True if all embeddings were deleted successfully, False otherwise
        """
        if not embedding_ids:
            logger.warning("Empty embedding_ids list provided to EmbeddingService.delete_embeddings_batch")
            return True
            
        try:
            # Delete the embeddings from the vector store
            success = self._vector_store.delete_vectors(embedding_ids)
            
            if success:
                # Save the updated vector store to disk
                self._vector_store.save()
            else:
                logger.warning(f"Failed to delete embeddings batch: {len(embedding_ids)} embeddings")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting embeddings batch: {str(e)}")
            return False
    
    def rebuild_index(self) -> bool:
        """
        Rebuilds the FAISS index from scratch.
        
        Returns:
            bool: True if the index was rebuilt successfully, False otherwise
        """
        try:
            # Clear the vector store
            success = self._vector_store.clear()
            
            if success:
                # Save the empty vector store to disk
                self._vector_store.save()
                logger.info("Successfully rebuilt FAISS index")
            else:
                logger.warning("Failed to rebuild FAISS index")
            
            return success
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {str(e)}")
            return False