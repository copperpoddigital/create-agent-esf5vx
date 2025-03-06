"""
Service module that provides file storage operations for the Document Management and AI Chatbot System.
This service handles the storage, retrieval, and deletion of document files in the file system, 
ensuring secure and efficient document management.
"""

import os
from pathlib import Path
from typing import Optional
import uuid  # version: standard library
from fastapi import HTTPException  # version: 0.95.0+

from ..core.logging import get_logger
from ..core.settings import document_settings
from ..utils.file_utils import (
    ensure_directory_exists,
    generate_unique_filename,
    is_safe_path,
    get_absolute_path,
    delete_file
)

# Initialize logger for the service
logger = get_logger(__name__)


class FileStorage:
    """
    Service class that handles file storage operations for documents in the system.
    Provides methods for storing, retrieving, and deleting document files.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initializes the FileStorage service with the configured storage path.
        
        Args:
            storage_path (Optional[str]): Override for the default storage path
        """
        self._storage_path = storage_path or document_settings.DOCUMENT_STORAGE_PATH
        
        # Ensure the storage directory exists
        if not ensure_directory_exists(self._storage_path):
            msg = f"Failed to create storage directory: {self._storage_path}"
            logger.error(msg)
            raise HTTPException(status_code=500, detail=msg)
        
        logger.info(f"FileStorage service initialized with path: {self._storage_path}")

    def store_document(self, content: bytes, original_filename: str) -> str:
        """
        Stores a document file in the file system.
        
        Args:
            content (bytes): The content of the document file
            original_filename (str): The original filename of the document
            
        Returns:
            str: Path where the document was stored (relative to storage path)
            
        Raises:
            HTTPException: If the document cannot be stored
        """
        try:
            # Check file size
            content_size_mb = len(content) / (1024 * 1024)
            if content_size_mb > document_settings.MAX_DOCUMENT_SIZE_MB:
                msg = f"Document exceeds maximum size limit of {document_settings.MAX_DOCUMENT_SIZE_MB}MB"
                logger.error(msg)
                raise HTTPException(status_code=413, detail=msg)
            
            # Generate a unique filename
            unique_filename = generate_unique_filename(original_filename)
            
            # Create the full file path
            file_path = os.path.join(self._storage_path, unique_filename)
            abs_path = get_absolute_path(file_path)
            
            # Ensure the path is safe
            if not is_safe_path(self._storage_path, unique_filename):
                msg = f"Invalid file path detected: {unique_filename}"
                logger.error(msg)
                raise HTTPException(status_code=400, detail=msg)
            
            # Write the file content
            with open(abs_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Document stored successfully: {unique_filename} ({content_size_mb:.2f}MB)")
            
            # Return the relative path for database storage
            return unique_filename
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            msg = f"Failed to store document: {str(e)}"
            logger.error(msg)
            raise HTTPException(status_code=500, detail=msg)

    def retrieve_document(self, file_path: str) -> bytes:
        """
        Retrieves a document file from storage.
        
        Args:
            file_path (str): Path to the document file (relative to storage path)
            
        Returns:
            bytes: Document file content
            
        Raises:
            HTTPException: If the document cannot be retrieved
        """
        try:
            # Create the full file path
            full_path = self.get_full_path(file_path)
            
            # Check if the file exists
            if not os.path.isfile(full_path):
                msg = f"Document not found: {file_path}"
                logger.error(msg)
                raise HTTPException(status_code=404, detail=msg)
            
            # Read and return the file content
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Document retrieved successfully: {file_path}")
            return content
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            msg = f"Failed to retrieve document: {str(e)}"
            logger.error(msg)
            raise HTTPException(status_code=500, detail=msg)

    def delete_document(self, file_path: str) -> bool:
        """
        Deletes a document file from storage.
        
        Args:
            file_path (str): Path to the document file (relative to storage path)
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Create the full file path
            full_path = self.get_full_path(file_path)
            
            # Delete the file
            result = delete_file(full_path)
            
            if result:
                logger.info(f"Document deleted successfully: {file_path}")
            else:
                logger.warning(f"Document deletion failed or file not found: {file_path}")
            
            return result
        
        except HTTPException:
            logger.error(f"Error getting full path for document deletion: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {file_path}: {str(e)}")
            return False

    def document_exists(self, file_path: str) -> bool:
        """
        Checks if a document file exists in storage.
        
        Args:
            file_path (str): Path to the document file (relative to storage path)
            
        Returns:
            bool: True if document exists, False otherwise
        """
        try:
            # Create the full file path
            full_path = self.get_full_path(file_path)
            
            # Check if the file exists
            exists = os.path.isfile(full_path)
            
            if not exists:
                logger.debug(f"Document does not exist: {file_path}")
            
            return exists
        
        except HTTPException:
            logger.error(f"Error getting full path for document existence check: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error checking document existence {file_path}: {str(e)}")
            return False

    def get_full_path(self, file_path: str) -> str:
        """
        Gets the full system path for a document file.
        
        Args:
            file_path (str): Path to the document file (relative to storage path)
            
        Returns:
            str: Full system path to the document
            
        Raises:
            HTTPException: If the path is invalid or unsafe
        """
        try:
            # Join the storage path with the relative file path
            full_path = os.path.join(self._storage_path, file_path)
            abs_path = get_absolute_path(full_path)
            
            # Ensure the path is safe
            if not is_safe_path(self._storage_path, file_path):
                msg = f"Invalid file path detected: {file_path}"
                logger.error(msg)
                raise HTTPException(status_code=400, detail=msg)
            
            return abs_path
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            msg = f"Failed to get full path: {str(e)}"
            logger.error(msg)
            raise HTTPException(status_code=500, detail=msg)