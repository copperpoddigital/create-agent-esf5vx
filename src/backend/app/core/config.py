"""
Configuration module for the Document Management and AI Chatbot System.

This module initializes and exports application settings instances,
loads settings from environment variables, and provides cached access
to settings through getter functions.
"""
import os
import logging
import functools
from .settings import (
    Settings, 
    DatabaseSettings, 
    SecuritySettings, 
    VectorSearchSettings,
    LLMSettings, 
    DocumentSettings,
    FeedbackSettings
)

# Setup logger for this module
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Constructs a database URL from individual environment variables 
    or returns the full URL if provided.
    
    Returns:
        str: Complete database connection URL
    """
    # If the full database URI is provided, use it
    if os.getenv("SQLALCHEMY_DATABASE_URI"):
        return os.getenv("SQLALCHEMY_DATABASE_URI")
    
    # Otherwise, construct from individual components
    driver = os.getenv("DB_DRIVER", "postgresql")
    username = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "docmanagement")
    
    return f"{driver}://{username}:{password}@{host}:{port}/{database}"


# Initialize settings instances
settings = Settings()
db_settings = DatabaseSettings(SQLALCHEMY_DATABASE_URI=get_database_url())
security_settings = SecuritySettings()
vector_settings = VectorSearchSettings()
llm_settings = LLMSettings()
document_settings = DocumentSettings()
feedback_settings = FeedbackSettings()


@functools.lru_cache()
def get_settings() -> Settings:
    """
    Returns the main application settings instance.
    
    Returns:
        Settings: Main application settings instance
    """
    logger.debug("Retrieving application settings")
    return settings


@functools.lru_cache()
def get_db_settings() -> DatabaseSettings:
    """
    Returns the database settings instance.
    
    Returns:
        DatabaseSettings: Database settings instance
    """
    logger.debug("Retrieving database settings")
    return db_settings


@functools.lru_cache()
def get_security_settings() -> SecuritySettings:
    """
    Returns the security settings instance.
    
    Returns:
        SecuritySettings: Security settings instance
    """
    logger.debug("Retrieving security settings")
    return security_settings


@functools.lru_cache()
def get_vector_settings() -> VectorSearchSettings:
    """
    Returns the vector search settings instance.
    
    Returns:
        VectorSearchSettings: Vector search settings instance
    """
    logger.debug("Retrieving vector search settings")
    return vector_settings


@functools.lru_cache()
def get_llm_settings() -> LLMSettings:
    """
    Returns the LLM settings instance.
    
    Returns:
        LLMSettings: LLM settings instance
    """
    logger.debug("Retrieving LLM settings")
    return llm_settings


@functools.lru_cache()
def get_document_settings() -> DocumentSettings:
    """
    Returns the document settings instance.
    
    Returns:
        DocumentSettings: Document settings instance
    """
    logger.debug("Retrieving document settings")
    return document_settings


@functools.lru_cache()
def get_feedback_settings() -> FeedbackSettings:
    """
    Returns the feedback settings instance.
    
    Returns:
        FeedbackSettings: Feedback settings instance
    """
    logger.debug("Retrieving feedback settings")
    return feedback_settings