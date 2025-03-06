"""
Vector Store Module for the Document Management and AI Chatbot System

This module provides a unified interface for vector storage and retrieval operations,
essential for the system's semantic search capabilities. It implements efficient storage
and similarity search of document vector embeddings using FAISS (Facebook AI Similarity Search).

The module exposes:
- VectorStore: Abstract base class defining the interface for vector operations
- FAISSStore: Concrete implementation using FAISS (version 1.7.4+) for efficient similarity search

Core operations supported:
- Vector addition and storage
- Similarity search with customizable parameters
- Vector deletion and management
- Persistence (save/load) capabilities
- Index statistics and vector retrieval

This vector store implementation addresses the requirements for vector storage (F-001-RQ-003)
and vector search (F-101-RQ-002) as specified in the system requirements.
"""

from .base import VectorStore
from .faiss_store import FAISSStore

# Export classes for type hinting and direct import
__all__ = ["VectorStore", "FAISSStore"]