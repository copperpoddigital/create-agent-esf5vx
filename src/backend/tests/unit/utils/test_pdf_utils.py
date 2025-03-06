import os
import tempfile
import pytest
from unittest.mock import patch
from fastapi import HTTPException

from app.utils.pdf_utils import (
    extract_text_from_pdf,
    extract_text_from_pdf_bytes,
    clean_text,
    chunk_text,
    extract_pdf_metadata,
    count_tokens,
    process_pdf_document
)
from tests.fixtures.documents import SAMPLE_PDF_PATH, get_sample_pdf_bytes


def test_extract_text_from_pdf_valid_file():
    """Tests that text can be successfully extracted from a valid PDF file"""
    # Use the SAMPLE_PDF_PATH fixture to get a valid PDF file path
    text = extract_text_from_pdf(str(SAMPLE_PDF_PATH))
    
    # Assert that the returned text is not empty
    assert text
    
    # Assert that the returned text is a string
    assert isinstance(text, str)
    
    # Assert that the returned text contains expected content from the sample PDF
    assert len(text) > 0


def test_extract_text_from_pdf_file_not_found():
    """Tests that appropriate exception is raised when PDF file is not found"""
    # Create a non-existent file path
    non_existent_path = "non_existent_file.pdf"
    
    # Use pytest.raises to assert that HTTPException is raised when calling extract_text_from_pdf
    with pytest.raises(HTTPException) as exc_info:
        extract_text_from_pdf(non_existent_path)
    
    # Verify that the exception status code is 404
    assert exc_info.value.status_code == 404


def test_extract_text_from_pdf_invalid_file():
    """Tests that appropriate exception is raised when file is not a valid PDF"""
    # Create a temporary text file that is not a PDF
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(b"This is not a PDF file")
        tmp_path = tmp_file.name
    
    try:
        # Use pytest.raises to assert that HTTPException is raised when calling extract_text_from_pdf
        with pytest.raises(HTTPException) as exc_info:
            extract_text_from_pdf(tmp_path)
        
        # Verify that the exception status code is 400
        assert exc_info.value.status_code == 400
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_extract_text_from_pdf_bytes_valid():
    """Tests that text can be successfully extracted from valid PDF bytes"""
    # Use get_sample_pdf_bytes to get sample PDF content as bytes
    pdf_bytes = get_sample_pdf_bytes()
    
    # Call extract_text_from_pdf_bytes with the sample PDF bytes
    text = extract_text_from_pdf_bytes(pdf_bytes)
    
    # Assert that the returned text is not empty
    assert text
    
    # Assert that the returned text is a string
    assert isinstance(text, str)
    
    # Assert that the returned text contains expected content from the sample PDF
    assert len(text) > 0


def test_extract_text_from_pdf_bytes_invalid():
    """Tests that appropriate exception is raised when bytes are not a valid PDF"""
    # Create invalid PDF bytes (e.g., text string encoded as bytes)
    invalid_bytes = b"This is not a PDF file"
    
    # Use pytest.raises to assert that HTTPException is raised when calling extract_text_from_pdf_bytes
    with pytest.raises(HTTPException) as exc_info:
        extract_text_from_pdf_bytes(invalid_bytes)
    
    # Verify that the exception status code is 400
    assert exc_info.value.status_code == 400


def test_clean_text():
    """Tests that text cleaning properly normalizes whitespace and formatting"""
    # Create a sample text with excessive whitespace, multiple newlines, etc.
    sample_text = "   This    text   has  excessive    whitespace.  \n\n\nAnd   multiple\nnewlines.   "
    
    # Call clean_text with the sample text
    cleaned_text = clean_text(sample_text)
    
    # Assert that the returned text has normalized whitespace
    assert "  " not in cleaned_text
    
    # Assert that multiple newlines are reduced to single newlines
    assert "\n\n" not in cleaned_text
    
    # Assert that leading and trailing whitespace is removed
    assert not cleaned_text.startswith(" ")
    assert not cleaned_text.endswith(" ")
    
    # Assert the cleaned text contains the expected content
    assert "This text has excessive whitespace." in cleaned_text


def test_chunk_text_default_settings():
    """Tests that text is correctly chunked using default settings"""
    # Create a sample text longer than the default chunk size
    # We'll need to make this much longer than the default chunk size from settings
    # Based on the settings, default CHUNK_SIZE is 1000
    sample_text = "A" * 2500
    
    # Call chunk_text with the sample text and default settings
    chunks = chunk_text(sample_text)
    
    # Assert that multiple chunks are returned
    assert len(chunks) > 1
    
    # Assert that each chunk is no longer than the default chunk size
    for chunk in chunks:
        assert len(chunk) <= 1000  # Assuming default chunk size is 1000
    
    # Assert that the chunks have appropriate overlap
    if len(chunks) > 1:
        # Calculate step size based on first two chunks
        step_size = len(sample_text) // len(chunks)
        
        # Check for some overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            overlap_found = False
            for j in range(1, len(chunks[i])):
                if chunks[i][-j:] == chunks[i+1][:j]:
                    overlap_found = True
                    break
            assert overlap_found, f"No overlap found between chunks {i} and {i+1}"


def test_chunk_text_custom_settings():
    """Tests that text is correctly chunked using custom chunk size and overlap"""
    # Create a sample text longer than the custom chunk size
    sample_text = "B" * 500
    
    # Define custom chunk settings
    chunk_size = 200
    chunk_overlap = 50
    
    # Call chunk_text with the sample text and custom chunk size and overlap
    chunks = chunk_text(sample_text, chunk_size, chunk_overlap)
    
    # Assert that multiple chunks are returned
    assert len(chunks) > 1
    
    # Assert that each chunk is no longer than the custom chunk size
    for chunk in chunks:
        assert len(chunk) <= chunk_size
    
    # Assert that the chunks have the specified overlap
    if len(chunks) > 1:
        # For a homogeneous text of all "B"s, if the chunks are of the maximum size,
        # the second chunk should start (chunk_size - chunk_overlap) characters into the text
        expected_step_size = chunk_size - chunk_overlap
        
        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            if len(chunks[i]) == chunk_size:
                assert chunks[i][-chunk_overlap:] == chunks[i+1][:chunk_overlap]


def test_chunk_text_empty():
    """Tests that chunking empty text returns an empty list"""
    # Call chunk_text with an empty string
    chunks = chunk_text("")
    
    # Assert that an empty list is returned
    assert chunks == []


def test_chunk_text_invalid_params():
    """Tests that appropriate exception is raised when chunk_size <= chunk_overlap"""
    # Create a sample text
    sample_text = "Sample text for testing invalid chunking parameters."
    
    # Use pytest.raises to assert that ValueError is raised when chunk_size <= chunk_overlap
    with pytest.raises(ValueError) as exc_info:
        chunk_text(sample_text, chunk_size=100, chunk_overlap=100)
    
    # Verify the exception message mentions the invalid parameters
    assert "Chunk size must be greater than chunk overlap" in str(exc_info.value)


def test_extract_pdf_metadata_valid_file():
    """Tests that metadata can be successfully extracted from a valid PDF file"""
    # Use the SAMPLE_PDF_PATH fixture to get a valid PDF file path
    metadata = extract_pdf_metadata(str(SAMPLE_PDF_PATH))
    
    # Assert that the returned metadata is a dictionary
    assert isinstance(metadata, dict)
    
    # Assert that the metadata contains expected keys (e.g., 'title', 'author', 'page_count')
    expected_keys = ['title', 'author', 'page_count', 'file_size']
    for key in expected_keys:
        assert key in metadata
    
    # Assert that the page_count matches the expected number of pages in the sample PDF
    # Note: We assume the sample PDF has at least 1 page
    assert metadata['page_count'] >= 1


def test_extract_pdf_metadata_file_not_found():
    """Tests that appropriate exception is raised when PDF file is not found"""
    # Create a non-existent file path
    non_existent_path = "non_existent_file.pdf"
    
    # Use pytest.raises to assert that HTTPException is raised when calling extract_pdf_metadata
    with pytest.raises(HTTPException) as exc_info:
        extract_pdf_metadata(non_existent_path)
    
    # Verify that the exception status code is 404
    assert exc_info.value.status_code == 404


def test_count_tokens():
    """Tests that token counting correctly counts tokens in text"""
    # Create sample texts of varying complexity
    short_text = "This is a short text."
    medium_text = "This is a medium length text with some additional words to increase its length."
    long_text = "This is a longer text that contains multiple sentences. It has punctuation, and various words of different lengths. The purpose is to test the token counting functionality with more complex text."
    
    # Call count_tokens for each sample text
    short_count = count_tokens(short_text)
    medium_count = count_tokens(medium_text)
    long_count = count_tokens(long_text)
    
    # Assert that the token counts are reasonable for the given texts
    assert short_count > 0
    assert medium_count > short_count
    assert long_count > medium_count
    
    # Assert that longer, more complex texts have more tokens than shorter, simpler texts
    assert long_count > medium_count > short_count


def test_count_tokens_empty():
    """Tests that token counting returns 0 for empty text"""
    # Call count_tokens with an empty string
    token_count = count_tokens("")
    
    # Assert that the token count is 0
    assert token_count == 0


def test_process_pdf_document():
    """Tests the complete PDF document processing workflow"""
    # Use the SAMPLE_PDF_PATH fixture to get a valid PDF file path
    result = process_pdf_document(str(SAMPLE_PDF_PATH))
    
    # Assert that the returned result is a dictionary
    assert isinstance(result, dict)
    
    # Assert that the result contains expected keys ('text', 'chunks', 'metadata', 'token_counts')
    expected_keys = ['text', 'chunks', 'metadata', 'token_counts', 'total_chunks', 'total_tokens']
    for key in expected_keys:
        assert key in result
    
    # Assert that the text is not empty
    assert result['text']
    
    # Assert that chunks is a list of strings
    assert isinstance(result['chunks'], list)
    assert all(isinstance(chunk, str) for chunk in result['chunks'])
    
    # Assert that metadata is a dictionary with expected keys
    assert isinstance(result['metadata'], dict)
    assert 'title' in result['metadata']
    assert 'page_count' in result['metadata']
    
    # Assert that token_counts is a dictionary of integers with the same length as chunks
    assert isinstance(result['token_counts'], dict)
    assert len(result['token_counts']) == len(result['chunks'])


def test_process_pdf_document_custom_chunk_settings():
    """Tests PDF document processing with custom chunk settings"""
    # Use the SAMPLE_PDF_PATH fixture to get a valid PDF file path
    # Define custom chunk settings
    chunk_size = 200
    chunk_overlap = 50
    
    # Call process_pdf_document with the sample PDF path and custom chunk size and overlap
    result = process_pdf_document(str(SAMPLE_PDF_PATH), chunk_size, chunk_overlap)
    
    # Assert that the returned result is a dictionary with expected keys
    assert isinstance(result, dict)
    expected_keys = ['text', 'chunks', 'metadata', 'token_counts', 'total_chunks', 'total_tokens']
    for key in expected_keys:
        assert key in result
    
    # Assert that the chunks conform to the custom chunk size and overlap
    if result['text'] and len(result['text']) > chunk_size:
        # If the document is long enough to require chunking
        for chunk in result['chunks']:
            assert len(chunk) <= chunk_size


def test_process_pdf_document_file_not_found():
    """Tests that appropriate exception is raised when PDF file is not found"""
    # Create a non-existent file path
    non_existent_path = "non_existent_file.pdf"
    
    # Use pytest.raises to assert that HTTPException is raised when calling process_pdf_document
    with pytest.raises(HTTPException) as exc_info:
        process_pdf_document(non_existent_path)
    
    # Verify that the exception status code is 404
    assert exc_info.value.status_code == 404