#!/usr/bin/env python3
"""
Main initialization module for test fixtures.

This module provides centralized access to all test data fixtures used throughout 
the test suite. It imports and re-exports key fixtures from subdirectories to 
simplify imports in test files and maintain a clean fixture organization.
"""

from pathlib import Path

# Define the main fixtures directory
FIXTURES_DIR = Path(__file__).parent

# Import document fixtures
from .documents import (
    SAMPLE_PDF_PATH,
    DOCUMENTS_DIR,
    get_sample_pdf_path,
    get_sample_pdf_bytes,
    get_documents_dir,
)

# Import vector fixtures
from .vectors import (
    SAMPLE_EMBEDDINGS_PATH,
    load_sample_embeddings,
    get_embedding_vectors,
    get_embedding_ids,
    get_embedding_texts,
    get_sample_vectors_with_ids,
)

# Import response fixtures
from .responses import (
    RESPONSES_FILE_PATH,
    DEFAULT_RESPONSE,
    load_responses,
    get_response_for_query,
    get_standard_response,
    get_no_context_response,
    get_error_fallback_response,
    get_responses_dict,
)


def get_fixtures_dir() -> Path:
    """
    Returns the path to the fixtures directory.
    
    Returns:
        pathlib.Path: Path to the fixtures directory
    """
    return FIXTURES_DIR