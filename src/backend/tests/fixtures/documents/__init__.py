"""
Test fixtures for document processing.

This module provides access to sample PDF documents used in testing. It exposes
paths and utility functions to access test PDF documents for unit and integration 
tests of document processing functionality.
"""

import os
from pathlib import Path

# Define paths to test documents
DOCUMENTS_DIR = Path(__file__).parent
SAMPLE_PDF_PATH = DOCUMENTS_DIR / 'sample.pdf'


def get_sample_pdf_path() -> Path:
    """
    Returns the absolute path to the sample PDF file.
    
    Returns:
        Path: Path to the sample PDF file
    """
    return SAMPLE_PDF_PATH


def get_sample_pdf_bytes() -> bytes:
    """
    Reads and returns the sample PDF file as bytes.
    
    Returns:
        bytes: Content of the sample PDF file as bytes
    """
    with open(SAMPLE_PDF_PATH, 'rb') as f:
        return f.read()


def get_documents_dir() -> Path:
    """
    Returns the path to the documents fixtures directory.
    
    Returns:
        Path: Path to the documents fixtures directory
    """
    return DOCUMENTS_DIR