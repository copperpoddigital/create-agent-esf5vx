"""
Utility module that provides validation functions for data validation across 
the Document Management and AI Chatbot System.

This module implements validation for document files, query parameters, feedback data,
and other input validation to ensure data integrity and security.
"""

import os
import re
import magic  # version 0.4.27+
import logging
import uuid
from typing import Optional, Tuple, Union
from fastapi import HTTPException
from pydantic import ValidationError as PydanticValidationError

from ..core.config import document_settings

# Configure logger for this module
logger = logging.getLogger(__name__)

# Regular expressions for validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
FILENAME_REGEX = re.compile(r'^[\w\-. ]+$')
UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

# Constants for validation
MAX_QUERY_LENGTH = 1000
MIN_QUERY_LENGTH = 3
MAX_FEEDBACK_RATING = 5
MIN_FEEDBACK_RATING = 1
DEFAULT_SKIP = 0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class ValidationError(Exception):
    """
    Custom exception class for validation errors.
    
    Attributes:
        message (str): Error message describing the validation issue
        status_code (int): HTTP status code to return
    """
    
    def __init__(self, message: str, status_code: int = 400):
        """
        Initialize a ValidationError with message and status code.
        
        Args:
            message: Error message describing the validation issue
            status_code: HTTP status code to return (default: 400 Bad Request)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        
    def __str__(self) -> str:
        """
        Returns string representation of the error.
        
        Returns:
            str: Formatted error message with status code
        """
        return f"Validation Error ({self.status_code}): {self.message}"


def validate_document_file(file_content: bytes, filename: str) -> bool:
    """
    Validates an uploaded document file for size, format, and content.
    
    Args:
        file_content: Binary content of the uploaded file
        filename: Name of the uploaded file
    
    Returns:
        bool: True if file is valid
        
    Raises:
        HTTPException: If validation fails with appropriate status code and detail
    """
    logger.debug(f"Validating document file: {filename}")
    
    # Check if file content is not empty
    if not file_content:
        logger.warning(f"Empty file content for {filename}")
        raise HTTPException(
            status_code=400,
            detail="File content is empty"
        )
    
    # Validate file size against MAX_DOCUMENT_SIZE_MB
    max_size_bytes = document_settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if len(file_content) > max_size_bytes:
        logger.warning(f"File {filename} exceeds max size of {document_settings.MAX_DOCUMENT_SIZE_MB}MB")
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {document_settings.MAX_DOCUMENT_SIZE_MB}MB"
        )
    
    # Detect file MIME type using magic library
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
        logger.debug(f"Detected MIME type for {filename}: {mime_type}")
        
        # Validate MIME type against ALLOWED_DOCUMENT_TYPES
        if mime_type not in document_settings.ALLOWED_DOCUMENT_TYPES:
            logger.warning(f"Unsupported file type {mime_type} for {filename}")
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type. Allowed types: {', '.join(document_settings.ALLOWED_DOCUMENT_TYPES)}"
            )
    except Exception as e:
        logger.error(f"Error detecting MIME type for {filename}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Error analyzing file content"
        )
    
    # Validate filename using FILENAME_REGEX
    if not FILENAME_REGEX.match(filename):
        logger.warning(f"Invalid filename format: {filename}")
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Only alphanumeric characters, spaces, dots, underscores, and hyphens are allowed"
        )
    
    logger.debug(f"Document file {filename} passed all validations")
    return True


def validate_query_text(query_text: str) -> str:
    """
    Validates search query text for length and content.
    
    Args:
        query_text: The search query to validate
    
    Returns:
        str: Sanitized and validated query text
        
    Raises:
        HTTPException: If validation fails with appropriate status code and detail
    """
    logger.debug("Validating query text")
    
    # Check if query text is not None or empty
    if not query_text or query_text.strip() == "":
        logger.warning("Empty query text")
        raise HTTPException(
            status_code=400,
            detail="Query text cannot be empty"
        )
    
    # Sanitize query text by removing excessive whitespace
    sanitized_query = sanitize_string(query_text)
    
    # Validate query length is between MIN_QUERY_LENGTH and MAX_QUERY_LENGTH
    if len(sanitized_query) < MIN_QUERY_LENGTH:
        logger.warning(f"Query text too short: {len(sanitized_query)} chars")
        raise HTTPException(
            status_code=400,
            detail=f"Query text must be at least {MIN_QUERY_LENGTH} characters long"
        )
    
    if len(sanitized_query) > MAX_QUERY_LENGTH:
        logger.warning(f"Query text too long: {len(sanitized_query)} chars")
        raise HTTPException(
            status_code=400,
            detail=f"Query text cannot exceed {MAX_QUERY_LENGTH} characters"
        )
    
    logger.debug(f"Query text validated successfully: {sanitized_query[:50]}...")
    return sanitized_query


def validate_email(email: str) -> str:
    """
    Validates email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        str: Validated email address (lowercase)
        
    Raises:
        ValueError: If email format is invalid
    """
    logger.debug("Validating email address")
    
    # Check if email is not None or empty
    if not email or email.strip() == "":
        logger.warning("Empty email address")
        raise ValueError("Email address cannot be empty")
    
    # Validate email format using EMAIL_REGEX
    if not EMAIL_REGEX.match(email):
        logger.warning(f"Invalid email format: {email}")
        raise ValueError("Invalid email address format")
    
    # Return lowercase email if valid
    validated_email = email.lower().strip()
    logger.debug(f"Email validated successfully: {validated_email}")
    return validated_email


def validate_password(password: str) -> bool:
    """
    Validates password strength based on security settings.
    
    Args:
        password: Password to validate
    
    Returns:
        bool: True if password meets requirements
        
    Raises:
        ValueError: With specific message about which requirement failed
    """
    from ..core.config import security_settings
    
    logger.debug("Validating password strength")
    
    # Check if password meets minimum length requirement
    if len(password) < security_settings.PASSWORD_MIN_LENGTH:
        logger.warning("Password too short")
        raise ValueError(
            f"Password must be at least {security_settings.PASSWORD_MIN_LENGTH} characters long"
        )
    
    # Check for uppercase characters if required by settings
    if security_settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        logger.warning("Password missing uppercase character")
        raise ValueError("Password must contain at least one uppercase letter")
    
    # Check for lowercase characters if required by settings
    if security_settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        logger.warning("Password missing lowercase character")
        raise ValueError("Password must contain at least one lowercase letter")
    
    # Check for digit characters if required by settings
    if security_settings.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        logger.warning("Password missing digit character")
        raise ValueError("Password must contain at least one digit")
    
    # Check for special characters if required by settings
    if security_settings.PASSWORD_REQUIRE_SPECIAL and not any(not c.isalnum() for c in password):
        logger.warning("Password missing special character")
        raise ValueError("Password must contain at least one special character")
    
    logger.debug("Password passed all strength validations")
    return True


def validate_feedback_rating(rating: int) -> int:
    """
    Validates feedback rating is within acceptable range.
    
    Args:
        rating: Feedback rating (typically 1-5)
    
    Returns:
        int: Validated rating
        
    Raises:
        ValueError: If rating is invalid
    """
    logger.debug(f"Validating feedback rating: {rating}")
    
    # Check if rating is an integer between MIN_FEEDBACK_RATING and MAX_FEEDBACK_RATING
    if not isinstance(rating, int):
        logger.warning(f"Rating is not an integer: {type(rating)}")
        raise ValueError(f"Rating must be an integer between {MIN_FEEDBACK_RATING} and {MAX_FEEDBACK_RATING}")
    
    if rating < MIN_FEEDBACK_RATING or rating > MAX_FEEDBACK_RATING:
        logger.warning(f"Rating out of acceptable range: {rating}")
        raise ValueError(f"Rating must be between {MIN_FEEDBACK_RATING} and {MAX_FEEDBACK_RATING}")
    
    logger.debug(f"Rating validated successfully: {rating}")
    return rating


def sanitize_string(text: str) -> str:
    """
    Sanitizes a string by removing excessive whitespace and potentially dangerous characters.
    
    Args:
        text: String to sanitize
    
    Returns:
        str: Sanitized string
    """
    if not text:
        return ""
    
    # Remove leading and trailing whitespace
    sanitized = text.strip()
    
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Remove or escape potentially dangerous characters
    # This is a basic implementation - consider more comprehensive solutions for production
    sanitized = re.sub(r'[<>]', '', sanitized)
    
    return sanitized


def validate_uuid(uuid_str: str) -> bool:
    """
    Validates that a string is a valid UUID format.
    
    Args:
        uuid_str: String to validate as UUID
    
    Returns:
        bool: True if valid UUID format, False otherwise
    """
    logger.debug(f"Validating UUID: {uuid_str}")
    
    if not uuid_str:
        logger.warning("Empty UUID string")
        return False
    
    # Check if string matches UUID pattern
    if not UUID_REGEX.match(uuid_str.lower()):
        logger.warning(f"Invalid UUID format: {uuid_str}")
        return False
    
    # Additional validation by trying to parse it
    try:
        uuid.UUID(uuid_str)
        logger.debug(f"UUID validated successfully: {uuid_str}")
        return True
    except ValueError:
        logger.warning(f"UUID validation failed: {uuid_str}")
        return False


def validate_pagination_params(skip: Optional[int] = None, limit: Optional[int] = None) -> Tuple[int, int]:
    """
    Validates pagination parameters for list endpoints.
    
    Args:
        skip: Number of items to skip (default: 0)
        limit: Maximum number of items to return (default: 20, max: 100)
    
    Returns:
        tuple: Tuple of validated (skip, limit) values
    """
    logger.debug(f"Validating pagination params: skip={skip}, limit={limit}")
    
    # Set default values if parameters are None
    validated_skip = DEFAULT_SKIP if skip is None else skip
    validated_limit = DEFAULT_LIMIT if limit is None else limit
    
    # Ensure skip is not negative
    if validated_skip < 0:
        logger.warning(f"Negative skip value: {validated_skip}")
        validated_skip = DEFAULT_SKIP
    
    # Ensure limit is between 1 and MAX_LIMIT
    if validated_limit < 1:
        logger.warning(f"Limit too small: {validated_limit}")
        validated_limit = DEFAULT_LIMIT
    elif validated_limit > MAX_LIMIT:
        logger.warning(f"Limit too large: {validated_limit}")
        validated_limit = MAX_LIMIT
    
    logger.debug(f"Pagination params validated: skip={validated_skip}, limit={validated_limit}")
    return validated_skip, validated_limit