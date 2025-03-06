import os
import json
import uuid
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import openai  # version 1.0.0+

from src.backend.app.services.llm_service import LLMService
from src.backend.app.services.vector_search import VectorSearchService
from src.backend.app.vector_store.faiss_store import FAISSStore
from src.backend.app.schemas.document_chunk import DocumentChunkWithSimilarity
from src.backend.app.schemas.query import QueryResponse

# Define path to fixtures directory
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '../..', 'fixtures')
RESPONSES_FILE = os.path.join(FIXTURES_DIR, 'responses', 'llm_responses.json')

def load_response_fixtures():
    """Loads LLM response fixtures from JSON file"""
    try:
        with open(RESPONSES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return some default fixtures if file doesn't exist or is invalid
        return {
            "vector_db_response": "Vector databases are specialized databases designed to store and search high-dimensional vectors efficiently. They are essential for machine learning applications that use embeddings to represent complex data like text, images, or audio.",
            "no_info_response": "I don't have enough information to answer this question."
        }

def create_mock_document_chunks(count=3):
    """Creates mock document chunks with similarity scores for testing"""
    document_chunks = []
    for i in range(count):
        document_chunks.append({
            "document_id": str(uuid.uuid4()),
            "content": f"This is test document chunk {i+1} with relevant information.",
            "similarity_score": 0.9 - (i * 0.1),  # Decreasing similarity scores
            "chunk_index": i
        })
    return document_chunks

def create_mock_openai_response(content):
    """Creates a mock OpenAI API response object"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response

class TestLLMService:
    """Test class for LLM service integration tests"""

    def setup_method(self, method):
        """Set up test environment before each test"""
        self.response_fixtures = load_response_fixtures()
        self.document_chunks = create_mock_document_chunks(3)
        
        # Create mock vector search service
        self.mock_vector_search = MagicMock(spec=VectorSearchService)
        self.mock_vector_search.search.return_value = self.document_chunks
        
        # Initialize LLM service with mock dependencies
        self.llm_service = LLMService()
        
        # For tests that need to patch OpenAI calls
        self.openai_patcher = patch('src.backend.app.services.llm_service.get_openai_client')
        self.mock_openai_client = self.openai_patcher.start()
        
    def teardown_method(self, method):
        """Clean up after each test"""
        if hasattr(self, 'openai_patcher'):
            self.openai_patcher.stop()

    def test_format_prompt(self):
        """Test that prompts are correctly formatted with system instructions and context"""
        query = "What are the key benefits of vector databases?"
        messages = self.llm_service.format_prompt(query, self.document_chunks)
        
        # Verify that prompt is correctly structured
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "helpful assistant" in messages[0]["content"].lower()
        assert messages[1]["role"] == "user"
        assert "Context:" in messages[1]["content"]
        assert query in messages[1]["content"]
        
        # Verify that document content is included in context
        for chunk in self.document_chunks:
            assert chunk["content"] in messages[1]["content"]

    def test_prepare_context(self):
        """Test that context is correctly prepared from document chunks"""
        context = self.llm_service.prepare_context(self.document_chunks, 2000)
        
        # Verify document chunks are included in context
        for i, chunk in enumerate(self.document_chunks):
            assert f"Document {i+1}" in context
            assert chunk["content"] in context
            assert f"ID: {chunk['document_id']}" in context
            
        # Verify that documents with higher similarity scores appear first
        sorted_chunks = sorted(self.document_chunks, key=lambda x: x.get("similarity_score", 0), reverse=True)
        first_chunk_content = sorted_chunks[0]["content"]
        last_chunk_content = sorted_chunks[-1]["content"]
        
        first_pos = context.find(first_chunk_content)
        last_pos = context.find(last_chunk_content)
        
        assert first_pos < last_pos

    def test_generate_response(self):
        """Test that responses are correctly generated based on query and context"""
        query = "What are vector databases?"
        expected_response = self.response_fixtures["vector_db_response"]
        
        # Mock OpenAI client to return expected response
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = create_mock_openai_response(expected_response)
        self.mock_openai_client.return_value = mock_client
        
        # Generate response
        response = self.llm_service.generate_response(query, self.document_chunks)
        
        # Verify response matches expected output
        assert response == expected_response
        
        # Verify OpenAI client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert "messages" in call_args
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][1]["role"] == "user"
        assert query in call_args["messages"][1]["content"]

    def test_generate_response_with_empty_context(self):
        """Test response generation when no relevant documents are found"""
        query = "What are vector databases?"
        expected_response = self.response_fixtures["no_info_response"]
        
        # Mock OpenAI client to return expected response
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = create_mock_openai_response(expected_response)
        self.mock_openai_client.return_value = mock_client
        
        # Generate response with empty context
        response = self.llm_service.generate_response(query, [])
        
        # Verify response indicates no information available
        assert response == expected_response
        
        # Verify OpenAI client was called with correct parameters
        call_args = mock_client.chat.completions.create.call_args[1]
        assert "Context:\n\n" in call_args["messages"][1]["content"]  # Empty context

    def test_create_query_response(self):
        """Test creation of a complete query response object"""
        query_text = "What are vector databases?"
        expected_response = self.response_fixtures["vector_db_response"]
        
        # Mock generate_response to return expected output
        with patch.object(self.llm_service, 'generate_response', return_value=expected_response):
            response = self.llm_service.create_query_response(query_text, self.document_chunks)
        
        # Verify response object structure
        assert isinstance(response, QueryResponse)
        assert response.query_text == query_text
        assert response.response_text == expected_response
        assert len(response.relevant_documents) == len(self.document_chunks)

    def test_error_handling(self):
        """Test error handling when the LLM service encounters an error"""
        query = "What are vector databases?"
        
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        self.mock_openai_client.return_value = mock_client
        
        # Generate response (should handle the exception)
        response = self.llm_service.generate_response(query, self.document_chunks)
        
        # Verify error response
        assert "sorry" in response.lower()
        assert "error" in response.lower()

    @pytest.mark.asyncio
    async def test_async_generate_response(self):
        """Test asynchronous response generation"""
        query = "What are vector databases?"
        expected_response = self.response_fixtures["vector_db_response"]
        
        # Mock OpenAI client to return expected response
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = create_mock_openai_response(expected_response)
        self.mock_openai_client.return_value = mock_client
        
        # Generate response asynchronously
        response = await self.llm_service.async_generate_response(query, self.document_chunks)
        
        # Verify response matches expected output
        assert response == expected_response
        
        # Verify OpenAI client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_create_query_response(self):
        """Test asynchronous creation of a complete query response object"""
        query_text = "What are vector databases?"
        expected_response = self.response_fixtures["vector_db_response"]
        
        # Mock async_generate_response to return expected output
        with patch.object(self.llm_service, 'async_generate_response', return_value=expected_response):
            response = await self.llm_service.async_create_query_response(query_text, self.document_chunks)
        
        # Verify response object structure
        assert isinstance(response, QueryResponse)
        assert response.query_text == query_text
        assert response.response_text == expected_response
        assert len(response.relevant_documents) == len(self.document_chunks)

    def test_integration_with_vector_search(self):
        """Test integration between vector search and LLM response generation"""
        query = "What are vector databases?"
        expected_response = self.response_fixtures["vector_db_response"]
        
        # Set up a real VectorSearchService with mock FAISS store
        mock_faiss = MagicMock(spec=FAISSStore)
        vector_search = VectorSearchService(mock_faiss)
        
        # Configure mock to return test document chunks
        vector_search.search = MagicMock(return_value=self.document_chunks)
        
        # Mock OpenAI client to return expected response
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = create_mock_openai_response(expected_response)
        self.mock_openai_client.return_value = mock_client
        
        # Mock LLM service's generate_response to avoid actual API calls
        with patch.object(self.llm_service, 'generate_response', return_value=expected_response):
            # Generate response using the integrated services
            db_mock = MagicMock()  # Mock database session
            response = self.llm_service.create_query_response(query, vector_search.search(query, db_mock))
        
        # Verify response
        assert response.query_text == query
        assert response.response_text == expected_response
        assert len(response.relevant_documents) == len(self.document_chunks)

    def test_token_limit_handling(self):
        """Test handling of token limits for context window"""
        # Create document chunks with varying lengths
        long_chunks = create_mock_document_chunks(3)
        for i, chunk in enumerate(long_chunks):
            # Make each chunk progressively longer
            chunk["content"] = f"Document {i+1} content: " + "This is test content. " * (10 * (i+1))
        
        # Mock count_tokens to return predictable values based on text length
        def mock_count_tokens(text):
            return len(text) // 5  # Simple approximation
        
        # Apply the mocks
        with patch('src.backend.app.services.llm_service.count_tokens', side_effect=mock_count_tokens):
            # Test with a low token limit
            small_context = self.llm_service.prepare_context(long_chunks, 100)
            
            # Verify only part of the content fits within token limit
            assert len(small_context) <= 100 * 5  # Using our token approximation
            
            # Test truncation with very long content
            very_long_chunks = create_mock_document_chunks(1)
            very_long_chunks[0]["content"] = "X" * 5000
            
            # Mock truncate_context to simulate tokenizer behavior
            with patch('src.backend.app.services.llm_service.truncate_context') as mock_truncate:
                mock_truncate.return_value = "Truncated content...\n\n[Context truncated due to length limitations]"
                truncated_context = self.llm_service.prepare_context(very_long_chunks, 100)
                assert "[Context truncated" in truncated_context

    def test_caching_mechanism(self):
        """Test that responses are correctly cached and retrieved"""
        query = "What are vector databases?"
        expected_response = self.response_fixtures["vector_db_response"]
        cache_data = {}
        
        # Create mock functions for cache operations
        def mock_check_cache(query, context_documents):
            key = f"{query}:{','.join([d['document_id'] for d in context_documents])}"
            return cache_data.get(key)
        
        def mock_update_cache(query, context_documents, response):
            key = f"{query}:{','.join([d['document_id'] for d in context_documents])}"
            cache_data[key] = response
        
        # Apply the mock functions
        with patch('src.backend.app.services.llm_service.check_cache', side_effect=mock_check_cache), \
             patch('src.backend.app.services.llm_service.update_cache', side_effect=mock_update_cache), \
             patch('src.backend.app.services.llm_service.llm_settings.USE_CACHE', True):
             
            # Mock OpenAI client to return expected response
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = create_mock_openai_response(expected_response)
            self.mock_openai_client.return_value = mock_client
            
            # First call should use the API
            response1 = self.llm_service.generate_response(query, self.document_chunks)
            assert mock_client.chat.completions.create.call_count == 1
            
            # Second call should use the cache
            response2 = self.llm_service.generate_response(query, self.document_chunks)
            
            # Verify both responses are identical
            assert response1 == response2
            
            # Verify OpenAI client was still only called once
            assert mock_client.chat.completions.create.call_count == 1