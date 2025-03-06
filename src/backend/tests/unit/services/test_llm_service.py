"""
Unit tests for the LLM service component that handles integration with language models 
for generating contextual responses based on document content and user queries.
"""

import uuid
import pytest
from unittest.mock import Mock, patch, MagicMock
import pytest_asyncio
import openai
import tiktoken

from app.services.llm_service import (
    LLMService, 
    SYSTEM_PROMPT
)
from app.schemas.query import QueryResponse
from app.schemas.document_chunk import DocumentChunkWithSimilarity
from app.core.config import get_llm_settings

# Test data
MOCK_DOCUMENT_CHUNKS = [
    {
        'id': uuid.uuid4(),
        'document_id': uuid.uuid4(),
        'chunk_index': 0,
        'content': 'This is a test document about artificial intelligence.',
        'token_count': 10,
        'embedding_id': 'test-embedding-1',
        'similarity_score': 0.95
    },
    {
        'id': uuid.uuid4(),
        'document_id': uuid.uuid4(),
        'chunk_index': 1,
        'content': 'Vector databases are used for semantic search applications.',
        'token_count': 12,
        'embedding_id': 'test-embedding-2',
        'similarity_score': 0.85
    },
    {
        'id': uuid.uuid4(),
        'document_id': uuid.uuid4(),
        'chunk_index': 2,
        'content': 'Large language models can generate human-like text responses.',
        'token_count': 11,
        'embedding_id': 'test-embedding-3',
        'similarity_score': 0.75
    }
]

MOCK_QUERY = "What is artificial intelligence?"

MOCK_RESPONSE = "Artificial intelligence refers to systems or machines that can perform tasks that typically require human intelligence. Based on the provided context, artificial intelligence is mentioned in the test document, but no detailed definition is provided in the available information."


class TestLLMService:
    """Test class for the LLMService component"""
    
    def setup_method(self):
        """Set up method that runs before each test"""
        # Create mock OpenAI client
        self.mock_client = Mock()
        self.mock_chat_completion = Mock()
        self.mock_client.chat.completions.create.return_value = self.mock_chat_completion
        self.mock_chat_completion.choices = [Mock(message=Mock(content=MOCK_RESPONSE))]
        
        # Create mock tokenizer
        self.mock_tokenizer = Mock()
        self.mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        
        # Set up document chunks
        self.document_chunks = MOCK_DOCUMENT_CHUNKS
        
        # Patch external dependencies
        with patch('app.services.llm_service.get_openai_client', return_value=self.mock_client), \
             patch('app.services.llm_service.get_tokenizer', return_value=self.mock_tokenizer):
            
            # Initialize LLM service
            self.llm_service = LLMService()
    
    def test_initialization(self):
        """Test that LLMService initializes correctly"""
        assert self.llm_service._client == self.mock_client
        assert self.llm_service._tokenizer == self.mock_tokenizer
        assert hasattr(self.llm_service, '_cache')
    
    def test_count_tokens(self):
        """Test token counting functionality"""
        test_text = "This is a test text"
        
        # Mock the tokenizer to return a list with 5 items
        self.mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        
        # Call the method
        token_count = self.llm_service.count_tokens(test_text)
        
        # Assert
        assert token_count == 5
        self.mock_tokenizer.encode.assert_called_once_with(test_text)
    
    def test_format_prompt(self):
        """Test prompt formatting"""
        query = MOCK_QUERY
        context = "This is the context from documents."
        
        # Mock prepare_context to return our test context
        with patch.object(self.llm_service, 'prepare_context', return_value=context):
            # Call the method
            messages = self.llm_service.format_prompt(query, self.document_chunks)
            
            # Assert
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == SYSTEM_PROMPT
            assert messages[1]["role"] == "user"
            assert context in messages[1]["content"]
            assert query in messages[1]["content"]
    
    def test_prepare_context(self):
        """Test context preparation from documents"""
        max_tokens = 100
        
        # Mock count_tokens to return predictable values
        with patch.object(self.llm_service, 'count_tokens', side_effect=lambda x: len(x.split())):
            # Call the method
            context = self.llm_service.prepare_context(self.document_chunks, max_tokens)
            
            # Assert
            assert context != ""
            # Verify documents are included in the context
            for doc in self.document_chunks:
                assert doc['content'] in context
            
            # Verify documents are sorted by similarity score
            first_doc_index = context.find(self.document_chunks[0]['content'])
            second_doc_index = context.find(self.document_chunks[1]['content'])
            third_doc_index = context.find(self.document_chunks[2]['content'])
            
            assert first_doc_index < second_doc_index < third_doc_index
    
    def test_generate_response(self):
        """Test response generation"""
        query = MOCK_QUERY
        
        # Mock format_prompt to return a predetermined prompt
        mock_prompt = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\nTest context\n\nQuestion: {query}"}
        ]
        with patch.object(self.llm_service, 'format_prompt', return_value=mock_prompt):
            # Call the method
            response = self.llm_service.generate_response(query, self.document_chunks)
            
            # Assert
            assert response == MOCK_RESPONSE
            self.mock_client.chat.completions.create.assert_called_once()
            call_kwargs = self.mock_client.chat.completions.create.call_args[1]
            assert call_kwargs['messages'] == mock_prompt
    
    @pytest.mark.asyncio
    async def test_async_generate_response(self):
        """Test async response generation"""
        query = MOCK_QUERY
        
        # Mock format_prompt to return a predetermined prompt
        mock_prompt = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\nTest context\n\nQuestion: {query}"}
        ]
        with patch.object(self.llm_service, 'format_prompt', return_value=mock_prompt):
            # Call the method
            response = await self.llm_service.async_generate_response(query, self.document_chunks)
            
            # Assert
            assert response == MOCK_RESPONSE
            self.mock_client.chat.completions.create.assert_called_once()
            call_kwargs = self.mock_client.chat.completions.create.call_args[1]
            assert call_kwargs['messages'] == mock_prompt
    
    def test_create_query_response(self):
        """Test creation of QueryResponse object"""
        query = MOCK_QUERY
        
        # Mock generate_response to return a predetermined response
        with patch.object(self.llm_service, 'generate_response', return_value=MOCK_RESPONSE):
            # Call the method
            response = self.llm_service.create_query_response(query, self.document_chunks)
            
            # Assert
            assert isinstance(response, QueryResponse)
            assert response.query_text == query
            assert response.response_text == MOCK_RESPONSE
            assert response.relevant_documents == self.document_chunks
            assert response.query_id is not None
    
    @pytest.mark.asyncio
    async def test_async_create_query_response(self):
        """Test async creation of QueryResponse object"""
        query = MOCK_QUERY
        
        # Mock async_generate_response to return a predetermined response
        with patch.object(self.llm_service, 'async_generate_response', return_value=MOCK_RESPONSE):
            # Call the method
            response = await self.llm_service.async_create_query_response(query, self.document_chunks)
            
            # Assert
            assert isinstance(response, QueryResponse)
            assert response.query_text == query
            assert response.response_text == MOCK_RESPONSE
            assert response.relevant_documents == self.document_chunks
            assert response.query_id is not None
    
    def test_caching(self):
        """Test response caching mechanism"""
        query = MOCK_QUERY
        
        # Call generate_response twice with the same input
        with patch.object(self.llm_service, 'check_cache', side_effect=[None, MOCK_RESPONSE]), \
             patch.object(self.llm_service, 'update_cache'):
            
            # First call should use the OpenAI API
            response1 = self.llm_service.generate_response(query, self.document_chunks)
            
            # Reset the mock to track new calls
            self.mock_client.chat.completions.create.reset_mock()
            
            # Second call should use the cache (we're mocking check_cache to return MOCK_RESPONSE)
            response2 = self.llm_service.generate_response(query, self.document_chunks)
            
            # Assert
            assert response1 == MOCK_RESPONSE
            assert response2 == MOCK_RESPONSE
            # API should only be called once (on the first call)
            assert not self.mock_client.chat.completions.create.called
    
    def test_token_limit_handling(self):
        """Test token limit handling"""
        # Create test document chunks with known token counts
        documents = [
            {'content': 'Doc 1', 'token_count': 20, 'similarity_score': 0.9, 'document_id': uuid.uuid4()},
            {'content': 'Doc 2', 'token_count': 30, 'similarity_score': 0.8, 'document_id': uuid.uuid4()},
            {'content': 'Doc 3', 'token_count': 40, 'similarity_score': 0.7, 'document_id': uuid.uuid4()},
        ]
        
        # Set a token limit that will only include the first two documents
        max_tokens = 60
        
        # Mock count_tokens to return the token_count of the document
        with patch.object(self.llm_service, 'count_tokens', side_effect=lambda x: len(x) * 10):
            # Call the method
            context = self.llm_service.prepare_context(documents, max_tokens)
            
            # Assert
            assert 'Doc 1' in context
            assert 'Doc 2' in context
            assert 'Doc 3' not in context  # This should be excluded due to token limit
    
    def test_error_handling(self):
        """Test error handling for API failures"""
        query = MOCK_QUERY
        
        # Mock OpenAI client to raise an exception
        self.mock_client.chat.completions.create.side_effect = Exception("API error")
        
        # Call the method
        response = self.llm_service.generate_response(query, self.document_chunks)
        
        # Assert that the error message is returned
        assert "error" in response.lower()
        assert "try again" in response.lower()
    
    def test_timeout_handling(self):
        """Test handling of API timeout errors"""
        query = MOCK_QUERY
        
        # Mock OpenAI client to raise a timeout error
        timeout_error = openai.APITimeoutError("Request timed out", request=None)
        self.mock_client.chat.completions.create.side_effect = timeout_error
        
        # Call the method
        response = self.llm_service.generate_response(query, self.document_chunks)
        
        # Assert that the timeout message is returned
        assert "couldn't generate" in response.lower()
        assert "time" in response.lower()
    
    def test_retry_mechanism(self):
        """Test retry mechanism for rate limits"""
        query = MOCK_QUERY
        
        # Mock OpenAI client to raise a rate limit error once, then succeed
        rate_limit_error = openai.RateLimitError("Rate limit exceeded")
        self.mock_client.chat.completions.create.side_effect = [
            rate_limit_error,
            self.mock_chat_completion
        ]
        
        # Mock backoff to avoid actual waiting during tests
        with patch('app.services.llm_service.backoff.expo', return_value=[0]), \
             patch.object(self.llm_service, 'format_prompt', return_value=[]):
            
            # Call the method
            response = self.llm_service.generate_response(query, self.document_chunks)
            
            # Assert
            assert response == MOCK_RESPONSE
            assert self.mock_client.chat.completions.create.call_count == 2  # Called twice due to retry