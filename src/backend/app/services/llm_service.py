"""
Service module that handles integration with the Language Model API for generating
contextual responses based on document content and user queries.

This module provides functionality for prompt construction, response generation, 
and handling token limits and context management.
"""

import logging
import time
import uuid
from typing import List, Dict, Any, Optional
import functools

import openai  # version 1.0.0+
import backoff  # version 2.2.1+
import tiktoken  # version 0.4.0+

from ..core.config import llm_settings, get_llm_settings
from ..schemas.query import QueryResponse

# Configure logger
logger = logging.getLogger(__name__)

# Global variables
_openai_client = None
_tokenizer = None
_response_cache = {}

# System prompt for LLM
SYSTEM_PROMPT = "You are a helpful assistant that answers questions based on the provided document context. Only use information from the provided context to answer the question. If the context doesn't contain relevant information, say \"I don't have enough information to answer this question.\" Provide specific references to the documents you used in your answer."


def get_openai_client():
    """
    Returns the OpenAI client, initializing it if necessary
    
    Returns:
        Initialized OpenAI client
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = openai.Client(api_key=llm_settings.OPENAI_API_KEY.get_secret_value())
        logger.info("OpenAI client initialized")
    return _openai_client


def get_tokenizer():
    """
    Returns the tokenizer for the current LLM model
    
    Returns:
        Tokenizer for the current model
    """
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.encoding_for_model(llm_settings.LLM_MODEL)
        logger.info(f"Tokenizer initialized for model {llm_settings.LLM_MODEL}")
    return _tokenizer


def count_tokens(text: str) -> int:
    """
    Counts the number of tokens in a text string
    
    Args:
        text: The text to count tokens for
    
    Returns:
        Number of tokens in the text
    """
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))


def format_prompt(query: str, context_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formats a prompt with system instructions, context, and query
    
    Args:
        query: The user's query text
        context_documents: List of relevant document chunks with content
    
    Returns:
        List of message objects for the LLM API
    """
    # Create system message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Prepare context from documents
    max_context_tokens = llm_settings.CONTEXT_WINDOW_SIZE - 500  # Reserve tokens for other parts
    context = prepare_context(context_documents, max_context_tokens)
    
    # Ensure context is within token limits
    if context:
        context = truncate_context(context, max_context_tokens)
    
    # Create user message with context and query
    user_content = f"Context:\n{context}\n\nQuestion: {query}"
    messages.append({"role": "user", "content": user_content})
    
    return messages


def prepare_context(documents: List[Dict[str, Any]], max_tokens: int) -> str:
    """
    Prepares context from relevant documents with token limit management
    
    Args:
        documents: List of document chunks with content and metadata
        max_tokens: Maximum number of tokens allowed for context
    
    Returns:
        Formatted context string within token limit
    """
    context = ""
    token_count = 0
    
    # Sort documents by similarity score (descending) if available
    if documents and "similarity_score" in documents[0]:
        documents = sorted(documents, key=lambda x: x.get("similarity_score", 0), reverse=True)
    
    for i, doc in enumerate(documents):
        document_id = doc.get("document_id") or doc.get("id", f"doc-{i}")
        content = doc.get("content", "")
        
        # Format document content with reference
        doc_text = f"Document {i+1} [ID: {document_id}]:\n{content}\n\n"
        doc_tokens = count_tokens(doc_text)
        
        # Check if adding this document would exceed token limit
        if token_count + doc_tokens > max_tokens:
            break
        
        context += doc_text
        token_count += doc_tokens
    
    return context


def truncate_context(context: str, max_tokens: int) -> str:
    """
    Truncates context to fit within token limit
    
    Args:
        context: The context text to truncate
        max_tokens: Maximum number of tokens allowed
    
    Returns:
        Truncated context
    """
    context_tokens = count_tokens(context)
    
    if context_tokens <= max_tokens:
        return context
    
    # If context exceeds token limit, truncate it
    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(context)
    truncated_tokens = tokens[:max_tokens - 50]  # Reserve tokens for truncation notice
    truncated_context = tokenizer.decode(truncated_tokens)
    
    # Add truncation notice
    truncated_context += "\n\n[Context truncated due to length limitations]"
    
    return truncated_context


def get_cache_key(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """
    Generates a cache key for a query and context
    
    Args:
        query: The user's query text
        context_documents: List of relevant document chunks
    
    Returns:
        Cache key string
    """
    # Use query and document IDs to create a unique key
    doc_ids = [str(doc.get("document_id") or doc.get("id", "")) for doc in context_documents]
    doc_ids.sort()  # Sort for consistency
    return f"{query}:{','.join(doc_ids)}"


def check_cache(query: str, context_documents: List[Dict[str, Any]]) -> Optional[str]:
    """
    Checks if a response is cached for the given query and context
    
    Args:
        query: The user's query text
        context_documents: List of relevant document chunks
    
    Returns:
        Cached response or None if not found
    """
    if not llm_settings.USE_CACHE:
        return None
    
    cache_key = get_cache_key(query, context_documents)
    
    if cache_key in _response_cache:
        cached_item = _response_cache[cache_key]
        timestamp, response = cached_item
        
        # Check if cache is still valid
        if time.time() - timestamp < llm_settings.CACHE_TTL_SECONDS:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return response
    
    return None


def update_cache(query: str, context_documents: List[Dict[str, Any]], response: str) -> None:
    """
    Updates the cache with a new response
    
    Args:
        query: The user's query text
        context_documents: List of relevant document chunks
        response: The generated response
    """
    if not llm_settings.USE_CACHE:
        return
    
    cache_key = get_cache_key(query, context_documents)
    
    # Store response with current timestamp
    _response_cache[cache_key] = (time.time(), response)
    
    # Prune cache if it gets too large (simple LRU)
    if len(_response_cache) > 1000:  # Arbitrary limit
        logger.debug("Pruning response cache")
        # Remove oldest 20% of entries
        sorted_keys = sorted(_response_cache.keys(), key=lambda k: _response_cache[k][0])
        for key in sorted_keys[:200]:
            del _response_cache[key]


@backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=3)
def generate_response(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """
    Generates an AI response based on query and context documents
    
    Args:
        query: The user's query text
        context_documents: List of relevant document chunks
    
    Returns:
        AI-generated response
    """
    # Check cache first
    cached_response = check_cache(query, context_documents)
    if cached_response:
        return cached_response
    
    # Format prompt
    messages = format_prompt(query, context_documents)
    
    # Get OpenAI client
    client = get_openai_client()
    
    try:
        logger.debug(f"Sending request to OpenAI API for query: {query[:50]}...")
        start_time = time.time()
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=llm_settings.LLM_MODEL,
            messages=messages,
            temperature=llm_settings.TEMPERATURE,
            max_tokens=llm_settings.MAX_TOKENS,
            timeout=llm_settings.REQUEST_TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        logger.debug(f"OpenAI API response received in {elapsed_time:.2f} seconds")
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Update cache
        update_cache(query, context_documents, response_text)
        
        return response_text
        
    except openai.RateLimitError:
        logger.warning("OpenAI API rate limit exceeded, retrying with backoff...")
        raise
    except openai.APITimeoutError:
        logger.error(f"OpenAI API request timed out after {llm_settings.REQUEST_TIMEOUT} seconds")
        return "I'm sorry, but I couldn't generate a response in time. Please try again later."
    except Exception as e:
        logger.exception(f"Error generating response: {str(e)}")
        return "I'm sorry, but I encountered an error while generating a response. Please try again later."


@backoff.on_exception(backoff.expo, openai.RateLimitError, max_tries=3)
async def async_generate_response(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """
    Asynchronously generates an AI response based on query and context documents
    
    Args:
        query: The user's query text
        context_documents: List of relevant document chunks
    
    Returns:
        AI-generated response
    """
    # Check cache first
    cached_response = check_cache(query, context_documents)
    if cached_response:
        return cached_response
    
    # Format prompt
    messages = format_prompt(query, context_documents)
    
    # Get OpenAI client
    client = get_openai_client()
    
    try:
        logger.debug(f"Sending async request to OpenAI API for query: {query[:50]}...")
        start_time = time.time()
        
        # Call OpenAI API asynchronously
        # Note: The OpenAI Python client v1.0.0+ doesn't have native async methods
        # We use it in an async context, but the call itself is synchronous
        response = client.chat.completions.create(
            model=llm_settings.LLM_MODEL,
            messages=messages,
            temperature=llm_settings.TEMPERATURE,
            max_tokens=llm_settings.MAX_TOKENS,
            timeout=llm_settings.REQUEST_TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        logger.debug(f"OpenAI API response received in {elapsed_time:.2f} seconds")
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Update cache
        update_cache(query, context_documents, response_text)
        
        return response_text
        
    except openai.RateLimitError:
        logger.warning("OpenAI API rate limit exceeded, retrying with backoff...")
        raise
    except openai.APITimeoutError:
        logger.error(f"OpenAI API request timed out after {llm_settings.REQUEST_TIMEOUT} seconds")
        return "I'm sorry, but I couldn't generate a response in time. Please try again later."
    except Exception as e:
        logger.exception(f"Error generating response: {str(e)}")
        return "I'm sorry, but I encountered an error while generating a response. Please try again later."


def create_query_response(query_text: str, relevant_documents: List[Dict[str, Any]]) -> QueryResponse:
    """
    Creates a QueryResponse object with generated response and relevant documents
    
    Args:
        query_text: The user's query text
        relevant_documents: List of relevant document chunks
    
    Returns:
        Complete query response with AI-generated answer
    """
    # Generate AI response
    response_text = generate_response(query_text, relevant_documents)
    
    # Create query response object
    query_id = uuid.uuid4()
    
    return QueryResponse(
        query_id=query_id,
        query_text=query_text,
        response_text=response_text,
        relevant_documents=relevant_documents
    )


async def async_create_query_response(query_text: str, relevant_documents: List[Dict[str, Any]]) -> QueryResponse:
    """
    Asynchronously creates a QueryResponse object with generated response and relevant documents
    
    Args:
        query_text: The user's query text
        relevant_documents: List of relevant document chunks
    
    Returns:
        Complete query response with AI-generated answer
    """
    # Generate AI response asynchronously
    response_text = await async_generate_response(query_text, relevant_documents)
    
    # Create query response object
    query_id = uuid.uuid4()
    
    return QueryResponse(
        query_id=query_id,
        query_text=query_text,
        response_text=response_text,
        relevant_documents=relevant_documents
    )


class LLMService:
    """Service class that provides methods for generating AI responses using LLM"""
    
    def __init__(self):
        """Initializes the LLMService with OpenAI client and tokenizer"""
        self._client = get_openai_client()
        self._tokenizer = get_tokenizer()
        self._cache = {}
        logger.info("LLM service initialized")
    
    def generate_response(self, query: str, context_documents: List[Dict[str, Any]]) -> str:
        """
        Generates an AI response based on query and context documents
        
        Args:
            query: The user's query text
            context_documents: List of relevant document chunks
        
        Returns:
            AI-generated response
        """
        return generate_response(query, context_documents)
    
    async def async_generate_response(self, query: str, context_documents: List[Dict[str, Any]]) -> str:
        """
        Asynchronously generates an AI response based on query and context documents
        
        Args:
            query: The user's query text
            context_documents: List of relevant document chunks
        
        Returns:
            AI-generated response
        """
        return await async_generate_response(query, context_documents)
    
    def format_prompt(self, query: str, context_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats a prompt with system instructions, context, and query
        
        Args:
            query: The user's query text
            context_documents: List of relevant document chunks
        
        Returns:
            Formatted prompt messages
        """
        return format_prompt(query, context_documents)
    
    def prepare_context(self, documents: List[Dict[str, Any]], max_tokens: int) -> str:
        """
        Prepares context from relevant documents with token limit management
        
        Args:
            documents: List of document chunks with content and metadata
            max_tokens: Maximum number of tokens allowed for context
        
        Returns:
            Formatted context string within token limit
        """
        return prepare_context(documents, max_tokens)
    
    def count_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in a text string
        
        Args:
            text: The text to count tokens for
        
        Returns:
            Number of tokens in the text
        """
        return len(self._tokenizer.encode(text))
    
    def create_query_response(self, query_text: str, relevant_documents: List[Dict[str, Any]]) -> QueryResponse:
        """
        Creates a QueryResponse object with generated response and relevant documents
        
        Args:
            query_text: The user's query text
            relevant_documents: List of relevant document chunks
        
        Returns:
            Complete query response with AI-generated answer
        """
        return create_query_response(query_text, relevant_documents)
    
    async def async_create_query_response(self, query_text: str, relevant_documents: List[Dict[str, Any]]) -> QueryResponse:
        """
        Asynchronously creates a QueryResponse object with generated response and relevant documents
        
        Args:
            query_text: The user's query text
            relevant_documents: List of relevant document chunks
        
        Returns:
            Complete query response with AI-generated answer
        """
        return await async_create_query_response(query_text, relevant_documents)
    
    def check_cache(self, query: str, context_documents: List[Dict[str, Any]]) -> Optional[str]:
        """
        Checks if a response is cached for the given query and context
        
        Args:
            query: The user's query text
            context_documents: List of relevant document chunks
        
        Returns:
            Cached response or None if not found
        """
        if not llm_settings.USE_CACHE:
            return None
        
        cache_key = get_cache_key(query, context_documents)
        
        if cache_key in self._cache:
            timestamp, response = self._cache[cache_key]
            
            # Check if cache is still valid
            if time.time() - timestamp < llm_settings.CACHE_TTL_SECONDS:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return response
        
        return None
    
    def update_cache(self, query: str, context_documents: List[Dict[str, Any]], response: str) -> None:
        """
        Updates the cache with a new response
        
        Args:
            query: The user's query text
            context_documents: List of relevant document chunks
            response: The generated response
        """
        if not llm_settings.USE_CACHE:
            return
        
        cache_key = get_cache_key(query, context_documents)
        
        # Store response with current timestamp
        self._cache[cache_key] = (time.time(), response)
        
        # Prune cache if it gets too large (simple LRU)
        if len(self._cache) > 1000:  # Arbitrary limit
            logger.debug("Pruning response cache")
            # Remove oldest 20% of entries
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][0])
            for key in sorted_keys[:200]:
                del self._cache[key]