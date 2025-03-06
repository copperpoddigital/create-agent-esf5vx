"""
Utility package initialization module for the Document Management and AI Chatbot System.

This module exports utility functions and classes from various utility modules,
simplifying imports by providing a single entry point for commonly used utility 
functions across the system.

Exported utilities include:
- Validation functions for data validation
- Token utilities for JWT handling
- File utilities for file system operations
- PDF utilities for document processing
- Vector utilities for embeddings and similarity search
"""

# Import validation utilities
from .validation import (
    validate_document_file,
    validate_query_text,
    validate_email,
    validate_password,
    validate_feedback_rating,
    sanitize_string,
    validate_uuid,
    validate_pagination_params,
    ValidationError
)

# Import token utilities
from .token_utils import (
    decode_token,
    extract_token_data,
    create_token_payload,
    encode_token,
    get_token_from_header,
    is_token_expired,
    calculate_token_expiry
)

# Import file utilities
from .file_utils import (
    ensure_directory_exists,
    generate_unique_filename,
    sanitize_filename,
    get_file_extension,
    is_safe_path,
    get_absolute_path,
    is_pdf_file,
    get_file_size,
    delete_file,
    copy_file,
    move_file,
    create_temp_directory,
    clean_temp_directory
)

# Import PDF utilities
from .pdf_utils import (
    extract_text_from_pdf,
    extract_text_from_pdf_bytes,
    clean_text,
    chunk_text,
    extract_pdf_metadata,
    count_tokens,
    process_pdf_document
)

# Import vector utilities
from .vector_utils import (
    normalize_vector,
    validate_vector_dimensions,
    calculate_similarity,
    generate_embedding_id,
    serialize_vector,
    deserialize_vector,
    batch_normalize_vectors,
    convert_to_numpy_array,
    combine_vectors
)

# Define what will be exported when using "from app.utils import *"
__all__ = [
    # Validation utilities
    'validate_document_file',
    'validate_query_text',
    'validate_email',
    'validate_password',
    'validate_feedback_rating',
    'sanitize_string',
    'validate_uuid',
    'validate_pagination_params',
    'ValidationError',
    
    # Token utilities
    'decode_token',
    'extract_token_data',
    'create_token_payload',
    'encode_token',
    'get_token_from_header',
    'is_token_expired',
    'calculate_token_expiry',
    
    # File utilities
    'ensure_directory_exists',
    'generate_unique_filename',
    'sanitize_filename',
    'get_file_extension',
    'is_safe_path',
    'get_absolute_path',
    'is_pdf_file',
    'get_file_size',
    'delete_file',
    'copy_file',
    'move_file',
    'create_temp_directory',
    'clean_temp_directory',
    
    # PDF utilities
    'extract_text_from_pdf',
    'extract_text_from_pdf_bytes',
    'clean_text',
    'chunk_text',
    'extract_pdf_metadata',
    'count_tokens',
    'process_pdf_document',
    
    # Vector utilities
    'normalize_vector',
    'validate_vector_dimensions',
    'calculate_similarity',
    'generate_embedding_id',
    'serialize_vector',
    'deserialize_vector',
    'batch_normalize_vectors',
    'convert_to_numpy_array',
    'combine_vectors'
]