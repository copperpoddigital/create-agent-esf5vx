"""
Main initialization file for the Document Management and AI Chatbot System application package.
This file serves as the entry point for the application module, exposing core components,
models, services, and utilities to provide a clean and organized import interface for the
entire application.
"""

# Import core module for configuration, settings, and security utilities
from .core import core

# Import database module for ORM models and database access
from .db import db

# Import database models for all entities in the system
from .models import models

# Import Pydantic schemas for request/response validation
from .schemas import schemas

# Import CRUD operations for database entities
from .crud import crud

# Import API routes and endpoints
from .api import api

# Import service components for business logic
from .services import services

# Import vector store components for similarity search
from .vector_store import vector_store

# Import utility functions and helpers
from .utils import utils

# Define the version of the application
__version__ = "1.0.0"

# Export core module for application-wide configuration and utilities
__all__ = [
    "core",
    "db",
    "models",
    "schemas",
    "crud",
    "api",
    "services",
    "vector_store",
    "utils",
    "__version__",
]