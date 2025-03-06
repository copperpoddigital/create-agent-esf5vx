"""
Initializes the v1 API router for the Document Management and AI Chatbot System.
This module aggregates all endpoint routers from the v1 API version and exports a single router that can be included in the main API router. It serves as the central point for organizing all v1 API endpoints.
"""

from fastapi import APIRouter  # version 0.95.0+
from ....core.logging import get_logger  # Import logging utility for router configuration
from .endpoints import health as health_router  # Import health check endpoints router
from .endpoints import auth as auth_router  # Import authentication endpoints router
from .endpoints import documents as documents_router  # Import document management endpoints router
from .endpoints import query as query_router  # Import vector search and query endpoints router
from .endpoints import feedback as feedback_router  # Import feedback and reinforcement learning endpoints router

# Initialize logger
logger = get_logger(__name__)

# Create main API router with version prefix
api_router = APIRouter(prefix="/v1")

def configure_routes():
    """
    Configures the v1 API router by including all endpoint routers
    """
    # Include the health_router under the v1 API router
    api_router.include_router(health_router.router)
    
    # Include the auth_router under the v1 API router
    api_router.include_router(auth_router.router)
    
    # Include the documents_router under the v1 API router
    api_router.include_router(documents_router.router)
    
    # Include the query_router under the v1 API router
    api_router.include_router(query_router.router)
    
    # Include the feedback_router under the v1 API router
    api_router.include_router(feedback_router.router)
    
    # Log that v1 routes have been configured
    logger.info("Configured v1 API routes")

configure_routes()