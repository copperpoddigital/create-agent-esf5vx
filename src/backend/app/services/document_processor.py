"""
Service module that handles the processing of uploaded PDF documents for the Document Management and AI Chatbot System.
This module orchestrates the document processing workflow, including text extraction, chunking, vector embedding generation,
and storage of document chunks and their embeddings.
"""

import os
import uuid
import asyncio
from typing import List, Dict, Optional, Any

from fastapi import HTTPException  # version: 0.95.0+

from ..core.logging import get_logger
from ..core.settings import document_settings
from ..utils.pdf_utils import (
    extract_text_from_pdf,
    extract_text_from_pdf_bytes,
    chunk_text,
    extract_pdf_metadata,
    count_tokens
)
from ..utils.file_utils import is_pdf_file
from .file_storage import FileStorage
from .embedding_service import process_document_chunks, async_process_document_chunks
from ..models.document import Document, DocumentStatus
from ..models.document_chunk import DocumentChunk
from ..schemas.document_chunk import DocumentChunkCreate

# Initialize logger
logger = get_logger(__name__)

# Initialize file storage service
file_storage = FileStorage()


def process_document(
    document_content: bytes,
    filename: str,
    db_document: Optional[Document] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Processes a document by extracting text, creating chunks, and generating vector embeddings.
    
    Args:
        document_content: Raw document content as bytes
        filename: Original filename of the document
        db_document: Optional Document model instance to update status
        chunk_size: Optional custom chunk size (defaults to settings value)
        chunk_overlap: Optional custom chunk overlap (defaults to settings value)
        
    Returns:
        Dictionary containing processed document data and metadata
        
    Raises:
        HTTPException: If document validation, processing, or embedding generation fails
    """
    try:
        # Validate that the document is a valid PDF
        if not is_pdf_file(document_content):
            logger.error(f"Invalid PDF file: {filename}")
            if db_document:
                db_document.update_status(DocumentStatus.error)
            raise HTTPException(status_code=400, detail="Invalid PDF file format")
        
        # Store the document file
        file_path = file_storage.store_document(document_content, filename)
        logger.info(f"Document stored at {file_path}")
        
        # Extract text from the PDF bytes
        text = extract_text_from_pdf_bytes(document_content)
        logger.info(f"Successfully extracted text from {filename}")
        
        # Extract metadata from the PDF
        metadata = extract_pdf_metadata(file_storage.get_full_path(file_path))
        logger.info(f"Extracted metadata from {filename}")
        
        # Use default values from settings if not provided
        if chunk_size is None:
            chunk_size = document_settings.CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = document_settings.CHUNK_OVERLAP
            
        # Create text chunks
        text_chunks = chunk_text(text, chunk_size, chunk_overlap)
        logger.info(f"Created {len(text_chunks)} text chunks from document")
        
        # Count tokens for each chunk
        token_counts = [count_tokens(chunk) for chunk in text_chunks]
        logger.info(f"Counted tokens for {len(text_chunks)} chunks")
        
        # Create document chunks
        document_id = db_document.id if db_document else uuid.uuid4()
        chunks = create_document_chunks(text_chunks, token_counts, document_id)
        logger.info(f"Created {len(chunks)} document chunks")
        
        # Process document chunks to generate embeddings
        embedding_ids = process_document_chunks(chunks)
        logger.info(f"Generated {len(embedding_ids)} embeddings for document chunks")
        
        # Update document status to available if db_document is provided
        if db_document:
            db_document.update_status(DocumentStatus.available)
            logger.info(f"Updated document status to available: {db_document.id}")
        
        # Return processing results
        return {
            "document_path": file_path,
            "metadata": metadata,
            "chunks": chunks,
            "text_chunks": text_chunks,
            "token_counts": token_counts,
            "embedding_ids": embedding_ids,
            "status": "success"
        }
    except HTTPException as e:
        # Log the error and update document status
        logger.error(f"HTTP error processing document {filename}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise
    except Exception as e:
        # Log the error, update document status, and re-raise as HTTPException
        logger.error(f"Error processing document {filename}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


async def async_process_document(
    document_content: bytes,
    filename: str,
    db_document: Optional[Document] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Asynchronously processes a document by extracting text, creating chunks, and generating vector embeddings.
    
    Args:
        document_content: Raw document content as bytes
        filename: Original filename of the document
        db_document: Optional Document model instance to update status
        chunk_size: Optional custom chunk size (defaults to settings value)
        chunk_overlap: Optional custom chunk overlap (defaults to settings value)
        
    Returns:
        Dictionary containing processed document data and metadata
        
    Raises:
        HTTPException: If document validation, processing, or embedding generation fails
    """
    try:
        # Validate that the document is a valid PDF
        if not is_pdf_file(document_content):
            logger.error(f"Invalid PDF file: {filename}")
            if db_document:
                db_document.update_status(DocumentStatus.error)
            raise HTTPException(status_code=400, detail="Invalid PDF file format")
        
        # Store the document file
        file_path = file_storage.store_document(document_content, filename)
        logger.info(f"Document stored at {file_path}")
        
        # Extract text from the PDF bytes (run in thread pool as it's CPU-bound)
        text = await asyncio.to_thread(extract_text_from_pdf_bytes, document_content)
        logger.info(f"Successfully extracted text from {filename}")
        
        # Extract metadata from the PDF (run in thread pool as it's CPU-bound)
        metadata = await asyncio.to_thread(
            extract_pdf_metadata, 
            file_storage.get_full_path(file_path)
        )
        logger.info(f"Extracted metadata from {filename}")
        
        # Use default values from settings if not provided
        if chunk_size is None:
            chunk_size = document_settings.CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = document_settings.CHUNK_OVERLAP
            
        # Create text chunks (run in thread pool as it's CPU-bound)
        text_chunks = await asyncio.to_thread(chunk_text, text, chunk_size, chunk_overlap)
        logger.info(f"Created {len(text_chunks)} text chunks from document")
        
        # Count tokens for each chunk (run in thread pool as it's CPU-bound)
        token_counts = await asyncio.to_thread(
            lambda chunks: [count_tokens(chunk) for chunk in chunks], 
            text_chunks
        )
        logger.info(f"Counted tokens for {len(text_chunks)} chunks")
        
        # Create document chunks
        document_id = db_document.id if db_document else uuid.uuid4()
        chunks = create_document_chunks(text_chunks, token_counts, document_id)
        logger.info(f"Created {len(chunks)} document chunks")
        
        # Process document chunks asynchronously to generate embeddings
        embedding_ids = await async_process_document_chunks(chunks)
        logger.info(f"Generated {len(embedding_ids)} embeddings for document chunks")
        
        # Update document status to available if db_document is provided
        if db_document:
            db_document.update_status(DocumentStatus.available)
            logger.info(f"Updated document status to available: {db_document.id}")
        
        # Return processing results
        return {
            "document_path": file_path,
            "metadata": metadata,
            "chunks": chunks,
            "text_chunks": text_chunks,
            "token_counts": token_counts,
            "embedding_ids": embedding_ids,
            "status": "success"
        }
    except HTTPException as e:
        # Log the error and update document status
        logger.error(f"HTTP error processing document {filename}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise
    except Exception as e:
        # Log the error, update document status, and re-raise as HTTPException
        logger.error(f"Error processing document {filename}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


def process_document_from_path(
    file_path: str,
    db_document: Optional[Document] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Processes a document from a file path by extracting text, creating chunks, and generating vector embeddings.
    
    Args:
        file_path: Path to the document file
        db_document: Optional Document model instance to update status
        chunk_size: Optional custom chunk size (defaults to settings value)
        chunk_overlap: Optional custom chunk overlap (defaults to settings value)
        
    Returns:
        Dictionary containing processed document data and metadata
        
    Raises:
        HTTPException: If document validation, processing, or embedding generation fails
    """
    try:
        # Get the full path to the document
        full_path = file_storage.get_full_path(file_path)
        logger.info(f"Processing document from path: {full_path}")
        
        # Validate that the file exists and is a valid PDF
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            if db_document:
                db_document.update_status(DocumentStatus.error)
            raise HTTPException(status_code=404, detail="Document file not found")
            
        if not is_pdf_file(full_path):
            logger.error(f"Invalid PDF file: {full_path}")
            if db_document:
                db_document.update_status(DocumentStatus.error)
            raise HTTPException(status_code=400, detail="Invalid PDF file format")
        
        # Extract text from the PDF file
        text = extract_text_from_pdf(full_path)
        logger.info(f"Successfully extracted text from {file_path}")
        
        # Extract metadata from the PDF
        metadata = extract_pdf_metadata(full_path)
        logger.info(f"Extracted metadata from {file_path}")
        
        # Use default values from settings if not provided
        if chunk_size is None:
            chunk_size = document_settings.CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = document_settings.CHUNK_OVERLAP
            
        # Create text chunks
        text_chunks = chunk_text(text, chunk_size, chunk_overlap)
        logger.info(f"Created {len(text_chunks)} text chunks from document")
        
        # Count tokens for each chunk
        token_counts = [count_tokens(chunk) for chunk in text_chunks]
        logger.info(f"Counted tokens for {len(text_chunks)} chunks")
        
        # Create document chunks
        document_id = db_document.id if db_document else uuid.uuid4()
        chunks = create_document_chunks(text_chunks, token_counts, document_id)
        logger.info(f"Created {len(chunks)} document chunks")
        
        # Process document chunks to generate embeddings
        embedding_ids = process_document_chunks(chunks)
        logger.info(f"Generated {len(embedding_ids)} embeddings for document chunks")
        
        # Update document status to available if db_document is provided
        if db_document:
            db_document.update_status(DocumentStatus.available)
            logger.info(f"Updated document status to available: {db_document.id}")
        
        # Return processing results
        return {
            "document_path": file_path,
            "metadata": metadata,
            "chunks": chunks,
            "text_chunks": text_chunks,
            "token_counts": token_counts,
            "embedding_ids": embedding_ids,
            "status": "success"
        }
    except HTTPException as e:
        # Log the error and update document status
        logger.error(f"HTTP error processing document from path {file_path}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise
    except Exception as e:
        # Log the error, update document status, and re-raise as HTTPException
        logger.error(f"Error processing document from path {file_path}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


async def async_process_document_from_path(
    file_path: str,
    db_document: Optional[Document] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Asynchronously processes a document from a file path by extracting text, creating chunks, and generating vector embeddings.
    
    Args:
        file_path: Path to the document file
        db_document: Optional Document model instance to update status
        chunk_size: Optional custom chunk size (defaults to settings value)
        chunk_overlap: Optional custom chunk overlap (defaults to settings value)
        
    Returns:
        Dictionary containing processed document data and metadata
        
    Raises:
        HTTPException: If document validation, processing, or embedding generation fails
    """
    try:
        # Get the full path to the document
        full_path = file_storage.get_full_path(file_path)
        logger.info(f"Asynchronously processing document from path: {full_path}")
        
        # Validate that the file exists and is a valid PDF
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            if db_document:
                db_document.update_status(DocumentStatus.error)
            raise HTTPException(status_code=404, detail="Document file not found")
            
        if not is_pdf_file(full_path):
            logger.error(f"Invalid PDF file: {full_path}")
            if db_document:
                db_document.update_status(DocumentStatus.error)
            raise HTTPException(status_code=400, detail="Invalid PDF file format")
        
        # Extract text from the PDF file (run in thread pool as it's CPU-bound)
        text = await asyncio.to_thread(extract_text_from_pdf, full_path)
        logger.info(f"Successfully extracted text from {file_path}")
        
        # Extract metadata from the PDF (run in thread pool as it's CPU-bound)
        metadata = await asyncio.to_thread(extract_pdf_metadata, full_path)
        logger.info(f"Extracted metadata from {file_path}")
        
        # Use default values from settings if not provided
        if chunk_size is None:
            chunk_size = document_settings.CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = document_settings.CHUNK_OVERLAP
            
        # Create text chunks (run in thread pool as it's CPU-bound)
        text_chunks = await asyncio.to_thread(chunk_text, text, chunk_size, chunk_overlap)
        logger.info(f"Created {len(text_chunks)} text chunks from document")
        
        # Count tokens for each chunk (run in thread pool as it's CPU-bound)
        token_counts = await asyncio.to_thread(
            lambda chunks: [count_tokens(chunk) for chunk in chunks], 
            text_chunks
        )
        logger.info(f"Counted tokens for {len(text_chunks)} chunks")
        
        # Create document chunks
        document_id = db_document.id if db_document else uuid.uuid4()
        chunks = create_document_chunks(text_chunks, token_counts, document_id)
        logger.info(f"Created {len(chunks)} document chunks")
        
        # Process document chunks asynchronously to generate embeddings
        embedding_ids = await async_process_document_chunks(chunks)
        logger.info(f"Generated {len(embedding_ids)} embeddings for document chunks")
        
        # Update document status to available if db_document is provided
        if db_document:
            db_document.update_status(DocumentStatus.available)
            logger.info(f"Updated document status to available: {db_document.id}")
        
        # Return processing results
        return {
            "document_path": file_path,
            "metadata": metadata,
            "chunks": chunks,
            "text_chunks": text_chunks,
            "token_counts": token_counts,
            "embedding_ids": embedding_ids,
            "status": "success"
        }
    except HTTPException as e:
        # Log the error and update document status
        logger.error(f"HTTP error processing document from path {file_path}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise
    except Exception as e:
        # Log the error, update document status, and re-raise as HTTPException
        logger.error(f"Error processing document from path {file_path}: {str(e)}")
        if db_document:
            db_document.update_status(DocumentStatus.error)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


def create_document_chunks(
    text_chunks: List[str],
    token_counts: List[int],
    document_id: uuid.UUID
) -> List[DocumentChunkCreate]:
    """
    Creates DocumentChunkCreate objects from text chunks.
    
    Args:
        text_chunks: List of text chunks from document
        token_counts: List of token counts corresponding to each chunk
        document_id: UUID of the document these chunks belong to
        
    Returns:
        List of DocumentChunkCreate objects ready for database insertion
    """
    document_chunks = []
    
    for i, (chunk, token_count) in enumerate(zip(text_chunks, token_counts)):
        # Create a DocumentChunkCreate for each text chunk
        chunk_obj = DocumentChunkCreate(
            document_id=document_id,
            chunk_index=i,
            content=chunk,
            token_count=token_count,
            embedding_id=""  # Will be updated after embedding generation
        )
        document_chunks.append(chunk_obj)
    
    return document_chunks


class DocumentProcessor:
    """
    Service class that handles the processing of documents, including text extraction, chunking,
    and vector embedding generation.
    """
    
    def __init__(
        self, 
        file_storage: Optional[FileStorage] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initializes the DocumentProcessor with file storage and chunking settings.
        
        Args:
            file_storage: Optional FileStorage instance for document storage
            chunk_size: Optional custom chunk size (defaults to settings value)
            chunk_overlap: Optional custom chunk overlap (defaults to settings value)
        """
        self._logger = get_logger(__name__)
        self._file_storage = file_storage or FileStorage()
        self._chunk_size = chunk_size or document_settings.CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or document_settings.CHUNK_OVERLAP
        
        self._logger.info(
            f"DocumentProcessor initialized with chunk_size={self._chunk_size}, "
            f"chunk_overlap={self._chunk_overlap}"
        )
    
    def process_document(
        self,
        document_content: bytes,
        filename: str,
        db_document: Optional[Document] = None
    ) -> Dict[str, Any]:
        """
        Processes a document by extracting text, creating chunks, and generating vector embeddings.
        
        Args:
            document_content: Raw document content as bytes
            filename: Original filename of the document
            db_document: Optional Document model instance to update status
            
        Returns:
            Dictionary containing processed document data and metadata
        """
        return process_document(
            document_content=document_content,
            filename=filename,
            db_document=db_document,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap
        )
    
    async def async_process_document(
        self,
        document_content: bytes,
        filename: str,
        db_document: Optional[Document] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously processes a document by extracting text, creating chunks, and generating vector embeddings.
        
        Args:
            document_content: Raw document content as bytes
            filename: Original filename of the document
            db_document: Optional Document model instance to update status
            
        Returns:
            Dictionary containing processed document data and metadata
        """
        return await async_process_document(
            document_content=document_content,
            filename=filename,
            db_document=db_document,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap
        )
    
    def process_document_from_path(
        self,
        file_path: str,
        db_document: Optional[Document] = None
    ) -> Dict[str, Any]:
        """
        Processes a document from a file path by extracting text, creating chunks, and generating vector embeddings.
        
        Args:
            file_path: Path to the document file
            db_document: Optional Document model instance to update status
            
        Returns:
            Dictionary containing processed document data and metadata
        """
        return process_document_from_path(
            file_path=file_path,
            db_document=db_document,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap
        )
    
    async def async_process_document_from_path(
        self,
        file_path: str,
        db_document: Optional[Document] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously processes a document from a file path by extracting text, creating chunks, and generating vector embeddings.
        
        Args:
            file_path: Path to the document file
            db_document: Optional Document model instance to update status
            
        Returns:
            Dictionary containing processed document data and metadata
        """
        return await async_process_document_from_path(
            file_path=file_path,
            db_document=db_document,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap
        )
    
    def reprocess_document(self, document: Document) -> Dict[str, Any]:
        """
        Reprocesses an existing document to update its chunks and vector embeddings.
        
        Args:
            document: Document model instance to reprocess
            
        Returns:
            Dictionary containing processed document data and metadata
        """
        # Update document status to processing
        document.update_status(DocumentStatus.processing)
        self._logger.info(f"Reprocessing document: {document.id}")
        
        # Process the document from its file path
        return self.process_document_from_path(document.file_path, document)
    
    async def async_reprocess_document(self, document: Document) -> Dict[str, Any]:
        """
        Asynchronously reprocesses an existing document to update its chunks and vector embeddings.
        
        Args:
            document: Document model instance to reprocess
            
        Returns:
            Dictionary containing processed document data and metadata
        """
        # Update document status to processing
        document.update_status(DocumentStatus.processing)
        self._logger.info(f"Asynchronously reprocessing document: {document.id}")
        
        # Process the document from its file path asynchronously
        return await self.async_process_document_from_path(document.file_path, document)