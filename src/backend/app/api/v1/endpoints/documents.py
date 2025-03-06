"""
Document management endpoints for the Document Management and AI Chatbot System.

This module implements API endpoints for uploading, listing, retrieving, and deleting documents.
It handles document processing, vector embedding generation, and access control to ensure 
that users can only access their own documents unless they have admin privileges.
"""

import os
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks, Query, Path, Response
from sqlalchemy.orm import Session

from ..../../api/dependencies import get_db_dependency, get_current_active_user, get_current_admin_user
from ..../../crud.crud_document import document
from ..../../crud.crud_document_chunk import document_chunk
from ..../../models.document import Document, DocumentStatus
from ..../../models.user import User
from ..../../schemas.document import DocumentCreate, Document as DocumentSchema, DocumentUpdate, DocumentFilter, DocumentWithChunks
from ..../../services.document_processor import DocumentProcessor
from ..../../services.file_storage import FileStorage
from ..../../core.logging import get_logger
from ..../../core.settings import document_settings

router = APIRouter(prefix='/documents', tags=['documents'])
logger = get_logger(__name__)
file_storage = FileStorage()
document_processor = DocumentProcessor()

@router.post('/', response_model=DocumentSchema, status_code=status.HTTP_201_CREATED)
async def create_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
) -> DocumentSchema:
    """
    Upload a new document for processing and vector embedding generation.
    
    The file must be a PDF and must not exceed the configured maximum size.
    Document processing (text extraction and vector generation) occurs in the background
    after the upload is complete.
    
    Args:
        background_tasks: FastAPI background tasks for async processing
        file: The uploaded PDF file
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        DocumentSchema: The created document metadata
        
    Raises:
        HTTPException: 
            - 400 if file is not a PDF
            - 413 if file exceeds maximum size
            - 422 if file could not be processed
    """
    logger.info(f"Document upload initiated by user {current_user.id}: {file.filename}")
    
    # Validate file content type
    content_type = file.content_type
    if content_type not in document_settings.ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are supported. Got: {content_type}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Check file size
    file_size = len(file_content)
    max_size_bytes = document_settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {document_settings.MAX_DOCUMENT_SIZE_MB}MB"
        )
    
    try:
        # Create document in DB with processing status
        document_id = uuid.uuid4()
        doc_create = DocumentCreate(
            id=document_id,
            title=os.path.splitext(file.filename)[0],  # Use filename without extension as title
            filename=file.filename,
            size_bytes=file_size,
            status=DocumentStatus.processing,
            file_path="",  # Will be updated after storage
            uploader_id=current_user.id
        )
        
        # Store the document in the database
        db_document = document.create(db=db, obj_in=doc_create)
        
        # Store the file
        file_path = file_storage.store_document(file_content, file.filename)
        
        # Update document file path
        db_document = document.update(
            db=db, 
            db_obj=db_document, 
            obj_in={"file_path": file_path}
        )
        
        # Add background task to process the document
        background_tasks.add_task(
            process_document_background,
            document_id=db_document.id,
            db=db
        )
        
        logger.info(f"Document {db_document.id} created successfully, processing in background")
        return db_document
        
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not process document: {str(e)}"
        )

@router.get('/', response_model=Dict[str, Any])
async def get_documents(
    filter_params: Optional[DocumentFilter] = Depends(),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    List documents with optional filtering and pagination.
    
    Regular users can only see their own documents.
    Admin users can see all documents.
    
    Args:
        filter_params: Optional filter criteria for documents
        skip: Number of documents to skip (pagination)
        limit: Maximum number of documents to return (pagination)
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        Dict containing documents list, total count, and pagination info
    """
    logger.info(f"Get documents request by user {current_user.id}")
    
    # Apply user filtering for non-admin users
    if not current_user.is_admin():
        if filter_params is None:
            filter_params = DocumentFilter()
        filter_params.uploader_id = current_user.id
    
    # Count total matching documents
    total_count = document.count_with_filter(db=db, filter_params=filter_params)
    
    # Get documents with pagination
    documents_list = document.get_multi_with_filter(
        db=db, 
        filter_params=filter_params, 
        skip=skip, 
        limit=limit
    )
    
    # Return results with pagination info
    return {
        "items": documents_list,
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total_count
    }

@router.get('/{document_id}', response_model=DocumentSchema)
async def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
) -> DocumentSchema:
    """
    Get a specific document by ID.
    
    Regular users can only access their own documents.
    Admin users can access any document.
    
    Args:
        document_id: ID of the document to retrieve
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        DocumentSchema: The requested document's metadata
        
    Raises:
        HTTPException: 
            - 404 if document not found
            - 403 if user doesn't have access to the document
    """
    logger.info(f"Get document {document_id} request by user {current_user.id}")
    
    # Get document from database
    db_document = document.get(db=db, id=document_id)
    if not db_document:
        logger.warning(f"Document {document_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to the document
    if not current_user.is_admin() and db_document.uploader_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access document {document_id} without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )
    
    return db_document

@router.get('/{document_id}/chunks', response_model=DocumentWithChunks)
async def get_document_with_chunks(
    document_id: uuid.UUID,
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
) -> DocumentWithChunks:
    """
    Get a document along with its chunked text content.
    
    Regular users can only access their own documents.
    Admin users can access any document.
    
    Args:
        document_id: ID of the document to retrieve
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        DocumentWithChunks: The document with its text chunks
        
    Raises:
        HTTPException: 
            - 404 if document not found
            - 403 if user doesn't have access to the document
    """
    logger.info(f"Get document {document_id} with chunks request by user {current_user.id}")
    
    # Get document from database
    db_document = document.get(db=db, id=document_id)
    if not db_document:
        logger.warning(f"Document {document_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to the document
    if not current_user.is_admin() and db_document.uploader_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access document {document_id} without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )
    
    # Get document chunks
    chunks = document_chunk.get_by_document_id(db=db, document_id=document_id)
    
    # Create response with document and chunks
    result = DocumentWithChunks.model_validate(db_document)
    result.chunks = chunks
    
    return result

@router.get('/{document_id}/download')
async def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
) -> Response:
    """
    Download the original document file.
    
    Regular users can only download their own documents.
    Admin users can download any document.
    
    Args:
        document_id: ID of the document to download
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        Response: File download response
        
    Raises:
        HTTPException: 
            - 404 if document not found
            - 403 if user doesn't have access to the document
            - 404 if document file not found
    """
    logger.info(f"Download document {document_id} request by user {current_user.id}")
    
    # Get document from database
    db_document = document.get(db=db, id=document_id)
    if not db_document:
        logger.warning(f"Document {document_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to the document
    if not current_user.is_admin() and db_document.uploader_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to download document {document_id} without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this document"
        )
    
    try:
        # Retrieve document from storage
        file_content = file_storage.retrieve_document(db_document.file_path)
        
        # Return file as response
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{db_document.filename}"'
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions from file_storage
        raise
    except Exception as e:
        logger.error(f"Error retrieving document file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found"
        )

@router.delete('/{document_id}', status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Soft delete a document.
    
    This marks the document as deleted but doesn't remove it from the system.
    Regular users can only delete their own documents.
    Admin users can delete any document.
    
    Args:
        document_id: ID of the document to delete
        db: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        Dict with success message
        
    Raises:
        HTTPException: 
            - 404 if document not found
            - 403 if user doesn't have permission to delete the document
    """
    logger.info(f"Delete document {document_id} request by user {current_user.id}")
    
    # Get document from database
    db_document = document.get(db=db, id=document_id)
    if not db_document:
        logger.warning(f"Document {document_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to delete the document
    if not current_user.is_admin() and db_document.uploader_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to delete document {document_id} without permission")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document"
        )
    
    # Soft delete the document (mark as deleted)
    document.soft_delete(db=db, id=document_id)
    
    logger.info(f"Document {document_id} soft deleted by user {current_user.id}")
    return {"message": "Document deleted successfully"}

@router.delete('/{document_id}/permanent', status_code=status.HTTP_200_OK)
async def hard_delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db_dependency),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Permanently delete a document and its associated files.
    
    This operation is only available to admin users and permanently removes
    the document, its chunks, and the stored file.
    
    Args:
        document_id: ID of the document to permanently delete
        db: Database session dependency
        current_user: Current authenticated admin user
        
    Returns:
        Dict with success message
        
    Raises:
        HTTPException: 
            - 404 if document not found
    """
    logger.info(f"Permanent delete document {document_id} request by admin {current_user.id}")
    
    # Get document from database
    db_document = document.get(db=db, id=document_id)
    if not db_document:
        logger.warning(f"Document {document_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get file path before deletion
    file_path = db_document.file_path
    
    try:
        # Delete document chunks
        document_chunk.remove_by_document_id(db=db, document_id=document_id)
        
        # Delete document from database
        document.remove(db=db, id=document_id)
        
        # Delete document file
        file_storage.delete_document(file_path)
        
        logger.info(f"Document {document_id} permanently deleted by admin {current_user.id}")
        return {"message": "Document permanently deleted"}
    except Exception as e:
        logger.error(f"Error permanently deleting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document"
        )

async def process_document_background(document_id: uuid.UUID, db: Session) -> None:
    """
    Background task to process a document.
    
    Extracts text from the document, creates chunks, generates vector embeddings,
    and updates the document status.
    
    Args:
        document_id: ID of the document to process
        db: Database session
    """
    logger.info(f"Starting background processing for document {document_id}")
    
    try:
        # Get document from database
        db_document = document.get(db=db, id=document_id)
        if not db_document:
            logger.error(f"Document {document_id} not found for background processing")
            return
        
        # Process document
        result = document_processor.process_document_from_path(
            file_path=db_document.file_path,
            db_document=db_document
        )
        
        # Create document chunks in the database
        document_chunk.create_batch(db=db, objs_in=result["chunks"])
        
        # Update document status to available
        document.update_status(db=db, document=db_document, status=DocumentStatus.available)
        
        logger.info(f"Background processing completed for document {document_id}")
    except Exception as e:
        logger.error(f"Error in background processing for document {document_id}: {str(e)}")
        
        # Update document status to error
        try:
            db_document = document.get(db=db, id=document_id)
            if db_document:
                document.update_status(db=db, document=db_document, status=DocumentStatus.error)
        except Exception as update_error:
            logger.error(f"Failed to update document status to error: {str(update_error)}")