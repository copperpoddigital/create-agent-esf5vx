"""
Initialization file for the scripts package in the Document Management and AI Chatbot System.

This file makes key utility scripts and functions available for import from the scripts package,
facilitating administrative tasks, database migrations, vector index maintenance, and
performance benchmarking.
"""

# Import logging for configuration
import logging  # standard library version

# Import functions from internal modules
from .create_admin import create_admin_user
from .generate_migrations import generate_migration
from .rebuild_index import rebuild_index
from .benchmark_vector_search import run_comprehensive_benchmark, BenchmarkConfig

# Configure module-level logger
logger = logging.getLogger(__name__)

# Define package version
__version__ = "1.0.0"

# Export items for package-level access
__all__ = [
    "create_admin_user",
    "generate_migration",
    "rebuild_index",
    "run_comprehensive_benchmark",
    "BenchmarkConfig",
]