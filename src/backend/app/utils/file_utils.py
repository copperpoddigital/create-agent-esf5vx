"""
Utility module that provides file system operations and helper functions for handling files in the Document Management and AI Chatbot System.

This module includes directory management, file validation, unique filename generation, and path manipulation
to support document storage and retrieval operations.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Union, Optional

import magic  # version: 0.4.27+
from fastapi import HTTPException  # version: 0.95.0+

from ..core.settings import document_settings
from ..core.logging import get_logger

# Initialize module logger
logger = get_logger(__name__)

# Define a set of characters considered safe for filenames
SAFE_FILENAME_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensures that a directory exists, creating it if necessary.
    
    Args:
        directory_path: The path of the directory to ensure exists
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.info(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {str(e)}")
        return False


def generate_unique_filename(original_filename: str) -> str:
    """
    Generates a unique filename for storing documents.
    
    Args:
        original_filename: The original filename
        
    Returns:
        str: Unique filename with original extension
    """
    # Extract the file extension
    ext = get_file_extension(original_filename)
    
    # Generate a UUID for uniqueness
    unique_id = str(uuid.uuid4())
    
    # Get the base name without directory path and sanitize it
    base_name = sanitize_filename(os.path.basename(original_filename))
    
    # Remove extension from base name if present
    if ext and base_name.lower().endswith(f".{ext.lower()}"):
        base_name = base_name[:-len(ext)-1]
    
    # Combine sanitized name, UUID, and extension
    if ext:
        return f"{base_name}_{unique_id}.{ext}"
    return f"{base_name}_{unique_id}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to ensure it's safe for storage.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Extract just the filename without directory path
    filename = os.path.basename(filename)
    
    # Replace unsafe characters with underscores
    sanitized = ''.join(c if c in SAFE_FILENAME_CHARS else '_' for c in filename)
    
    # Limit filename length to reasonable maximum (255 is often the filesystem limit)
    max_length = 200  # Conservative limit
    if len(sanitized) > max_length:
        # Preserve extension if present
        ext = get_file_extension(sanitized)
        if ext:
            base = sanitized[:-len(ext)-1]
            sanitized = f"{base[:max_length-len(ext)-1]}.{ext}"
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized


def get_file_extension(filename: str) -> str:
    """
    Extracts the file extension from a filename.
    
    Args:
        filename: The filename to extract extension from
        
    Returns:
        str: File extension (lowercase) or empty string if none
    """
    # Get the extension without the dot
    try:
        ext = os.path.splitext(filename)[1].lstrip('.')
        return ext.lower()
    except (AttributeError, IndexError):
        return ""


def is_safe_path(base_path: str, file_path: str) -> bool:
    """
    Checks if a file path is safe (no directory traversal).
    
    Args:
        base_path: The base directory path
        file_path: The file path to check
        
    Returns:
        bool: True if path is safe, False otherwise
    """
    # Convert both paths to absolute paths
    base_abs = os.path.abspath(base_path)
    file_abs = os.path.abspath(os.path.join(base_path, file_path))
    
    # Check if file_path is within or equal to base_path
    return os.path.commonpath([base_abs]) == os.path.commonpath([base_abs, file_abs])


def get_absolute_path(path: str) -> str:
    """
    Gets the absolute path of a file or directory.
    
    Args:
        path: The path to convert to absolute
        
    Returns:
        str: Absolute path
    """
    # Convert to absolute path and normalize
    abs_path = os.path.abspath(path)
    norm_path = os.path.normpath(abs_path)
    return norm_path


def is_pdf_file(file_or_data: Union[str, bytes]) -> bool:
    """
    Checks if a file is a valid PDF based on content.
    
    Args:
        file_or_data: Either a file path (str) or file content (bytes)
        
    Returns:
        bool: True if file is a valid PDF, False otherwise
    """
    try:
        mime = None
        if isinstance(file_or_data, str):
            # File path provided
            if not os.path.isfile(file_or_data):
                return False
            mime = magic.from_file(file_or_data, mime=True)
        elif isinstance(file_or_data, bytes):
            # File content provided
            mime = magic.from_buffer(file_or_data, mime=True)
        else:
            return False
        
        return mime == 'application/pdf'
    except Exception as e:
        logger.error(f"Error checking PDF file: {str(e)}")
        return False


def get_file_size(file_path: str) -> int:
    """
    Gets the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: File size in bytes
        
    Raises:
        HTTPException: If file not found
    """
    try:
        if os.path.isfile(file_path):
            return os.path.getsize(file_path)
        raise HTTPException(status_code=404, detail=f"File not found: {os.path.basename(file_path)}")
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving file size")


def delete_file(file_path: str) -> bool:
    """
    Deletes a file from the filesystem.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        logger.warning(f"File not found for deletion: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False


def copy_file(source_path: str, destination_path: str) -> bool:
    """
    Copies a file to a new location.
    
    Args:
        source_path: Path to the source file
        destination_path: Path to the destination location
        
    Returns:
        bool: True if copy was successful, False otherwise
    """
    try:
        if not os.path.isfile(source_path):
            logger.warning(f"Source file not found for copying: {source_path}")
            return False
        
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination_path)
        if dest_dir and not ensure_directory_exists(dest_dir):
            return False
        
        # Copy file with metadata
        shutil.copy2(source_path, destination_path)
        logger.info(f"Copied file from {source_path} to {destination_path}")
        return True
    except Exception as e:
        logger.error(f"Error copying file from {source_path} to {destination_path}: {str(e)}")
        return False


def move_file(source_path: str, destination_path: str) -> bool:
    """
    Moves a file to a new location.
    
    Args:
        source_path: Path to the source file
        destination_path: Path to the destination location
        
    Returns:
        bool: True if move was successful, False otherwise
    """
    try:
        if not os.path.isfile(source_path):
            logger.warning(f"Source file not found for moving: {source_path}")
            return False
        
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination_path)
        if dest_dir and not ensure_directory_exists(dest_dir):
            return False
        
        # Move file
        shutil.move(source_path, destination_path)
        logger.info(f"Moved file from {source_path} to {destination_path}")
        return True
    except Exception as e:
        logger.error(f"Error moving file from {source_path} to {destination_path}: {str(e)}")
        return False


def create_temp_directory(prefix: Optional[str] = None) -> str:
    """
    Creates a temporary directory for processing files.
    
    Args:
        prefix: Optional prefix for the directory name
        
    Returns:
        str: Path to the created temporary directory
        
    Raises:
        HTTPException: If directory creation fails
    """
    try:
        # Generate a unique directory name
        prefix = prefix or "docprocessing_"
        unique_id = str(uuid.uuid4())
        temp_dir = os.path.join(os.path.join(os.getcwd(), "tmp"), f"{prefix}{unique_id}")
        
        # Create the directory
        ensure_directory_exists(temp_dir)
        logger.info(f"Created temporary directory: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"Error creating temporary directory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create temporary processing directory")


def clean_temp_directory(directory_path: str) -> bool:
    """
    Cleans up a temporary directory and its contents.
    
    Args:
        directory_path: Path to the temporary directory
        
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    try:
        if os.path.isdir(directory_path):
            shutil.rmtree(directory_path)
            logger.info(f"Cleaned up temporary directory: {directory_path}")
            return True
        logger.warning(f"Directory not found for cleanup: {directory_path}")
        return False
    except Exception as e:
        logger.error(f"Error cleaning temporary directory {directory_path}: {str(e)}")
        return False