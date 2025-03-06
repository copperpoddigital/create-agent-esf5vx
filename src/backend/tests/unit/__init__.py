"""
Unit test package initialization module for the Document Management and AI Chatbot System.

This module marks the unit tests directory as a Python package and provides common
utilities, constants, and path configurations specific to unit testing. It builds on
the foundation provided by the main test package initialization and facilitates the
organization of unit tests according to the defined testing strategy.
"""

import os
import pytest

from .. import TEST_ROOT_DIR, BACKEND_ROOT_DIR

# Define the absolute path to the unit tests directory
UNIT_TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def get_unit_test_dir() -> str:
    """
    Returns the absolute path to the unit tests directory.
    
    Returns:
        str: Path to the unit tests directory
    """
    return UNIT_TEST_DIR


# Define common test directories for fixtures and utilities
FIXTURES_DIR = os.path.join(UNIT_TEST_DIR, "fixtures")
MOCK_DATA_DIR = os.path.join(FIXTURES_DIR, "mock_data")


# Add pytest configuration or utility functions as needed
def pytest_configure(config):
    """
    Custom pytest configuration for unit tests.
    
    This function is automatically called by pytest during initialization.
    It can be used to set up test markers, configure plugins, or set pytest options.
    
    Args:
        config: The pytest config object
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", "document_processor: marks tests related to document processing"
    )
    config.addinivalue_line(
        "markers", "vector_search: marks tests related to vector search functionality"
    )
    config.addinivalue_line(
        "markers", "llm_integration: marks tests related to LLM integration"
    )
    config.addinivalue_line(
        "markers", "authentication: marks tests related to authentication and authorization"
    )