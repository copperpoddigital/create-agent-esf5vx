"""
Main entry point for the Document Management and AI Chatbot System FastAPI application.
This file initializes the FastAPI app, configures middleware, sets up logging,
initializes the database, and includes API routes. It also handles application
startup and shutdown events.
"""
import os  # Operating system interfaces
import sys  # System-specific parameters and functions
import logging  # Logging facility for Python
import time  # Time access and conversions for performance monitoring

# Third-party libraries
from fastapi import FastAPI  # version 0.95.0+ - High-performance API framework
from fastapi.middleware.cors import CORSMiddleware  # version 0.26.0+ - CORS middleware
from starlette.middleware.base import BaseHTTPMiddleware  # version 0.26.0+ - Base middleware class
import uvicorn  # version 0.20.0+ - ASGI server for running the FastAPI application
from slowapi import Limiter, _rate_limit_exceeded_handler  # version 0.1.7+ - Rate limiting middleware
from slowapi.util import get_remote_address  # version 0.1.7+ - Utility function for rate limiting
from slowapi.errors import RateLimitExceeded  # version 0.1.7+ - Exception for rate limiting

# Internal modules
from app.core.config import settings  # Import application settings for configuration
from app.core.logging import setup_logging, get_logger, log_request, log_response  # Import logging setup function
from app.db.init_db import init_db  # Import database initialization function
from app.api.router import api_router  # Import main API router with all routes
from app.services.vector_search import get_vector_store  # Import function to get vector store instance

# Initialize logger for the main module
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI application instance
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Configure exception handler for rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

async def request_logging_middleware(request, call_next):
    """
    Middleware function to log HTTP requests and responses.

    Args:
        request (starlette.requests.Request): HTTP request object
        call_next (callable): Next middleware or route handler

    Returns:
        starlette.responses.Response: HTTP response object
    """
    start_time = time.time()
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
    }
    log_request(request_info)

    response = await call_next(request)

    process_time = time.time() - start_time
    response_info = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "process_time": process_time,
    }
    response.headers["X-Process-Time"] = str(process_time)
    log_response(response_info)

    return response

def configure_app():
    """
    Configures the FastAPI application with middleware and routes.

    Returns:
        fastapi.FastAPI: Configured FastAPI application
    """
    # Add CORS middleware to handle cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting middleware to protect API endpoints
    app.middleware("http")(limiter.limit(rate_limit=settings.RATE_LIMIT_PER_MINUTE)(request_logging_middleware))

    # Include API router with prefix from settings
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Register startup event handler for database initialization
    @app.on_event("startup")
    async def startup_db():
        """Initializes the database on application startup"""
        try:
            logger.info("Starting database initialization")
            init_db()
            logger.info("Successfully initialized database")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            sys.exit(1)

    # Register startup event handler for vector store initialization
    @app.on_event("startup")
    async def startup_vector_store():
        """Initializes the vector store on application startup"""
        try:
            logger.info("Starting vector store initialization")
            get_vector_store()
            logger.info("Successfully initialized vector store")
        except Exception as e:
            logger.error(f"Vector store initialization failed: {e}")
            sys.exit(1)

    # Register shutdown event handler for vector store saving
    @app.on_event("shutdown")
    async def shutdown_vector_store():
        """Saves the vector store state on application shutdown"""
        try:
            logger.info("Starting vector store saving")
            vector_store = get_vector_store()
            vector_store.save()
            logger.info("Successfully saved vector store")
        except Exception as e:
            logger.error(f"Vector store saving failed: {e}")

    return app

def main():
    """
    Main function to run the application with Uvicorn.
    """
    # Set up logging using the configuration
    setup_logging()

    # Configure the FastAPI application
    configured_app = configure_app()

    # Run the application with Uvicorn if executed as main script
    if __name__ == "__main__":
        # Use host 0.0.0.0 to listen on all interfaces
        host = "0.0.0.0"

        # Use port from environment variable or default to 8000
        port = int(os.environ.get("PORT", 8000))

        # Enable reload in debug mode
        reload = settings.DEBUG

        uvicorn.run(configured_app, host=host, port=port, reload=reload)

# Execute main function
main()