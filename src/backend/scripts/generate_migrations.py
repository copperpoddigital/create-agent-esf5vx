#!/usr/bin/env python3
"""
Script to automate the generation of database migration scripts.

This utility simplifies the creation of Alembic migration revisions by providing
a command-line interface with options for migration message and autogeneration.
It supports the database versioning strategy by implementing version-controlled
migrations using Alembic with SQLAlchemy, ensuring data integrity during schema
changes by providing both upgrade and downgrade paths.
"""
import os
import sys
import argparse
import logging
from alembic.config import Config
from alembic import command

# Set up logger
logger = logging.getLogger(__name__)


def setup_logging():
    """
    Configures logging for the migration script generator.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)


def parse_arguments():
    """
    Parses command line arguments for migration options.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate Alembic database migration scripts"
    )
    
    parser.add_argument(
        "--message", "-m",
        required=True,
        help="Migration message (required)"
    )
    
    parser.add_argument(
        "--autogenerate", "-a",
        action="store_true",
        help="Enable automatic migration generation based on model changes"
    )
    
    parser.add_argument(
        "--sql", "-s",
        action="store_true",
        help="Generate SQL script without applying changes"
    )
    
    return parser.parse_args()


def setup_alembic_config():
    """
    Creates and configures an Alembic configuration object.
    
    Returns:
        alembic.config.Config: Configured Alembic config object
    """
    # Get the directory containing the app package
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Build the path to the alembic.ini file
    alembic_ini_path = os.path.join(app_dir, "alembic.ini")
    
    # Create Alembic config from the ini file
    alembic_cfg = Config(alembic_ini_path)
    
    # Set the SQLAlchemy URL in the Alembic config
    from app.core.config import db_settings
    alembic_cfg.set_main_option("sqlalchemy.url", db_settings.SQLALCHEMY_DATABASE_URI)
    
    return alembic_cfg


def generate_migration(args):
    """
    Generates a new migration revision using Alembic.
    
    Args:
        args (argparse.Namespace): Command line arguments
    """
    # Set up Alembic configuration
    alembic_cfg = setup_alembic_config()
    
    # Log migration generation
    logger.info(f"Generating migration with message: {args.message}")
    
    if args.autogenerate:
        logger.info("Using autogeneration based on model changes")
        if args.sql:
            logger.info("Generating SQL script")
            command.revision(
                alembic_cfg,
                message=args.message,
                autogenerate=True,
                sql=True
            )
        else:
            command.revision(
                alembic_cfg,
                message=args.message,
                autogenerate=True
            )
    else:
        logger.info("Creating empty migration")
        command.revision(
            alembic_cfg,
            message=args.message,
            autogenerate=False
        )
    
    logger.info("Migration generation complete")


def main():
    """
    Main entry point for the migration generation script.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Set up logging
    setup_logging()
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Generate migration
        generate_migration(args)
        
        # Return success
        return 0
    except Exception as e:
        logger.error(f"Error generating migration: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Add the parent directory to the Python path to allow imports from the app package
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)
    
    # Import all models to ensure they are registered with SQLAlchemy
    from app.db.base import Base
    
    sys.exit(main())