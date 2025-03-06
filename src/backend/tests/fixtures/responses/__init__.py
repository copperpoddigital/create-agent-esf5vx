"""
Initialization module for LLM response test fixtures.

This module provides utility functions to load and access predefined LLM responses
for testing the AI response generation functionality. It enables consistent and
deterministic testing of the LLM service by providing standardized mock responses
for different query scenarios.
"""

import json
from pathlib import Path

# Path to the JSON file containing sample LLM responses
RESPONSES_FILE_PATH = Path(__file__).parent / 'llm_responses.json'

# Default response when no specific response is found
DEFAULT_RESPONSE = "I don't have enough information to answer this question based on the provided documents."

def load_responses():
    """
    Loads sample LLM responses from the JSON fixture file.
    
    Returns:
        dict: Dictionary containing sample LLM responses
    """
    with open(RESPONSES_FILE_PATH, 'r') as file:
        return json.load(file)

def get_response_for_query(query_type: str) -> str:
    """
    Returns a predefined response for a specific query type.
    
    Args:
        query_type (str): The type of query to get a response for
    
    Returns:
        str: Predefined response text for the query type
    """
    responses = load_responses()
    query_responses = responses.get('query_responses', {})
    return query_responses.get(query_type, DEFAULT_RESPONSE)

def get_standard_response() -> str:
    """
    Returns the standard AI response for testing.
    
    Returns:
        str: Standard response text
    """
    responses = load_responses()
    return responses.get('standard_response', DEFAULT_RESPONSE)

def get_no_context_response() -> str:
    """
    Returns the response for queries with no relevant context.
    
    Returns:
        str: No context response text
    """
    responses = load_responses()
    return responses.get('no_context_response', DEFAULT_RESPONSE)

def get_error_fallback_response() -> str:
    """
    Returns the fallback response for when LLM service encounters an error.
    
    Returns:
        str: Error fallback response text
    """
    responses = load_responses()
    return responses.get('error_fallback_response', DEFAULT_RESPONSE)

def get_responses_dict() -> dict:
    """
    Returns the complete dictionary of query responses.
    
    Returns:
        dict: Dictionary mapping query types to response texts
    """
    responses = load_responses()
    return responses.get('query_responses', {})