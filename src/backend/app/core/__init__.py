"""
Core module for the Document Management and AI Chatbot System.

This module exports essential components for application-wide use including:
- Configuration and settings management
- Security and authentication utilities
- Logging and monitoring infrastructure
- Core application utilities

The core module serves as the foundation for all other application components,
providing consistent interfaces for configuration, security, and logging.
"""

# Import settings classes from settings module
from .settings import (
    Settings,
    DatabaseSettings,
    SecuritySettings,
    VectorSearchSettings,
    LLMSettings,
    DocumentSettings,
    FeedbackSettings,
)

# Import configuration instances and functions from config module
from .config import (
    settings,
    db_settings,
    security_settings,
    vector_settings,
    llm_settings,
    document_settings,
    feedback_settings,
    get_settings,
    get_db_settings,
    get_security_settings,
    get_vector_settings,
    get_llm_settings,
    get_document_settings,
    get_feedback_settings,
)

# Import logging utilities from logging module
from .logging import (
    setup_logging,
    get_logger,
    log_request,
    log_response,
    JsonFormatter,
    RequestIdFilter,
)

# Import security utilities from security module
from .security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_secure_token,
    generate_uuid,
)

# Define explicitly what should be available when using "from app.core import *"
__all__ = [
    # Settings classes
    "Settings",
    "DatabaseSettings",
    "SecuritySettings",
    "VectorSearchSettings",
    "LLMSettings",
    "DocumentSettings",
    "FeedbackSettings",
    
    # Configuration instances
    "settings",
    "db_settings",
    "security_settings",
    "vector_settings",
    "llm_settings",
    "document_settings",
    "feedback_settings",
    
    # Configuration getters
    "get_settings",
    "get_db_settings",
    "get_security_settings",
    "get_vector_settings",
    "get_llm_settings",
    "get_document_settings",
    "get_feedback_settings",
    
    # Logging utilities
    "setup_logging",
    "get_logger",
    "log_request",
    "log_response",
    "JsonFormatter",
    "RequestIdFilter",
    
    # Security utilities
    "verify_password",
    "get_password_hash",
    "validate_password_strength",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "generate_secure_token",
    "generate_uuid",
]