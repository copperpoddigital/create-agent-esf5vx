"""
Unit tests for the vector search service in the Document Management and AI Chatbot System.

This file contains tests to verify the functionality of vector similarity search, including
searching by text and vector embeddings, result formatting, and both synchronous and 
asynchronous search operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np  # version 1.24.0+
import pytest_asyncio  # version 0.21.0+
import uuid

from src.backend.app.services.vector_search import (
    VectorSearchService,
    search_by_text,
    search_by_vector,
    async_search_by_text,
    async_search_by_vector,
    format_search_results,
    get_vector_store
)
from src.backend.app.vector_store.faiss_store import FAISSStore
from src.backend.app.services.embedding_service import generate_embedding, async_generate_embedding
from src.backend.app.models.document_chunk import DocumentChunk


def test_get_vector_store(mocker):
    """Tests that get_vector_store initializes and returns a FAISS vector store"""
    # Mock FAISSStore to avoid actual initialization
    mock_faiss_store = mocker.patch("src.backend.app.services.vector_search.FAISSStore", autospec=True)
    mock_faiss_store.return_value.load.return_value = None
    mock_faiss_store.return_value.count.return_value = 0
    
    # Clear any existing singleton instance
    mocker.patch("src.backend.app.services.vector_search._vector_store", None)
    
    # Call the function
    vector_store = get_vector_store()
    
    # Assert that FAISSStore was constructed correctly
    mock_faiss_store.assert_called_once()
    
    # Call again and verify singleton pattern
    vector_store2 = get_vector_store()
    assert mock_faiss_store.call_count == 1  # Should not create a new instance
    assert vector_store == vector_store2  # Should return the same instance


def test_search_by_vector(mocker):
    """Tests the search_by_vector function with a mock vector store"""
    # Create a mock FAISS store
    mock_faiss_store = Mock(spec=FAISSStore)
    
    # Configure the mock to return predefined search results
    mock_search_results = [
        {"id": "embedding1", "score": 0.95, "vector": [0.1, 0.2, 0.3], "index": 0},
        {"id": "embedding2", "score": 0.85, "vector": [0.4, 0.5, 0.6], "index": 1}
    ]
    mock_faiss_store.search.return_value = mock_search_results
    
    # Mock document chunk retrieval
    mock_db = Mock()
    mock_get_by_embedding_id = mocker.patch(
        "src.backend.app.crud.crud_document_chunk.document_chunk.get_by_embedding_id"
    )
    
    # Create test document chunks
    chunk1 = Mock(spec=DocumentChunk)
    chunk1.id = uuid.uuid4()
    chunk1.document_id = uuid.uuid4()
    chunk1.content = "This is test content 1"
    chunk1.embedding_id = "embedding1"
    chunk1.chunk_index = 0
    
    chunk2 = Mock(spec=DocumentChunk)
    chunk2.id = uuid.uuid4()
    chunk2.document_id = uuid.uuid4()
    chunk2.content = "This is test content 2"
    chunk2.embedding_id = "embedding2"
    chunk2.chunk_index = 1
    
    # Mock get_by_embedding_id to return the corresponding chunks
    mock_get_by_embedding_id.side_effect = lambda db, embedding_id: {
        "embedding1": chunk1,
        "embedding2": chunk2
    }.get(embedding_id)
    
    # Patch get_vector_store to return our mock
    with patch("src.backend.app.services.vector_search.get_vector_store", return_value=mock_faiss_store):
        # Create a test query vector
        query_vector = np.array([0.1, 0.2, 0.3])
        
        # Call the function
        results = search_by_vector(query_vector, mock_db, top_k=2, threshold=0.8)
        
        # Assertions
        mock_faiss_store.search.assert_called_once()
        assert len(results) == 2
        
        # Check that document chunks were retrieved for each result
        assert mock_get_by_embedding_id.call_count == 2
        
        # Verify result format and content
        assert results[0]["chunk_id"] == str(chunk1.id)
        assert results[0]["document_id"] == str(chunk1.document_id)
        assert results[0]["content"] == chunk1.content
        assert results[0]["similarity_score"] == 0.95
        
        assert results[1]["chunk_id"] == str(chunk2.id)
        assert results[1]["document_id"] == str(chunk2.document_id)
        assert results[1]["content"] == chunk2.content
        assert results[1]["similarity_score"] == 0.85


def test_search_by_text(mocker):
    """Tests the search_by_text function with mocked dependencies"""
    # Mock generate_embedding to return a test vector
    test_vector = np.array([0.1, 0.2, 0.3])
    mock_generate_embedding = mocker.patch(
        "src.backend.app.services.vector_search.generate_embedding",
        return_value=test_vector
    )
    
    # Mock search_by_vector to return predefined results
    test_results = [
        {"chunk_id": "id1", "document_id": "doc1", "content": "content1", "similarity_score": 0.95},
        {"chunk_id": "id2", "document_id": "doc2", "content": "content2", "similarity_score": 0.85}
    ]
    mock_search_by_vector = mocker.patch(
        "src.backend.app.services.vector_search.search_by_vector",
        return_value=test_results
    )
    
    # Create a mock database session
    mock_db = Mock()
    
    # Call the function
    query_text = "test query"
    results = search_by_text(query_text, mock_db, top_k=2, threshold=0.8)
    
    # Assertions
    mock_generate_embedding.assert_called_once_with(query_text)
    mock_search_by_vector.assert_called_once_with(test_vector, mock_db, 2, 0.8)
    assert results == test_results


@pytest.mark.asyncio
async def test_async_search_by_vector(mocker):
    """Tests the async_search_by_vector function with a mock vector store"""
    # Create a mock FAISS store
    mock_faiss_store = Mock(spec=FAISSStore)
    
    # Configure the mock to return predefined search results
    mock_search_results = [
        {"id": "embedding1", "score": 0.95, "vector": [0.1, 0.2, 0.3], "index": 0},
        {"id": "embedding2", "score": 0.85, "vector": [0.4, 0.5, 0.6], "index": 1}
    ]
    mock_faiss_store.search.return_value = mock_search_results
    
    # Mock document chunk retrieval
    mock_db = Mock()
    mock_get_by_embedding_id_async = mocker.patch(
        "src.backend.app.crud.crud_document_chunk.document_chunk.get_by_embedding_id_async"
    )
    
    # Create test document chunks
    chunk1 = Mock(spec=DocumentChunk)
    chunk1.id = uuid.uuid4()
    chunk1.document_id = uuid.uuid4()
    chunk1.content = "This is test content 1"
    chunk1.embedding_id = "embedding1"
    chunk1.chunk_index = 0
    
    chunk2 = Mock(spec=DocumentChunk)
    chunk2.id = uuid.uuid4()
    chunk2.document_id = uuid.uuid4()
    chunk2.content = "This is test content 2"
    chunk2.embedding_id = "embedding2"
    chunk2.chunk_index = 1
    
    # Mock asyncio.to_thread to execute synchronously in tests
    async def mock_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)
    
    mocker.patch("asyncio.to_thread", side_effect=mock_to_thread)
    
    # Mock get_by_embedding_id_async to return the corresponding chunks
    async def get_chunk(db, embedding_id):
        return {
            "embedding1": chunk1,
            "embedding2": chunk2
        }.get(embedding_id)
    
    mock_get_by_embedding_id_async.side_effect = get_chunk
    
    # Patch get_vector_store to return our mock
    with patch("src.backend.app.services.vector_search.get_vector_store", return_value=mock_faiss_store):
        # Create a test query vector
        query_vector = np.array([0.1, 0.2, 0.3])
        
        # Call the function
        results = await async_search_by_vector(query_vector, mock_db, top_k=2, threshold=0.8)
        
        # Assertions
        mock_faiss_store.search.assert_called_once()
        assert mock_get_by_embedding_id_async.call_count == 2
        assert len(results) == 2
        
        # Verify result format and content
        assert results[0]["chunk_id"] == str(chunk1.id)
        assert results[0]["document_id"] == str(chunk1.document_id)
        assert results[0]["content"] == chunk1.content
        assert results[0]["similarity_score"] == 0.95
        
        assert results[1]["chunk_id"] == str(chunk2.id)
        assert results[1]["document_id"] == str(chunk2.document_id)
        assert results[1]["content"] == chunk2.content
        assert results[1]["similarity_score"] == 0.85


@pytest.mark.asyncio
async def test_async_search_by_text(mocker):
    """Tests the async_search_by_text function with mocked dependencies"""
    # Mock async_generate_embedding to return a test vector
    test_vector = np.array([0.1, 0.2, 0.3])
    
    async def mock_async_generate_embedding(text):
        return test_vector
    
    mocker.patch(
        "src.backend.app.services.vector_search.async_generate_embedding",
        side_effect=mock_async_generate_embedding
    )
    
    # Mock async_search_by_vector to return predefined results
    test_results = [
        {"chunk_id": "id1", "document_id": "doc1", "content": "content1", "similarity_score": 0.95},
        {"chunk_id": "id2", "document_id": "doc2", "content": "content2", "similarity_score": 0.85}
    ]
    
    async def mock_async_search_by_vector(vector, db, top_k, threshold):
        return test_results
    
    mocker.patch(
        "src.backend.app.services.vector_search.async_search_by_vector",
        side_effect=mock_async_search_by_vector
    )
    
    # Create a mock database session
    mock_db = Mock()
    
    # Call the function
    query_text = "test query"
    results = await async_search_by_text(query_text, mock_db, top_k=2, threshold=0.8)
    
    # Assertions
    assert results == test_results


def test_format_search_results():
    """Tests the format_search_results function with test data"""
    # Create test vector search results
    vector_results = [
        {"id": "embedding1", "score": 0.95, "vector": [0.1, 0.2, 0.3], "index": 0},
        {"id": "embedding2", "score": 0.85, "vector": [0.4, 0.5, 0.6], "index": 1},
        {"id": "embedding3", "score": 0.75, "vector": [0.7, 0.8, 0.9], "index": 2},
    ]
    
    # Create test document chunks
    chunk1 = Mock(spec=DocumentChunk)
    chunk1.id = uuid.uuid4()
    chunk1.document_id = uuid.uuid4()
    chunk1.content = "This is test content 1"
    chunk1.embedding_id = "embedding1"
    chunk1.chunk_index = 0
    
    chunk2 = Mock(spec=DocumentChunk)
    chunk2.id = uuid.uuid4()
    chunk2.document_id = uuid.uuid4()
    chunk2.content = "This is test content 2"
    chunk2.embedding_id = "embedding2"
    chunk2.chunk_index = 1
    
    # Only include two chunks to test handling of missing chunks
    document_chunks = [chunk1, chunk2]
    
    # Call the function
    results = format_search_results(vector_results, document_chunks)
    
    # Assertions
    assert len(results) == 2  # Should only have results for the chunks that were found
    
    # Check first result
    assert results[0]["chunk_id"] == str(chunk1.id)
    assert results[0]["document_id"] == str(chunk1.document_id)
    assert results[0]["content"] == chunk1.content
    assert results[0]["similarity_score"] == 0.95
    assert results[0]["chunk_index"] == 0
    
    # Check second result
    assert results[1]["chunk_id"] == str(chunk2.id)
    assert results[1]["document_id"] == str(chunk2.document_id)
    assert results[1]["content"] == chunk2.content
    assert results[1]["similarity_score"] == 0.85
    assert results[1]["chunk_index"] == 1


def test_vector_search_service_init(mocker):
    """Tests the initialization of the VectorSearchService class"""
    # Create a mock FAISS store
    mock_faiss_store = Mock(spec=FAISSStore)
    
    # Patch get_vector_store to return our mock
    mock_get_vector_store = mocker.patch(
        "src.backend.app.services.vector_search.get_vector_store",
        return_value=mock_faiss_store
    )
    
    # Create a VectorSearchService with default vector store
    service = VectorSearchService()
    
    # Assertions
    mock_get_vector_store.assert_called_once()
    assert service._vector_store == mock_faiss_store
    
    # Create a VectorSearchService with custom vector store
    custom_store = Mock(spec=FAISSStore)
    service2 = VectorSearchService(vector_store=custom_store)
    
    # Assertions
    assert mock_get_vector_store.call_count == 1  # Should not call again
    assert service2._vector_store == custom_store


def test_vector_search_service_search(mocker):
    """Tests the search method of the VectorSearchService class"""
    # Create a mock FAISS store
    mock_faiss_store = Mock(spec=FAISSStore)
    
    # Create a VectorSearchService with our mock store
    service = VectorSearchService(vector_store=mock_faiss_store)
    
    # Mock generate_embedding to return a test vector
    test_vector = np.array([0.1, 0.2, 0.3])
    mock_generate_embedding = mocker.patch(
        "src.backend.app.services.vector_search.generate_embedding",
        return_value=test_vector
    )
    
    # Mock search_by_vector to return predefined results
    test_results = [
        {"chunk_id": "id1", "document_id": "doc1", "content": "content1", "similarity_score": 0.95},
        {"chunk_id": "id2", "document_id": "doc2", "content": "content2", "similarity_score": 0.85}
    ]
    mock_search_by_vector = mocker.patch(
        "src.backend.app.services.vector_search.search_by_vector",
        return_value=test_results
    )
    
    # Create a mock database session
    mock_db = Mock()
    
    # Call the function
    query_text = "test query"
    results = service.search(query_text, mock_db, top_k=2, threshold=0.8)
    
    # Assertions
    mock_generate_embedding.assert_called_once_with(query_text)
    mock_search_by_vector.assert_called_once_with(test_vector, mock_db, 2, 0.8)
    assert results == test_results


@pytest.mark.asyncio
async def test_vector_search_service_async_search(mocker):
    """Tests the async_search method of the VectorSearchService class"""
    # Create a mock FAISS store
    mock_faiss_store = Mock(spec=FAISSStore)
    
    # Create a VectorSearchService with our mock store
    service = VectorSearchService(vector_store=mock_faiss_store)
    
    # Mock async_generate_embedding to return a test vector
    test_vector = np.array([0.1, 0.2, 0.3])
    
    async def mock_async_generate_embedding(text):
        return test_vector
    
    mocker.patch(
        "src.backend.app.services.vector_search.async_generate_embedding",
        side_effect=mock_async_generate_embedding
    )
    
    # Mock async_search_by_vector to return predefined results
    test_results = [
        {"chunk_id": "id1", "document_id": "doc1", "content": "content1", "similarity_score": 0.95},
        {"chunk_id": "id2", "document_id": "doc2", "content": "content2", "similarity_score": 0.85}
    ]
    
    async def mock_async_search_by_vector(vector, db, top_k, threshold):
        return test_results
    
    mocker.patch(
        "src.backend.app.services.vector_search.async_search_by_vector",
        side_effect=mock_async_search_by_vector
    )
    
    # Create a mock database session
    mock_db = Mock()
    
    # Call the function
    query_text = "test query"
    results = await service.async_search(query_text, mock_db, top_k=2, threshold=0.8)
    
    # Assertions
    assert results == test_results


def test_vector_search_service_rerank_results():
    """Tests the rerank_results method of the VectorSearchService class"""
    # Create a VectorSearchService instance
    service = VectorSearchService(vector_store=Mock(spec=FAISSStore))
    
    # Create test search results
    test_results = [
        {"chunk_id": "id1", "document_id": "doc1", "content": "This is a test query", "similarity_score": 0.85},
        {"chunk_id": "id2", "document_id": "doc2", "content": "This is something else", "similarity_score": 0.95},
        {"chunk_id": "id3", "document_id": "doc3", "content": "Completely different content", "similarity_score": 0.75}
    ]
    
    # Call the function with query text that matches the first result
    query_text = "test query"
    reranked_results = service.rerank_results(test_results, query_text)
    
    # Assertions
    assert len(reranked_results) == 3
    
    # The first result should now be the one with exact match, even though it had lower score
    assert reranked_results[0]["chunk_id"] == "id1"
    
    # Original similarity scores should be preserved
    assert reranked_results[0]["similarity_score"] == 0.85
    assert reranked_results[1]["similarity_score"] == 0.95
    assert reranked_results[2]["similarity_score"] == 0.75


def test_vector_search_service_filter_results():
    """Tests the filter_results method of the VectorSearchService class"""
    # Create a VectorSearchService instance
    service = VectorSearchService(vector_store=Mock(spec=FAISSStore))
    
    # Create test search results
    test_results = [
        {"chunk_id": "id1", "document_id": "doc1", "content": "This is content with keyword", "similarity_score": 0.85},
        {"chunk_id": "id2", "document_id": "doc2", "content": "This is something else", "similarity_score": 0.95},
        {"chunk_id": "id3", "document_id": "doc1", "content": "Another chunk from same document", "similarity_score": 0.75}
    ]
    
    # Test filtering by document ID
    filters = {"document_id": "doc1"}
    filtered_results = service.filter_results(test_results, filters)
    
    # Assertions
    assert len(filtered_results) == 2
    assert filtered_results[0]["document_id"] == "doc1"
    assert filtered_results[1]["document_id"] == "doc1"
    
    # Test filtering by content
    filters = {"content_contains": "keyword"}
    filtered_results = service.filter_results(test_results, filters)
    
    # Assertions
    assert len(filtered_results) == 1
    assert filtered_results[0]["chunk_id"] == "id1"
    
    # Test filtering by minimum score
    filters = {"min_score": 0.80}
    filtered_results = service.filter_results(test_results, filters)
    
    # Assertions
    assert len(filtered_results) == 2
    assert filtered_results[0]["similarity_score"] >= 0.80
    assert filtered_results[1]["similarity_score"] >= 0.80


def test_search_with_empty_query(mocker):
    """Tests that search functions handle empty queries appropriately"""
    # Create a VectorSearchService instance
    service = VectorSearchService(vector_store=Mock(spec=FAISSStore))
    
    # Create a mock database session
    mock_db = Mock()
    
    # Call the search method with an empty query
    results = service.search("", mock_db)
    
    # An empty query should return an empty result set, not an error
    assert results == []
    
    # Test with only whitespace
    results = service.search("   ", mock_db)
    assert results == []


def test_search_with_no_results(mocker):
    """Tests that search functions handle queries with no matching results"""
    # Create a mock FAISS store that returns empty results
    mock_faiss_store = Mock(spec=FAISSStore)
    mock_faiss_store.search.return_value = []
    
    # Create a VectorSearchService with our mock store
    service = VectorSearchService(vector_store=mock_faiss_store)
    
    # Mock generate_embedding to return a test vector
    test_vector = np.array([0.1, 0.2, 0.3])
    mocker.patch(
        "src.backend.app.services.vector_search.generate_embedding",
        return_value=test_vector
    )
    
    # Create a mock database session
    mock_db = Mock()
    
    # Call the function
    query_text = "test query with no matches"
    results = service.search(query_text, mock_db)
    
    # Assertions
    assert isinstance(results, list)
    assert len(results) == 0


def test_search_with_threshold_filtering(mocker):
    """Tests that search functions correctly apply similarity threshold filtering"""
    # Create a mock FAISS store
    mock_faiss_store = Mock(spec=FAISSStore)
    
    # Configure the mock to return results with different similarity scores
    mock_search_results = [
        {"id": "embedding1", "score": 0.95, "vector": [0.1, 0.2, 0.3], "index": 0},
        {"id": "embedding2", "score": 0.85, "vector": [0.4, 0.5, 0.6], "index": 1},
        {"id": "embedding3", "score": 0.75, "vector": [0.7, 0.8, 0.9], "index": 2},
        {"id": "embedding4", "score": 0.65, "vector": [0.2, 0.3, 0.4], "index": 3}
    ]
    mock_faiss_store.search.return_value = mock_search_results
    
    # Create a VectorSearchService with our mock store
    service = VectorSearchService(vector_store=mock_faiss_store)
    
    # Mock generate_embedding to return a test vector
    test_vector = np.array([0.1, 0.2, 0.3])
    mocker.patch(
        "src.backend.app.services.vector_search.generate_embedding",
        return_value=test_vector
    )
    
    # Mock document_chunk.get_by_embedding_id to return test document chunks
    mock_get_by_embedding_id = mocker.patch(
        "src.backend.app.crud.crud_document_chunk.document_chunk.get_by_embedding_id"
    )
    
    # Create test document chunks for each embedding ID
    chunks = {}
    for i, embedding_id in enumerate(["embedding1", "embedding2", "embedding3", "embedding4"]):
        chunk = Mock(spec=DocumentChunk)
        chunk.id = uuid.uuid4()
        chunk.document_id = uuid.uuid4()
        chunk.content = f"Test content {i+1}"
        chunk.embedding_id = embedding_id
        chunk.chunk_index = i
        chunks[embedding_id] = chunk
    
    # Mock get_by_embedding_id to return the corresponding chunks
    mock_get_by_embedding_id.side_effect = lambda db, embedding_id: chunks.get(embedding_id)
    
    # Create a mock database session
    mock_db = Mock()
    
    # Test with a high threshold that should filter out lower-scoring results
    query_text = "test query"
    results = service.search(query_text, mock_db, threshold=0.80)
    
    # Assertions - only results with score >= 0.80 should be returned
    assert len(results) == 2
    assert all(result["similarity_score"] >= 0.80 for result in results)
    assert results[0]["content"] == "Test content 1"  # Score 0.95
    assert results[1]["content"] == "Test content 2"  # Score 0.85