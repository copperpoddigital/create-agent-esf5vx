"""
Integration tests for service components of the Document Management and AI Chatbot System.

This package contains integration tests that verify the correct interaction between
service components and external dependencies such as databases, vector stores, and LLM services.
"""

import os
import pytest  # pytest version 7.0.0+

# Define the path to the service integration tests directory
SERVICE_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_service_tests_dir() -> str:
    """
    Returns the absolute path to the service integration tests directory.
    
    Returns:
        str: Path to the service integration tests directory
    """
    return SERVICE_TESTS_DIR