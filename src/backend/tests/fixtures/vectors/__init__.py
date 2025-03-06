#!/usr/bin/env python3
"""
Vector embedding test fixtures module.

This module provides access to sample vector embeddings used for testing 
the FAISS vector store and vector search functionality. It includes utility 
functions to load and manipulate test vector data in a consistent format 
across the test suite.
"""

import json
from pathlib import Path
from numpy import array  # numpy 1.24.0+

# Path to the sample embeddings JSON file
SAMPLE_EMBEDDINGS_PATH = Path(__file__).parent / 'sample_embeddings.json'

def load_sample_embeddings():
    """
    Loads sample vector embeddings from the JSON fixture file.
    
    Returns:
        dict: Dictionary containing sample embeddings and metadata
    """
    with open(SAMPLE_EMBEDDINGS_PATH, 'r') as f:
        return json.load(f)

def get_embedding_vectors():
    """
    Returns sample embedding vectors as numpy arrays.
    
    Returns:
        list: List of numpy arrays representing vector embeddings
    """
    data = load_sample_embeddings()
    embeddings = data['embeddings']
    return [array(embedding) for embedding in embeddings]

def get_embedding_ids():
    """
    Returns the IDs associated with sample embeddings.
    
    Returns:
        list: List of embedding IDs
    """
    data = load_sample_embeddings()
    return data['embedding_ids']

def get_embedding_texts():
    """
    Returns the document texts associated with sample embeddings.
    
    Returns:
        list: List of document texts
    """
    data = load_sample_embeddings()
    return data['document_contents']

def get_sample_vectors_with_ids():
    """
    Returns a tuple of vectors and their corresponding IDs.
    
    Returns:
        tuple: Tuple containing (vectors, ids)
    """
    vectors = get_embedding_vectors()
    ids = get_embedding_ids()
    return (vectors, ids)