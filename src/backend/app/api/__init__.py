"""
Initialization module for the API package of the Document Management and AI Chatbot System.
This module exports the main API router and initializes the API package structure,
serving as the entry point for all API-related functionality.
"""

from fastapi import APIRouter  # version 0.95.0+ - High-performance API framework.

from .router import api_router as main_router  # Import router module for API configuration
from .dependencies import get_current_user, get_current_active_user, get_current_admin_user, require_role  # Import authentication and authorization dependencies
from ..core.logging import get_logger  # Import logging utility for API package

# Initialize logger
logger = get_logger(__name__)

# Create main API router
api_router = APIRouter()


# Include all versioned API routers
api_router.include_router(main_router)

# Export the main API router
__all__ = ["api_router"]

# Export authentication and authorization dependencies for API routes
dependencies = {
    "get_current_user": get_current_user,
    "get_current_active_user": get_current_active_user,
    "get_current_admin_user": get_current_admin_user,
    "require_role": require_role,
}