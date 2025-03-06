"""
Integration testing package initialization for the Document Management and AI Chatbot System.

This module marks the integration tests directory as a Python package and provides
common utilities, constants, and configuration specific to integration testing.
It builds upon the base test configuration defined in the parent tests package
to support integration tests across API endpoints and service components.
"""

import os
import pytest
from .. import TEST_ROOT_DIR, get_test_root_dir

# Define the integration tests directory path
INTEGRATION_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_integration_tests_dir() -> str:
    """
    Returns the absolute path to the integration tests directory.
    
    Returns:
        str: Path to the integration tests directory
    """
    return INTEGRATION_TESTS_DIR