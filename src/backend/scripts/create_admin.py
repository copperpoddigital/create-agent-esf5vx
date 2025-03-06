#!/usr/bin/env python
"""
Admin User Creation Script

This script allows system administrators to create an initial admin user with full system access,
which is essential for setting up the Document Management and AI Chatbot System.
"""
import argparse  # standard library
import sys  # standard library
import logging  # standard library
import uuid

from ..app.db.session import get_db
from ..app.models.user import User, UserRole
from ..app.schemas.user import UserCreate
from ..app.crud.crud_user import user

# Configure logger
logger = logging.getLogger(__name__)


def setup_logging():
    """
    Configures logging for the script with a consistent format and appropriate level.
    """
    logging_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=logging_format,
        handlers=[logging.StreamHandler()]
    )
    logger.info("Logging configured for admin user creation script")


def parse_arguments():
    """
    Parses command-line arguments for admin user creation.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments including username, email, and password
    """
    parser = argparse.ArgumentParser(
        description='Create an admin user for the Document Management and AI Chatbot System'
    )
    
    parser.add_argument(
        '--username',
        required=True,
        help='Username for the admin user'
    )
    
    parser.add_argument(
        '--email',
        required=True,
        help='Email address for the admin user'
    )
    
    parser.add_argument(
        '--password',
        required=True,
        help='Password for the admin user (must meet strength requirements)'
    )
    
    return parser.parse_args()


def create_admin_user(username: str, email: str, password: str) -> User:
    """
    Creates an admin user with the provided credentials.
    If a user with the given username already exists, returns that user.
    
    Args:
        username: Username for the admin user
        email: Email address for the admin user
        password: Password for the admin user
        
    Returns:
        User: Created or existing admin user
    """
    with get_db() as db:
        # Check if user already exists
        existing_user = user.get_by_username(db, username)
        if existing_user:
            logger.warning(f"User with username '{username}' already exists")
            
            # If user exists but is not admin, we could update them here
            if existing_user.role != UserRole.admin:
                logger.info(f"Updating user '{username}' to admin role")
                updated_user = user.update(db, existing_user, {"role": UserRole.admin})
                return updated_user
            
            return existing_user
        
        # Create a new admin user
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            role=UserRole.admin,
            is_active=True
        )
        
        logger.info(f"Creating new admin user with username '{username}'")
        created_user = user.create(db, user_data)
        return created_user


def main() -> int:
    """
    Main function that runs the admin user creation script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Setup logging
        setup_logging()
        
        # Parse command-line arguments
        args = parse_arguments()
        
        # Create admin user
        admin_user = create_admin_user(
            username=args.username,
            email=args.email,
            password=args.password
        )
        
        # Log success message
        logger.info(f"Admin user created/verified successfully: {admin_user}")
        logger.info(f"Username: {admin_user.username}")
        logger.info(f"Email: {admin_user.email}")
        logger.info(f"Role: {admin_user.role.name}")
        
        return 0  # Success exit code
    
    except Exception as e:
        # Log any exceptions that occur
        logger.error(f"Error creating admin user: {str(e)}", exc_info=True)
        return 1  # Failure exit code


if __name__ == "__main__":
    sys.exit(main())