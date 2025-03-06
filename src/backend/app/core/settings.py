import os
import secrets
import logging
from typing import List, Dict, Any, Optional
from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logger for the settings module
logger = logging.getLogger(__name__)

class BaseSettings(BaseSettings):
    """Base settings class that provides common configuration for all settings classes."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

class DatabaseSettings(BaseSettings):
    """Settings class for database configuration."""
    
    SQLALCHEMY_DATABASE_URI: str = "postgresql://postgres:postgres@localhost:5432/docmanagement"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_TIMEOUT: int = 30
    ECHO_SQL: bool = False
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        case_sensitive=True,
        extra="ignore",
    )

class SecuritySettings(BaseSettings):
    """Settings class for security and authentication configuration."""
    
    JWT_SECRET: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 10
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        case_sensitive=True,
        extra="ignore",
    )

class VectorSearchSettings(BaseSettings):
    """Settings class for vector search configuration."""
    
    VECTOR_INDEX_PATH: str = "data/faiss_index"
    VECTOR_DIMENSION: int = 768  # Default for Sentence Transformers
    INDEX_TYPE: str = "IVFFlat"
    DEFAULT_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    NLIST: int = 100  # Number of clusters for IVF
    NPROBE: int = 10  # Number of clusters to visit during search
    
    model_config = SettingsConfigDict(
        env_prefix="VECTOR_",
        case_sensitive=True,
        extra="ignore",
    )

class LLMSettings(BaseSettings):
    """Settings class for LLM integration configuration."""
    
    OPENAI_API_KEY: SecretStr = Field(
        default=None, 
        description="OpenAI API Key for LLM integration. Required for production use."
    )
    LLM_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 500
    CONTEXT_WINDOW_SIZE: int = 4000
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    USE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        case_sensitive=True,
        extra="ignore",
    )
    
    @field_validator("OPENAI_API_KEY", mode="before")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the OpenAI API key is set in production environment."""
        if not v and os.getenv("APP_ENV") == "production":
            logger.warning("OpenAI API key not set in production environment")
        return v

class DocumentSettings(BaseSettings):
    """Settings class for document processing configuration."""
    
    DOCUMENT_STORAGE_PATH: str = "data/documents"
    MAX_DOCUMENT_SIZE_MB: int = 10
    ALLOWED_DOCUMENT_TYPES: List[str] = ["application/pdf"]
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    model_config = SettingsConfigDict(
        env_prefix="DOCUMENT_",
        case_sensitive=True,
        extra="ignore",
    )

class FeedbackSettings(BaseSettings):
    """Settings class for feedback and reinforcement learning configuration."""
    
    ENABLE_FEEDBACK: bool = True
    ENABLE_REINFORCEMENT_LEARNING: bool = True
    FEEDBACK_BATCH_SIZE: int = 100
    RL_UPDATE_FREQUENCY_HOURS: int = 24
    LEARNING_RATE: float = 0.001
    
    model_config = SettingsConfigDict(
        env_prefix="FEEDBACK_",
        case_sensitive=True,
        extra="ignore",
    )

class Settings(BaseSettings):
    """Main settings class that combines all component-specific settings."""
    
    ENV: str = "development"
    APP_NAME: str = "Document Management and AI Chatbot"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default_factory=lambda: os.getenv("APP_ENV", "development") != "production")
    LOG_LEVEL: str = Field(
        default_factory=lambda: "DEBUG" if os.getenv("APP_ENV", "development") != "production" else "INFO"
    )
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Component-specific settings
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    vector_search: VectorSearchSettings = Field(default_factory=VectorSearchSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    document: DocumentSettings = Field(default_factory=DocumentSettings)
    feedback: FeedbackSettings = Field(default_factory=FeedbackSettings)
    
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=True,
        extra="ignore",
    )


# Create a singleton settings instance
settings = Settings()

# Export settings classes for type hinting in other modules
__all__ = [
    "Settings", 
    "DatabaseSettings", 
    "SecuritySettings", 
    "VectorSearchSettings",
    "LLMSettings",
    "DocumentSettings", 
    "FeedbackSettings",
    "settings"
]