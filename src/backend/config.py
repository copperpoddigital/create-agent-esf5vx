"""
Root configuration module for the Document Management and AI Chatbot System.

This module serves as the central entry point for accessing application settings
throughout the system. It imports and re-exports settings from the core configuration
modules, making them easily accessible to all components.
"""
import os
import logging
from pathlib import Path

# Import settings from core config module
from app.core.config import (
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

# Set up logging
logger = logging.getLogger(__name__)

# Define base directory and environment file path
BASE_DIR = Path(__file__).parent.absolute()
ENV_FILE = os.path.join(BASE_DIR, '.env')


def load_env_file() -> bool:
    """
    Loads environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env file was loaded, False otherwise
    """
    if os.path.exists(ENV_FILE):
        logger.info(f".env file found at {ENV_FILE}")
        return True
    else:
        logger.debug(f"No .env file found at {ENV_FILE}, using default/environment settings")
        return False


def get_app_settings() -> dict:
    """
    Returns a consolidated dictionary of all application settings.
    
    This function aggregates all settings from different components into
    a single dictionary, making it easy to access all settings in one place.
    
    Returns:
        dict: Dictionary containing all application settings
    """
    app_settings = {
        # General application settings
        "app": {
            "env": settings.ENV,
            "name": settings.APP_NAME,
            "api_prefix": settings.API_V1_PREFIX,
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
            "cors_origins": settings.CORS_ALLOW_ORIGINS,
            "rate_limit": settings.RATE_LIMIT_PER_MINUTE,
        },
        
        # Database settings
        "database": {
            "uri": db_settings.SQLALCHEMY_DATABASE_URI,
            "pool_size": db_settings.POOL_SIZE,
            "max_overflow": db_settings.MAX_OVERFLOW,
            "pool_timeout": db_settings.POOL_TIMEOUT,
            "echo_sql": db_settings.ECHO_SQL,
        },
        
        # Security settings
        "security": {
            "jwt_algorithm": security_settings.JWT_ALGORITHM,
            "access_token_expire_minutes": security_settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": security_settings.REFRESH_TOKEN_EXPIRE_DAYS,
        },
        
        # Vector search settings
        "vector_search": {
            "index_path": vector_settings.VECTOR_INDEX_PATH,
            "dimension": vector_settings.VECTOR_DIMENSION,
            "index_type": vector_settings.INDEX_TYPE,
            "default_top_k": vector_settings.DEFAULT_TOP_K,
            "similarity_threshold": vector_settings.SIMILARITY_THRESHOLD,
        },
        
        # LLM settings
        "llm": {
            "model": llm_settings.LLM_MODEL,
            "temperature": llm_settings.TEMPERATURE,
            "max_tokens": llm_settings.MAX_TOKENS,
            "context_window_size": llm_settings.CONTEXT_WINDOW_SIZE,
        },
        
        # Document settings
        "document": {
            "storage_path": document_settings.DOCUMENT_STORAGE_PATH,
            "max_size_mb": document_settings.MAX_DOCUMENT_SIZE_MB,
            "allowed_types": document_settings.ALLOWED_DOCUMENT_TYPES,
            "chunk_size": document_settings.CHUNK_SIZE,
            "chunk_overlap": document_settings.CHUNK_OVERLAP,
        },
        
        # Feedback settings
        "feedback": {
            "enable_feedback": feedback_settings.ENABLE_FEEDBACK,
            "enable_rl": feedback_settings.ENABLE_REINFORCEMENT_LEARNING,
            "batch_size": feedback_settings.FEEDBACK_BATCH_SIZE,
            "update_frequency_hours": feedback_settings.RL_UPDATE_FREQUENCY_HOURS,
        },
    }
    
    return app_settings


# Check if .env file exists
load_env_file()