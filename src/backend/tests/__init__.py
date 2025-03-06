"""
Test package initialization module for the Document Management and AI Chatbot System.

This module serves as the central configuration point for the test suite, providing
common utilities, constants, and path configurations used across all test modules.
It establishes a foundation for the comprehensive testing approach including unit,
integration, and specialized testing as defined in the testing strategy.
"""

import os
import pathlib
import sys

# Define important directory paths
TEST_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT_DIR = os.path.dirname(TEST_ROOT_DIR)
SRC_ROOT_DIR = os.path.dirname(BACKEND_ROOT_DIR)


def get_test_root_dir() -> str:
    """
    Returns the absolute path to the tests directory.
    
    Returns:
        str: Path to the tests directory
    """
    return TEST_ROOT_DIR


def get_backend_root_dir() -> str:
    """
    Returns the absolute path to the backend directory.
    
    Returns:
        str: Path to the backend directory
    """
    return BACKEND_ROOT_DIR


def add_src_to_path() -> None:
    """
    Adds the src directory to the Python path if not already present.
    This ensures proper imports from the src directory in test modules.
    
    Returns:
        None: No return value
    """
    if SRC_ROOT_DIR not in sys.path:
        sys.path.append(SRC_ROOT_DIR)


# Add src to Python path for proper imports
add_src_to_path()