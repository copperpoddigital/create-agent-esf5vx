"""
Utility module that provides PDF document processing functions for the Document Management and AI Chatbot System.

This module includes functions for:
- Extracting text from PDF documents
- Cleaning and normalizing extracted text
- Splitting text into manageable chunks for processing
- Extracting metadata from PDF files
- Counting tokens for LLM context management
- Complete document processing workflow
"""

import os
import re
from typing import Dict, List, Any, Optional

import fitz  # PyMuPDF version 1.21.0+
import tiktoken  # version 0.3.0+
from fastapi import HTTPException  # version 0.95.0+

from ..core.logging import get_logger
from ..core.settings import document_settings
from .file_utils import is_pdf_file

# Initialize module logger
logger = get_logger(__name__)

# Default encoding model for token counting
ENCODING_MODEL = "cl100k_base"  # OpenAI's encoding model for newer GPT models

# Regular expression for normalizing whitespace
WHITESPACE_PATTERN = re.compile(r'\s+')


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text content from the PDF
        
    Raises:
        HTTPException: If file is not found, not a valid PDF, or text extraction fails
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    # Check if file exists
    if not os.path.isfile(file_path):
        logger.error(f"PDF file not found: {file_path}")
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Validate PDF file
    if not is_pdf_file(file_path):
        logger.error(f"Not a valid PDF file: {file_path}")
        raise HTTPException(status_code=400, detail="Not a valid PDF file")
    
    try:
        # Open PDF file using PyMuPDF
        with fitz.open(file_path) as pdf_document:
            text_content = ""
            
            # Iterate through each page and extract text
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text_content += page.get_text()
                
            # Clean the extracted text
            cleaned_text = clean_text(text_content)
            
            logger.info(f"Successfully extracted text from PDF: {file_path}")
            return cleaned_text
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error extracting text from PDF: {str(e)}"
        )


def extract_text_from_pdf_bytes(pdf_data: bytes) -> str:
    """
    Extracts text content from PDF data in bytes format.
    
    Args:
        pdf_data: PDF content as bytes
        
    Returns:
        str: Extracted text content from the PDF bytes
        
    Raises:
        HTTPException: If data is not a valid PDF or text extraction fails
    """
    logger.info("Extracting text from PDF bytes data")
    
    # Validate PDF data
    if not is_pdf_file(pdf_data):
        logger.error("Invalid PDF data provided")
        raise HTTPException(status_code=400, detail="Not a valid PDF file")
    
    try:
        # Open PDF from bytes using PyMuPDF
        with fitz.open(stream=pdf_data, filetype="pdf") as pdf_document:
            text_content = ""
            
            # Iterate through each page and extract text
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text_content += page.get_text()
                
            # Clean the extracted text
            cleaned_text = clean_text(text_content)
            
            logger.info("Successfully extracted text from PDF bytes")
            return cleaned_text
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF bytes: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error extracting text from PDF: {str(e)}"
        )


def clean_text(text: str) -> str:
    """
    Cleans and normalizes extracted text.
    
    Args:
        text: Raw text to clean
        
    Returns:
        str: Cleaned and normalized text
    """
    # Replace multiple whitespace characters with a single space
    text = WHITESPACE_PATTERN.sub(' ', text)
    
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove leading and trailing whitespace
    text = text.strip()
    
    return text


def chunk_text(text: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> List[str]:
    """
    Splits text into chunks of specified size with overlap.
    
    Args:
        text: Text to split into chunks
        chunk_size: Maximum size of each chunk in characters (default from settings)
        chunk_overlap: Overlap between chunks in characters (default from settings)
        
    Returns:
        List[str]: List of text chunks
        
    Raises:
        ValueError: If chunk_size is less than or equal to chunk_overlap
    """
    logger.debug("Chunking text into smaller segments")
    
    # Use default values from settings if not provided
    if chunk_size is None:
        chunk_size = document_settings.CHUNK_SIZE
    
    if chunk_overlap is None:
        chunk_overlap = document_settings.CHUNK_OVERLAP
    
    # Validate chunk parameters
    if chunk_size <= chunk_overlap:
        logger.error(f"Invalid chunking parameters: chunk_size ({chunk_size}) must be greater than chunk_overlap ({chunk_overlap})")
        raise ValueError("Chunk size must be greater than chunk overlap")
    
    # If text is empty, return empty list
    if not text:
        return []
    
    chunks = []
    
    # Calculate step size (chunk size minus overlap)
    step_size = chunk_size - chunk_overlap
    
    # Split text into chunks with overlap
    for i in range(0, len(text), step_size):
        chunk = text[i:i + chunk_size]
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
    
    logger.debug(f"Created {len(chunks)} text chunks")
    return chunks


def extract_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts metadata from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dict[str, Any]: Dictionary containing PDF metadata
        
    Raises:
        HTTPException: If file is not found, not a valid PDF, or metadata extraction fails
    """
    logger.info(f"Extracting metadata from PDF: {file_path}")
    
    # Check if file exists
    if not os.path.isfile(file_path):
        logger.error(f"PDF file not found: {file_path}")
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Validate PDF file
    if not is_pdf_file(file_path):
        logger.error(f"Not a valid PDF file: {file_path}")
        raise HTTPException(status_code=400, detail="Not a valid PDF file")
    
    try:
        # Open PDF file using PyMuPDF
        with fitz.open(file_path) as pdf_document:
            # Initialize metadata dictionary
            metadata = {}
            
            # Extract standard PDF metadata
            metadata["title"] = pdf_document.metadata.get("title", "")
            metadata["author"] = pdf_document.metadata.get("author", "")
            metadata["subject"] = pdf_document.metadata.get("subject", "")
            metadata["keywords"] = pdf_document.metadata.get("keywords", "")
            metadata["creator"] = pdf_document.metadata.get("creator", "")
            metadata["producer"] = pdf_document.metadata.get("producer", "")
            metadata["creation_date"] = pdf_document.metadata.get("creationDate", "")
            metadata["modification_date"] = pdf_document.metadata.get("modDate", "")
            
            # Add additional document information
            metadata["page_count"] = len(pdf_document)
            metadata["file_size"] = os.path.getsize(file_path)
            metadata["encrypted"] = pdf_document.is_encrypted
            
            # Get document layout information
            if pdf_document.page_count > 0:
                first_page = pdf_document[0]
                metadata["page_width"] = first_page.rect.width
                metadata["page_height"] = first_page.rect.height
            
            logger.info(f"Successfully extracted metadata from PDF: {file_path}")
            return metadata
    
    except Exception as e:
        logger.error(f"Error extracting metadata from PDF {file_path}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error extracting metadata from PDF: {str(e)}"
        )


def count_tokens(text: str) -> int:
    """
    Counts the number of tokens in a text string using tiktoken.
    
    Args:
        text: Text to count tokens in
        
    Returns:
        int: Number of tokens in the text
    """
    try:
        # Get the encoding for the specified model
        encoding = tiktoken.get_encoding(ENCODING_MODEL)
        
        # Encode the text to get tokens
        tokens = encoding.encode(text)
        
        # Return the count of tokens
        return len(tokens)
    
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        # Return an approximate token count (1 token ≈ 4 characters)
        return len(text) // 4


def process_pdf_document(file_path: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> Dict[str, Any]:
    """
    Processes a PDF document by extracting text, metadata, and creating chunks.
    
    Args:
        file_path: Path to the PDF file
        chunk_size: Maximum size of each chunk in characters (default from settings)
        chunk_overlap: Overlap between chunks in characters (default from settings)
        
    Returns:
        Dict[str, Any]: Dictionary containing processed document data including:
            - text: Full extracted text
            - chunks: List of text chunks
            - metadata: Document metadata
            - token_counts: Dictionary with token counts for each chunk
            
    Raises:
        HTTPException: If document processing fails
    """
    logger.info(f"Processing PDF document: {file_path}")
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        
        # Extract metadata from PDF
        metadata = extract_pdf_metadata(file_path)
        
        # Create text chunks
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        
        # Count tokens for each chunk
        token_counts = {i: count_tokens(chunk) for i, chunk in enumerate(chunks)}
        
        # Build result dictionary
        result = {
            "text": text,
            "chunks": chunks,
            "metadata": metadata,
            "token_counts": token_counts,
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts.values())
        }
        
        logger.info(f"Successfully processed PDF document: {file_path}")
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error processing PDF document {file_path}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing PDF document: {str(e)}"
        )