"""
Service module that implements vector similarity search functionality for the Document Management and AI Chatbot System.

This module provides methods to search for documents similar to a query text or vector,
retrieve relevant document chunks, and handle both synchronous and asynchronous search operations.
"""

import numpy as np  # version 1.24.0+
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Union

from sqlalchemy.orm import Session  # version 2.0.0+
from sqlalchemy.ext.asyncio import AsyncSession  # version 2.0.0+

from ..core.settings import vector_settings, DEFAULT_TOP_K, SIMILARITY_THRESHOLD
from ..vector_store.faiss_store import FAISSStore
from ..vector_store.base import VectorStore
from .embedding_service import generate_embedding, async_generate_embedding
from ..crud.crud_document_chunk import document_chunk
from ..models.document_chunk import DocumentChunk
from ..utils.vector_utils import calculate_similarity, normalize_vector

# Configure logger
logger = logging.getLogger(__name__)

# Global vector store singleton
_vector_store = None


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


def search_by_vector(
    query_vector: np.ndarray, 
    db: Session, 
    top_k: Optional[int] = None, 
    threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Searches for document chunks similar to the provided vector embedding.
    
    Args:
        query_vector: Vector embedding to search for
        db: Database session
        top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
        threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
        
    Returns:
        List of document chunks with similarity scores
    """
    # Normalize the query vector
    query_vector = normalize_vector(query_vector)
    
    # Use default values if not provided
    if top_k is None:
        top_k = DEFAULT_TOP_K
    
    if threshold is None:
        threshold = SIMILARITY_THRESHOLD
    
    start_time = time.time()
    
    try:
        # Get the vector store
        vector_store = get_vector_store()
        
        # Perform similarity search
        vector_results = vector_store.search(query_vector, top_k, threshold)
        
        # Retrieve document chunks for the search results
        document_chunks = []
        for result in vector_results:
            chunk = document_chunk.get_by_embedding_id(db, result["id"])
            if chunk:
                document_chunks.append(chunk)
        
        # Format the results with document content and metadata
        formatted_results = format_search_results(vector_results, document_chunks)
        
        search_time = time.time() - start_time
        logger.info(f"Vector search completed in {search_time:.3f}s, found {len(formatted_results)} results")
        
        return formatted_results
    except Exception as e:
        logger.error(f"Error in search_by_vector: {str(e)}")
        return []


def search_by_text(
    query_text: str, 
    db: Session, 
    top_k: Optional[int] = None, 
    threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Searches for document chunks similar to the provided query text.
    
    Args:
        query_text: Query text to search for
        db: Database session
        top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
        threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
        
    Returns:
        List of document chunks with similarity scores
    """
    try:
        # Generate embedding for the query text
        query_vector = generate_embedding(query_text)
        
        # Search for similar document chunks
        results = search_by_vector(query_vector, db, top_k, threshold)
        
        return results
    except Exception as e:
        logger.error(f"Error in search_by_text: {str(e)}")
        return []


async def async_search_by_vector(
    query_vector: np.ndarray, 
    db: AsyncSession, 
    top_k: Optional[int] = None, 
    threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Asynchronously searches for document chunks similar to the provided vector embedding.
    
    Args:
        query_vector: Vector embedding to search for
        db: Async database session
        top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
        threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
        
    Returns:
        List of document chunks with similarity scores
    """
    # Normalize the query vector
    query_vector = normalize_vector(query_vector)
    
    # Use default values if not provided
    if top_k is None:
        top_k = DEFAULT_TOP_K
    
    if threshold is None:
        threshold = SIMILARITY_THRESHOLD
    
    start_time = time.time()
    
    try:
        # Get the vector store
        vector_store = get_vector_store()
        
        # Perform similarity search (FAISS operations are CPU-bound, so we run in thread pool)
        vector_results = await asyncio.to_thread(
            vector_store.search, query_vector, top_k, threshold
        )
        
        # Retrieve document chunks for the search results
        document_chunks = []
        for result in vector_results:
            chunk = await document_chunk.get_by_embedding_id_async(db, result["id"])
            if chunk:
                document_chunks.append(chunk)
        
        # Format the results with document content and metadata
        formatted_results = format_search_results(vector_results, document_chunks)
        
        search_time = time.time() - start_time
        logger.info(f"Async vector search completed in {search_time:.3f}s, found {len(formatted_results)} results")
        
        return formatted_results
    except Exception as e:
        logger.error(f"Error in async_search_by_vector: {str(e)}")
        return []


async def async_search_by_text(
    query_text: str, 
    db: AsyncSession, 
    top_k: Optional[int] = None, 
    threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Asynchronously searches for document chunks similar to the provided query text.
    
    Args:
        query_text: Query text to search for
        db: Async database session
        top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
        threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
        
    Returns:
        List of document chunks with similarity scores
    """
    try:
        # Generate embedding for the query text asynchronously
        query_vector = await async_generate_embedding(query_text)
        
        # Search for similar document chunks
        results = await async_search_by_vector(query_vector, db, top_k, threshold)
        
        return results
    except Exception as e:
        logger.error(f"Error in async_search_by_text: {str(e)}")
        return []


def format_search_results(
    vector_results: List[Dict[str, Any]], 
    document_chunks: List[DocumentChunk]
) -> List[Dict[str, Any]]:
    """
    Formats vector search results with document chunk content and metadata.
    
    Args:
        vector_results: Results from vector similarity search with embedding IDs and scores
        document_chunks: Document chunks corresponding to the search results
        
    Returns:
        Formatted search results with document content and metadata
    """
    # Create a map of embedding ID to document chunk for efficient lookup
    chunk_map = {chunk.embedding_id: chunk for chunk in document_chunks}
    
    # Format the results
    formatted_results = []
    for result in vector_results:
        embedding_id = result["id"]
        if embedding_id in chunk_map:
            chunk = chunk_map[embedding_id]
            formatted_results.append({
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "content": chunk.content,
                "similarity_score": result["score"],
                "chunk_index": chunk.chunk_index
            })
    
    return formatted_results


class VectorSearchService:
    """
    Service class that provides methods for vector similarity search operations.
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initializes the VectorSearchService with a vector store.
        
        Args:
            vector_store: Optional vector store instance, if not provided, the default will be used
        """
        self._vector_store = vector_store or get_vector_store()
        logger.info("Initialized VectorSearchService")
    
    def search(
        self, 
        query_text: str, 
        db: Session, 
        top_k: Optional[int] = None, 
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches for document chunks similar to the provided query text.
        
        Args:
            query_text: Query text to search for
            db: Database session
            top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
            threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
            
        Returns:
            List of document chunks with similarity scores
        """
        if not query_text or query_text.strip() == "":
            logger.warning("Empty query text provided to VectorSearchService.search")
            return []
        
        # Use default values if not provided
        if top_k is None:
            top_k = DEFAULT_TOP_K
        
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        start_time = time.time()
        
        try:
            # Generate embedding for the query text
            query_vector = generate_embedding(query_text)
            
            # Search for similar document chunks
            results = search_by_vector(query_vector, db, top_k, threshold)
            
            search_time = time.time() - start_time
            logger.info(f"Search for '{query_text[:50]}...' completed in {search_time:.3f}s, found {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Error in VectorSearchService.search: {str(e)}")
            return []
    
    async def async_search(
        self, 
        query_text: str, 
        db: AsyncSession, 
        top_k: Optional[int] = None, 
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously searches for document chunks similar to the provided query text.
        
        Args:
            query_text: Query text to search for
            db: Async database session
            top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
            threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
            
        Returns:
            List of document chunks with similarity scores
        """
        if not query_text or query_text.strip() == "":
            logger.warning("Empty query text provided to VectorSearchService.async_search")
            return []
        
        # Use default values if not provided
        if top_k is None:
            top_k = DEFAULT_TOP_K
        
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        start_time = time.time()
        
        try:
            # Generate embedding for the query text asynchronously
            query_vector = await async_generate_embedding(query_text)
            
            # Search for similar document chunks
            results = await async_search_by_vector(query_vector, db, top_k, threshold)
            
            search_time = time.time() - start_time
            logger.info(f"Async search for '{query_text[:50]}...' completed in {search_time:.3f}s, found {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Error in VectorSearchService.async_search: {str(e)}")
            return []
    
    def search_by_vector(
        self, 
        query_vector: np.ndarray, 
        db: Session, 
        top_k: Optional[int] = None, 
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches for document chunks similar to the provided vector embedding.
        
        Args:
            query_vector: Vector embedding to search for
            db: Database session
            top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
            threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
            
        Returns:
            List of document chunks with similarity scores
        """
        return search_by_vector(query_vector, db, top_k, threshold)
    
    async def async_search_by_vector(
        self, 
        query_vector: np.ndarray, 
        db: AsyncSession, 
        top_k: Optional[int] = None, 
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously searches for document chunks similar to the provided vector embedding.
        
        Args:
            query_vector: Vector embedding to search for
            db: Async database session
            top_k: Number of results to return, defaults to vector_settings.DEFAULT_TOP_K
            threshold: Similarity threshold for filtering results, defaults to vector_settings.SIMILARITY_THRESHOLD
            
        Returns:
            List of document chunks with similarity scores
        """
        return await async_search_by_vector(query_vector, db, top_k, threshold)
    
    def rerank_results(self, results: List[Dict[str, Any]], query_text: str) -> List[Dict[str, Any]]:
        """
        Reranks search results based on additional criteria.
        
        Args:
            results: Search results to rerank
            query_text: Original query text for context-aware reranking
            
        Returns:
            Reranked search results
        """
        if not results:
            return []
        
        try:
            # This is a simple implementation that could be extended with more sophisticated reranking
            # For example, incorporating BM25 scores, recency, document popularity, etc.
            
            # Generate query embedding for semantic comparison
            query_vector = generate_embedding(query_text)
            
            # For each result, we could compute additional ranking signals
            for result in results:
                # Example: boost exact matches in content
                exact_match_boost = 0.0
                if query_text.lower() in result["content"].lower():
                    exact_match_boost = 0.1
                
                # Combine the original similarity score with additional signals
                result["combined_score"] = result["similarity_score"] + exact_match_boost
            
            # Sort by the combined score
            reranked_results = sorted(results, key=lambda x: x.get("combined_score", 0), reverse=True)
            
            # Clean up temporary scoring fields
            for result in reranked_results:
                if "combined_score" in result:
                    del result["combined_score"]
            
            return reranked_results
        except Exception as e:
            logger.error(f"Error in rerank_results: {str(e)}")
            # If reranking fails, return original results
            return results
    
    def filter_results(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filters search results based on metadata criteria.
        
        Args:
            results: Search results to filter
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered search results
        """
        if not results or not filters:
            return results
        
        try:
            filtered_results = results.copy()
            
            # Apply document_id filter if present
            if "document_id" in filters and filters["document_id"]:
                filtered_results = [
                    r for r in filtered_results 
                    if str(r.get("document_id")) == str(filters["document_id"])
                ]
            
            # Apply content filter if present
            if "content_contains" in filters and filters["content_contains"]:
                content_filter = filters["content_contains"].lower()
                filtered_results = [
                    r for r in filtered_results 
                    if content_filter in r.get("content", "").lower()
                ]
            
            # Apply minimum similarity score filter if present
            if "min_score" in filters and filters["min_score"] is not None:
                min_score = float(filters["min_score"])
                filtered_results = [
                    r for r in filtered_results 
                    if r.get("similarity_score", 0) >= min_score
                ]
            
            return filtered_results
        except Exception as e:
            logger.error(f"Error in filter_results: {str(e)}")
            # If filtering fails, return original results
            return results