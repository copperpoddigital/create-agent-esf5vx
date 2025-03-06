"""
Initialization module for the services package that exports all service classes and functions from the various service modules. This module provides a centralized access point for all service components used in the Document Management and AI Chatbot System.
"""

# Authentication service functions
from .auth_service import (  # version 0.95.0+
    authenticate_user,
    authenticate_user_async,
    create_user_tokens,
    create_user_tokens_async,
    refresh_access_token,
    refresh_access_token_async,
    get_user_from_token,
    get_user_from_token_async,
)

# File storage service class
from .file_storage import FileStorage  # version 0.95.0+

# Embedding service class and functions
from .embedding_service import (  # sentence-transformers 2.2.2+
    EmbeddingService,
    generate_embedding,
    async_generate_embedding,
    process_document_chunks,
    async_process_document_chunks,
)

# Vector search service class and functions
from .vector_search import (  # faiss 1.7.4+
    VectorSearchService,
    search_by_text,
    async_search_by_text,
)

# Document processor service class and functions
from .document_processor import (  # PyMuPDF 1.21.0+
    DocumentProcessor,
    process_document,
    async_process_document,
)

# LLM service class and functions
from .llm_service import (  # openai 1.0.0+
    LLMService,
    generate_response,
    async_generate_response,
    create_query_response,
    async_create_query_response,
)

# Feedback processor service class and functions
from .feedback_processor import (  # Ray RLlib 2.5.0+
    FeedbackProcessor,
    process_feedback_batch,
    get_model_parameters,
)

__all__ = [
    "authenticate_user",
    "authenticate_user_async",
    "create_user_tokens",
    "create_user_tokens_async",
    "refresh_access_token",
    "refresh_access_token_async",
    "get_user_from_token",
    "get_user_from_token_async",
    "FileStorage",
    "EmbeddingService",
    "generate_embedding",
    "async_generate_embedding",
    "process_document_chunks",
    "async_process_document_chunks",
    "VectorSearchService",
    "search_by_text",
    "async_search_by_text",
    "DocumentProcessor",
    "process_document",
    "async_process_document",
    "LLMService",
    "generate_response",
    "async_generate_response",
    "create_query_response",
    "async_create_query_response",
    "FeedbackProcessor",
    "process_feedback_batch",
    "get_model_parameters",
]