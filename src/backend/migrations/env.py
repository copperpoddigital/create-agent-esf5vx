"""
Alembic environment configuration script for the Document Management and AI Chatbot System.

This script connects Alembic with the application's models and database configuration to 
enable automated schema migrations. It provides functionality for running migrations in 
both 'online' mode (directly applying changes to a database) and 'offline' mode 
(generating SQL scripts without connecting to a database).
"""

import logging
import os
import sys
from alembic import context, config
from sqlalchemy import engine_from_config, pool

# Configure logging for the migration environment
logging.basicConfig(format="%(levelname)-8s [%(asctime)s] %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("alembic.env")

# Add the parent directory to Python path to allow importing from the app module
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import all models via the Base class to ensure they're included in migrations
from app.db.base import Base

# Import database configuration from application settings
from app.core.config import db_settings

# Alembic Config object, which provides access to values in the alembic.ini file
config = context.config

# Use SQLAlchemy metadata from the application models for migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This generates SQL script based on migration directives without actually 
    connecting to the database. The generated commands can be manually run in 
    a database client or saved to a file for later execution.
    
    Returns:
        None: No return value
    """
    # Get database URL from Alembic config or application settings
    url = config.get_main_option("sqlalchemy.url", db_settings.SQLALCHEMY_DATABASE_URI)
    
    # Configure Alembic context with database URL and target metadata
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    # Run migrations in offline mode, generating SQL scripts
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    This connects to the database and applies migration changes directly.
    It uses the application's database configuration to ensure consistency.
    
    Returns:
        None: No return value
    """
    # Get database URL from application settings
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = db_settings.SQLALCHEMY_DATABASE_URI
    
    # Create SQLAlchemy engine from configuration
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    # Create a database connection from the engine
    with connectable.connect() as connection:
        # Configure Alembic context with connection and target metadata
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Enable transaction per migration to ensure atomic changes
            transaction_per_migration=True,
            # Include object names in the autogenerate output
            include_object_names=True,
        )
        
        # Run migrations within a transaction
        with context.begin_transaction():
            context.run_migrations()


# Determine whether to run in online or offline mode based on context
if context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()