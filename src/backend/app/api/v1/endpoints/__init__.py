"""
API v1 Endpoints Package.

This package contains all the API endpoint modules for version 1 of the API.
Each module defines a FastAPI router with endpoints for specific functionality.

The package implements URI-based versioning to support multiple API versions
and organizes endpoints into logical modules for better maintainability.
"""

from app.api.v1.endpoints import health
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import query
from app.api.v1.endpoints import feedback

# Define explicitly exported names
__all__ = [
    'health',
    'auth',
    'documents',
    'query',
    'feedback',
]