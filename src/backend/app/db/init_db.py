"""
Database initialization module that creates initial database tables and populates them with
required seed data for the Document Management and AI Chatbot System. This module is used
during application startup and for testing environments to ensure a consistent database state.
"""
import logging
import uuid
from datetime import datetime

# SQLAlchemy imports
from sqlalchemy.exc import SQLAlchemyError

# Internal imports
from .base import Base  # Import all models to create database tables
from .session import engine, get_db
from ..models.user import User, UserRole
from ..crud.crud_user import user
from ..core.config import settings
from ..core.security import get_password_hash

# Set up module logger
logger = logging.getLogger(__name__)


def create_tables() -> None:
    """
    Creates all database tables defined in the models.
    
    This function uses SQLAlchemy's metadata.create_all() method to create all
    database tables that have been defined in the models imported via base.py.
    
    Raises:
        SQLAlchemyError: If there's an error creating the tables
    """
    try:
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def create_initial_admin(db) -> None:
    """
    Creates an initial admin user if one doesn't already exist.
    
    Args:
        db (sqlalchemy.orm.Session): SQLAlchemy database session
        
    Raises:
        SQLAlchemyError: If there's an error creating the admin user
    """
    try:
        # Check if admin user already exists
        admin_email = settings.FIRST_ADMIN_EMAIL
        admin_user = user.get_by_email(db, admin_email)
        
        if not admin_user:
            logger.info(f"Creating initial admin user with email: {admin_email}")
            
            # Create user with admin role
            admin_data = {
                "id": uuid.uuid4(),
                "username": settings.FIRST_ADMIN_USERNAME,
                "email": settings.FIRST_ADMIN_EMAIL,
                "password": settings.FIRST_ADMIN_PASSWORD,
                "role": UserRole.admin,
                "is_active": True
            }
            
            # Use CRUD operation to create user with proper password hashing
            admin_user = user.create(db, obj_in=admin_data)
            
            logger.info(f"Admin user '{admin_user.username}' created successfully")
        else:
            logger.info(f"Admin user '{admin_user.username}' already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.rollback()
        raise


def init_db() -> None:
    """
    Initializes the database with tables and seed data.
    
    This function is called during application startup to ensure
    the database is properly set up with all required tables and initial data.
    
    Raises:
        Exception: If there's an error during database initialization
    """
    try:
        logger.info("Beginning database initialization")
        
        # Create database tables
        create_tables()
        
        # Create initial admin user
        with get_db() as db:
            create_initial_admin(db)
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def init_test_db(db) -> None:
    """
    Initializes a test database with tables and test data.
    
    This function is used for testing to create a consistent test database
    with predefined test data.
    
    Args:
        db (sqlalchemy.orm.Session): SQLAlchemy database session
        
    Raises:
        Exception: If there's an error during test database initialization
    """
    try:
        logger.info("Initializing test database")
        
        # Create initial admin user
        create_initial_admin(db)
        
        # Create additional test data as needed
        # (Additional test data creation would go here)
        
        logger.info("Test database initialization completed successfully")
    except Exception as e:
        logger.error(f"Test database initialization failed: {str(e)}")
        raise