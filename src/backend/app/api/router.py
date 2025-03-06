"""
Central router configuration for the Document Management and AI Chatbot System.
This file aggregates all API endpoint routers from different modules and exposes them through a single API router. It serves as the main entry point for all API routes in the application.
"""

from fastapi import APIRouter  # version 0.95.0+ - High-performance API framework.
from .core.logging import get_logger  # Import logging utility for router configuration
from .api import v1 as v1_module  # Import the configured v1 API router with all endpoints

# Initialize logger
logger = get_logger(__name__)

# Create main API router
api_router = APIRouter()


def configure_routes() -> None:
    """
    Configures the main API router by including all versioned API routers
    """
    # Include the v1 API router from app.api.v1
    api_router.include_router(v1_module.api_router)

    # Log that routes have been configured
    logger.info("Configured API routes")


configure_routes()

# Export the main API router
__all__ = ["api_router"]