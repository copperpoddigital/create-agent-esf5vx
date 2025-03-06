# Coding Standards and Guidelines

## Introduction

This document outlines the coding standards and best practices for the Document Management and AI Chatbot System. Adhering to these standards ensures code quality, maintainability, and consistency across the project.

These standards apply to all developers contributing to the project and cover Python code style, documentation requirements, architectural patterns, and security practices. Following these guidelines will help maintain a high-quality codebase and facilitate collaboration among team members.

## Code Style and Formatting

### Python Style Guide

The project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some project-specific modifications. All Python code must adhere to these style guidelines:

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (Black's default)
- Use snake_case for variable and function names
- Use CamelCase for class names
- Use UPPER_CASE for constants
- Use descriptive names that reflect the purpose of variables, functions, and classes
- Avoid single-letter variable names except in very short blocks where the meaning is clear (e.g., `for i in range(10)`)

### Automated Formatting

The project uses the following tools for automated code formatting and linting:

- **Black**: For code formatting
- **isort**: For sorting imports
- **Flake8**: For linting
- **mypy**: For static type checking

These tools are configured in `pyproject.toml` and should be run before committing code:

```bash
# Format code
poetry run black app tests

# Sort imports
poetry run isort app tests

# Lint code
poetry run flake8 app tests

# Type check
poetry run mypy app
```

The CI pipeline will enforce these standards, and pull requests that don't meet them will be rejected.

### Import Organization

Imports should be organized in the following order, with a blank line between each group:

1. Standard library imports
2. Third-party library imports
3. Local application imports

Within each group, imports should be sorted alphabetically.

Example:

```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# Local application imports
from app.core.config import settings
from app.models.document import Document
from app.services.vector_search import VectorSearchService
```

Use absolute imports rather than relative imports when possible.

### Comments and Docstrings

All modules, classes, methods, and functions must have docstrings following the Google style:

```python
def process_document(document_id: str, extract_text: bool = True) -> bool:
    """Process a document and generate vector embeddings.
    
    This function retrieves a document, extracts its text content,
    and generates vector embeddings for search functionality.
    
    Args:
        document_id: The unique identifier of the document to process
        extract_text: Whether to extract text from the document
        
    Returns:
        bool: True if processing was successful, False otherwise
        
    Raises:
        DocumentNotFoundError: If the document doesn't exist
        ProcessingError: If text extraction or embedding generation fails
    """
    # Implementation
```

Inline comments should be used sparingly and only to explain complex logic that isn't immediately obvious from the code itself.

## Project Structure

### Directory Organization

The project follows a modular structure with clear separation of concerns:

```
src/backend/
├── app/
│   ├── api/              # API endpoints and routers
│   │   ├── v1/           # API version 1
│   │   │   └── endpoints/  # API endpoint modules
│   ├── core/             # Core application components
│   ├── crud/             # Database CRUD operations
│   ├── db/               # Database configuration and session
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic schemas for validation
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions
│   └── vector_store/     # Vector database implementation
├── migrations/          # Alembic database migrations
├── scripts/             # Utility scripts
└── tests/               # Test suite
```

Each module should have a clear, single responsibility and should be designed for reusability and testability.

### File Naming Conventions

Follow these naming conventions for files:

- Python modules: snake_case (e.g., `vector_search.py`)
- Test files: `test_` prefix followed by the module name (e.g., `test_vector_search.py`)
- Configuration files: lowercase with appropriate extension (e.g., `pyproject.toml`, `.env.example`)
- Documentation files: Title case with spaces for readability in Markdown (e.g., `Coding Standards.md`)

Each file should contain only one primary class or a group of closely related functions. Keep files focused and avoid creating large, monolithic modules.

### Module Organization

Organize each Python module in the following order:

1. Module docstring
2. Imports (organized as described above)
3. Constants and global variables
4. Exception classes
5. Helper functions and classes
6. Main classes and functions

Example:

```python
"""Vector search service for document similarity search.

This module provides functionality for searching documents based on
vector similarity using FAISS.
"""

# Imports...

# Constants
DEFAULT_TOP_K = 5
VECTOR_DIMENSION = 768

# Exception classes
class VectorSearchError(Exception):
    """Base exception for vector search errors."""
    pass

# Helper functions
def _normalize_vector(vector: List[float]) -> List[float]:
    """Normalize a vector to unit length."""
    # Implementation

# Main class
class VectorSearchService:
    """Service for vector-based document search."""
    # Implementation
```

## Coding Practices

### Type Hints

Use type hints for all function parameters and return values. This improves code readability, enables static type checking with mypy, and provides better IDE support.

```python
from typing import Dict, List, Optional, Tuple, Union

def search_documents(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, str]] = None
) -> List[Dict[str, Union[str, float]]]:
    """Search for documents similar to the query."""
    # Implementation
```

Use the `typing` module for complex types and `Optional` for parameters that can be `None`. For Python 3.10+, you can use the new type annotation syntax where appropriate:

```python
def process_results(results: list[dict[str, str | float]]) -> dict[str, list[str]]:
    """Process search results into a structured format."""
    # Implementation
```

### Error Handling

Follow these guidelines for error handling:

1. Use custom exception classes for domain-specific errors
2. Catch specific exceptions, not `Exception` (unless absolutely necessary)
3. Include meaningful error messages
4. Log exceptions with appropriate context
5. Don't silence exceptions without good reason

Example:

```python
try:
    document = await document_service.get_document(document_id)
except DocumentNotFoundError:
    logger.warning(f"Document not found: {document_id}")
    raise HTTPException(status_code=404, detail="Document not found")
except DatabaseError as e:
    logger.error(f"Database error retrieving document {document_id}: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

For API endpoints, convert domain exceptions to appropriate HTTP exceptions with status codes and error details.

### Asynchronous Programming

The project uses FastAPI's asynchronous capabilities. Follow these guidelines for async code:

1. Use `async`/`await` consistently throughout an execution path
2. Don't mix synchronous and asynchronous code without careful consideration
3. Use `asyncio` primitives for coordination (not `threading` or `multiprocessing`)
4. Be aware of blocking operations and move them to background tasks when appropriate

Example:

```python
async def process_document(document_id: str) -> Document:
    """Process a document asynchronously."""
    document = await get_document(document_id)
    text = await extract_text(document)
    embeddings = await generate_embeddings(text)
    await store_embeddings(document_id, embeddings)
    return document
```

For CPU-bound operations that would block the event loop, use background tasks or consider using a thread pool executor.

### Dependency Injection

Use dependency injection to improve testability and flexibility. FastAPI's dependency injection system should be used for API dependencies, and constructor injection should be used for services.

Example for FastAPI dependencies:

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from the JWT token."""
    # Implementation

@router.get("/documents/")
async def list_documents(current_user: User = Depends(get_current_user)):
    """List documents for the current user."""
    # Implementation
```

Example for service constructor injection:

```python
class DocumentService:
    def __init__(
        self,
        db: Database,
        file_storage: FileStorage,
        embedding_service: EmbeddingService
    ):
        self.db = db
        self.file_storage = file_storage
        self.embedding_service = embedding_service
```

### Configuration Management

Use the centralized configuration system based on Pydantic settings classes. Don't hardcode configuration values in the code.

```python
from app.core.config import get_settings, get_vector_settings

settings = get_settings()
vector_settings = get_vector_settings()

def initialize_vector_index():
    """Initialize the vector index with configured parameters."""
    index_path = vector_settings.VECTOR_INDEX_PATH
    dimension = vector_settings.VECTOR_DIMENSION
    # Implementation using these settings
```

Environment-specific configuration should be loaded from environment variables or `.env` files, never committed to the repository.

## API Design

### RESTful Principles

Follow RESTful principles when designing API endpoints:

1. Use resource-oriented URLs (nouns, not verbs)
2. Use appropriate HTTP methods (GET, POST, PUT, DELETE)
3. Use standard HTTP status codes
4. Implement proper error responses
5. Use query parameters for filtering, sorting, and pagination

Example:

```python
# Good
@router.get("/documents/", response_model=List[DocumentSchema])
@router.get("/documents/{document_id}", response_model=DocumentSchema)
@router.post("/documents/", response_model=DocumentSchema, status_code=201)
@router.delete("/documents/{document_id}", status_code=204)

# Bad
@router.get("/get_documents/")
@router.get("/find_document_by_id/{document_id}")
@router.post("/create_document/")
@router.post("/delete_document/{document_id}")
```

### Request Validation

Use Pydantic models for request validation. Define clear schemas with appropriate field constraints and validation rules.

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(5, ge=1, le=100)
    filters: Optional[dict] = None
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace')
        return v
```

Validate all user input and never trust client-provided data without validation.

### Response Structure

Use consistent response structures across the API. Define response models with Pydantic and use them with FastAPI's `response_model` parameter.

```python
class DocumentResponse(BaseModel):
    id: str
    title: str
    upload_date: datetime
    status: str
    size_bytes: int
    
    class Config:
        orm_mode = True

class PaginatedDocumentResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int

@router.get("/documents/", response_model=PaginatedDocumentResponse)
async def list_documents(
    page: int = 1,
    size: int = 10,
    current_user: User = Depends(get_current_user)
):
    """List documents with pagination."""
    # Implementation
```

Include appropriate metadata in responses, such as pagination information, to help clients consume the API effectively.

### API Versioning

The API uses URL-based versioning with the format `/api/v{version_number}/`. All endpoints should be placed under the appropriate version module.

```python
# app/api/v1/endpoints/documents.py
from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])

# This will be accessible at /api/v1/documents/
@router.get("/")
async def list_documents():
    # Implementation
```

When making breaking changes, create a new API version rather than modifying existing endpoints. Maintain backward compatibility for at least one version.

## Database Practices

### SQLAlchemy Models

Follow these guidelines for SQLAlchemy ORM models:

1. Define models in the `app/models/` directory, one model per file
2. Use the base class from `app/db/base_class.py`
3. Include comprehensive docstrings for models and fields
4. Define relationships explicitly
5. Use appropriate column types and constraints

Example:

```python
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4

from app.db.base_class import Base

class Document(Base):
    """Document model for storing document metadata."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    title = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    upload_date = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    uploader_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    uploader = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
```

### Query Optimization

Write efficient database queries to ensure good performance:

1. Use appropriate indexes for frequently queried columns
2. Fetch only the columns you need (avoid `SELECT *`)
3. Use joins efficiently and avoid N+1 query problems
4. Implement pagination for large result sets
5. Use query optimization techniques like eager loading when appropriate

Example:

```python
async def get_user_documents(user_id: str, skip: int = 0, limit: int = 100):
    """Get documents for a specific user with pagination."""
    query = select(Document).where(Document.uploader_id == user_id)
    query = query.order_by(Document.upload_date.desc())
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

### Migrations

Use Alembic for database migrations:

1. Generate migrations when making model changes
2. Review migrations before committing them
3. Test migrations on a staging environment before production
4. Never modify existing migrations that have been applied to production

```bash
# Generate a new migration
poetry run alembic revision --autogenerate -m "Add status column to documents"

# Apply migrations
poetry run alembic upgrade head
```

Include meaningful messages in migration files and document any manual steps required.

### Transaction Management

Use transactions to ensure data consistency:

1. Group related operations in a single transaction
2. Handle transaction rollback on errors
3. Be mindful of transaction isolation levels

Example:

```python
async def create_document_with_chunks(document_data: dict, chunks_data: list):
    """Create a document and its chunks in a single transaction."""
    async with db.transaction():
        # Create document
        document = Document(**document_data)
        db.add(document)
        await db.flush()  # Flush to get the document ID
        
        # Create chunks with the document ID
        for chunk_data in chunks_data:
            chunk = DocumentChunk(document_id=document.id, **chunk_data)
            db.add(chunk)
        
        # The transaction will be committed if no exceptions occur
        # or rolled back if an exception is raised
```

## Vector Search Implementation

### FAISS Integration

Follow these guidelines for FAISS vector store implementation:

1. Use the abstraction layer defined in `app/vector_store/base.py`
2. Implement proper error handling for FAISS operations
3. Ensure thread safety for concurrent operations
4. Implement periodic index persistence to disk

Example:

```python
from app.vector_store.base import VectorStore
import faiss
import numpy as np
from typing import Dict, List, Tuple

class FAISSVectorStore(VectorStore):
    """FAISS implementation of the vector store."""
    
    def __init__(self, dimension: int, index_path: str = None):
        """Initialize the FAISS vector store.
        
        Args:
            dimension: Vector dimension
            index_path: Path to load existing index from
        """
        self.dimension = dimension
        self.index = self._create_index() if not index_path else self._load_index(index_path)
        self.id_map: Dict[str, int] = {}  # Map external IDs to FAISS internal IDs
        self.next_id = 0
    
    def _create_index(self) -> faiss.Index:
        """Create a new FAISS index."""
        return faiss.IndexFlatIP(self.dimension)  # Inner product similarity
    
    # Additional implementation...
```

### Embedding Generation

For text embedding generation:

1. Use the Sentence Transformers library for generating embeddings
2. Implement caching for frequently used embeddings
3. Process text appropriately before generating embeddings
4. Handle large documents by chunking and generating embeddings for each chunk

Example:

```python
from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the Sentence Transformers model to use
        """
        self.model = SentenceTransformer(model_name)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List[float]: Vector embedding
        """
        # Preprocess text if needed
        embedding = self.model.encode(text, convert_to_numpy=True).tolist()
        return embedding
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List[List[float]]: List of vector embeddings
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()
        return embeddings
```

### Search Optimization

Optimize vector search for performance and relevance:

1. Use appropriate FAISS index types based on the dataset size
2. Implement filtering capabilities to narrow search results
3. Normalize vectors before search when using cosine similarity
4. Implement caching for frequent queries

Example:

```python
async def search(self, query: str, top_k: int = 5, filters: dict = None) -> List[dict]:
    """Search for documents similar to the query.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        filters: Optional filters to apply to results
        
    Returns:
        List of search results with document info and similarity scores
    """
    # Generate query embedding
    query_embedding = await self.embedding_service.generate_embedding(query)
    
    # Perform vector search
    vector_results = await self.vector_store.search(query_embedding, top_k=top_k * 2)  # Get extra results for filtering
    
    # Retrieve document information
    document_ids = [result[0] for result in vector_results]
    documents = await self.document_service.get_documents_by_ids(document_ids)
    
    # Apply filters if provided
    if filters:
        documents = [doc for doc in documents if self._apply_filters(doc, filters)]
    
    # Combine document info with similarity scores
    results = [
        {
            "document_id": doc.id,
            "title": doc.title,
            "similarity": score,
            "content": doc.content
        }
        for (doc_id, score), doc in zip(vector_results, documents)
        if doc is not None  # In case a document was deleted but still in the index
    ][:top_k]  # Limit to top_k after filtering
    
    return results
```

## LLM Integration

### OpenAI API Usage

Follow these guidelines for OpenAI API integration:

1. Use the official OpenAI Python client
2. Implement proper error handling and retries for API calls
3. Manage token usage to stay within limits
4. Secure API keys using environment variables

Example:

```python
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_llm_settings

llm_settings = get_llm_settings()
openai.api_key = llm_settings.OPENAI_API_KEY.get_secret_value()

class LLMService:
    """Service for interacting with language models."""
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, query: str, context: str) -> str:
        """Generate a response based on the query and context.
        
        Args:
            query: User query
            context: Document context for the response
            
        Returns:
            Generated response text
            
        Raises:
            LLMServiceError: If the API call fails after retries
        """
        try:
            response = openai.ChatCompletion.create(
                model=llm_settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
                ],
                max_tokens=llm_settings.MAX_TOKENS,
                temperature=0.7
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            raise LLMServiceError(f"OpenAI API error: {str(e)}")
```

### Prompt Engineering

Apply best practices for prompt engineering:

1. Use clear and specific instructions in system prompts
2. Structure prompts consistently
3. Include relevant context for grounded responses
4. Implement safeguards against prompt injection

Example:

```python
def create_prompt(query: str, context: List[str]) -> List[dict]:
    """Create a prompt for the language model.
    
    Args:
        query: User query
        context: List of relevant document chunks
        
    Returns:
        Formatted prompt messages
    """
    # System prompt with clear instructions
    system_prompt = (
        "You are a helpful assistant that answers questions based on the provided document context. "
        "Only use information from the context to answer the question. "
        "If the context doesn't contain relevant information, say 'I don't have enough information to answer this question.' "
        "Provide specific references to the documents you used in your answer."
    )
    
    # Format context with document references
    formatted_context = "\n\n".join([f"Document {i+1}: {chunk}" for i, chunk in enumerate(context)])
    
    # User prompt with context and query
    user_prompt = f"Context:\n{formatted_context}\n\nQuestion: {query}"
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
```

### Response Processing

Process LLM responses appropriately:

1. Validate and sanitize responses
2. Extract structured information when needed
3. Handle edge cases and unexpected responses
4. Implement fallback mechanisms for API failures

Example:

```python
async def process_response(self, response: str) -> dict:
    """Process the LLM response.
    
    Args:
        response: Raw response from the LLM
        
    Returns:
        Processed response with additional metadata
    """
    # Basic sanitization
    sanitized_response = response.strip()
    
    # Extract document references if present
    references = self._extract_references(sanitized_response)
    
    # Check for "I don't have enough information" responses
    has_information = not any(phrase in sanitized_response.lower() for phrase in [
        "i don't have enough information",
        "the context doesn't provide",
        "no information available"
    ])
    
    return {
        "answer": sanitized_response,
        "references": references,
        "has_information": has_information
    }
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract document references from the response."""
        # Implementation to extract document references
        # This could use regex or other text processing techniques
```

## Security Practices

### Authentication and Authorization

Implement secure authentication and authorization:

1. Use JWT tokens with appropriate expiration
2. Implement proper password hashing with Passlib
3. Apply the principle of least privilege
4. Use role-based access control

Example:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import get_security_settings

security_settings = get_security_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            security_settings.JWT_SECRET.get_secret_value(),
            algorithms=[security_settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Input Validation and Sanitization

Validate and sanitize all user input:

1. Use Pydantic models for request validation
2. Implement additional validation for complex requirements
3. Sanitize data before using it in database queries or external APIs
4. Be particularly careful with file uploads

Example:

```python
from pydantic import BaseModel, Field, validator
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('email')
    def email_valid(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        return v
```

### Secure File Handling

Implement secure file handling practices:

1. Validate file types and sizes before processing
2. Store files outside the web root
3. Use secure file naming to prevent path traversal
4. Scan uploaded files for malware when possible

Example:

```python
import os
import uuid
from fastapi import UploadFile, HTTPException
from app.core.config import get_document_settings

document_settings = get_document_settings()

async def save_uploaded_file(file: UploadFile) -> str:
    """Save an uploaded file securely.
    
    Args:
        file: The uploaded file
        
    Returns:
        The path where the file was saved
        
    Raises:
        HTTPException: If the file type is not allowed or the file is too large
    """
    # Validate file type
    content_type = file.content_type
    if content_type not in document_settings.ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {document_settings.ALLOWED_DOCUMENT_TYPES}"
        )
    
    # Validate file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()  # Get position (file size)
    file.file.seek(0)  # Seek back to start
    
    max_size_bytes = document_settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {document_settings.MAX_DOCUMENT_SIZE_MB}MB"
        )
    
    # Generate secure filename
    file_extension = os.path.splitext(file.filename)[1].lower()
    secure_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create directory if it doesn't exist
    os.makedirs(document_settings.DOCUMENT_STORAGE_PATH, exist_ok=True)
    
    # Save file
    file_path = os.path.join(document_settings.DOCUMENT_STORAGE_PATH, secure_filename)
    with open(file_path, "wb") as f:
        while chunk := await file.read(chunk_size):
            f.write(chunk)
    
    return file_path
```

### Secure Coding Against Common Vulnerabilities

Protect against common security vulnerabilities:

1. SQL Injection: Use parameterized queries with SQLAlchemy
2. Cross-Site Scripting (XSS): Validate and sanitize user input
3. Cross-Site Request Forgery (CSRF): Implement CSRF protection
4. Insecure Direct Object References: Validate user permissions for resource access
5. Security Misconfiguration: Use secure default settings

Example for preventing SQL injection:

```python
# Good - Using SQLAlchemy's parameterized queries
async def get_documents_by_title(title: str):
    query = select(Document).where(Document.title.contains(title))
    result = await db.execute(query)
    return result.scalars().all()

# Bad - Never do this
async def get_documents_by_title_unsafe(title: str):
    query = f"SELECT * FROM documents WHERE title LIKE '%{title}%'"
    result = await db.execute(text(query))  # Vulnerable to SQL injection
    return result.fetchall()
```

Example for preventing insecure direct object references:

```python
async def get_document(document_id: str, current_user: User):
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has access to this document
    if document.uploader_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    return document
```

## Testing Requirements

### Test Coverage

Maintain high test coverage for the codebase:

1. Minimum 85% overall code coverage
2. 90% coverage for core business logic
3. 85% coverage for API endpoints
4. 80% coverage for utility functions

All new code must be accompanied by appropriate tests. Pull requests that decrease coverage will be rejected.

Project tests should be located in the tests directory with a structure that mirrors the application's structure.

### Test Types

Implement multiple types of tests:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test interactions between components
3. **API Tests**: Test API endpoints through HTTP requests
4. **Performance Tests**: Test system performance under load

Each type of test serves a different purpose and helps ensure overall system quality.

### Test Naming and Organization

Follow these conventions for test organization:

1. Place tests in the `tests` directory with a structure mirroring the application
2. Name test files with a `test_` prefix
3. Name test functions descriptively, indicating what is being tested and expected outcome
4. Group related tests in classes when appropriate

Example:

```python
# tests/unit/services/test_vector_search.py

import pytest
from unittest.mock import Mock
from app.services.vector_search import VectorSearchService

class TestVectorSearchService:
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_faiss = Mock()
        self.mock_embedding_service = Mock()
        self.service = VectorSearchService(
            faiss_store=self.mock_faiss,
            embedding_service=self.mock_embedding_service
        )
    
    def test_search_returns_relevant_documents(self):
        """Test that search returns relevant documents."""
        # Arrange
        query = "test query"
        self.mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        self.mock_faiss.search.return_value = [("doc1", 0.9), ("doc2", 0.8)]
        
        # Act
        results = self.service.search(query, top_k=2)
        
        # Assert
        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[0]["score"] == 0.9
        self.mock_embedding_service.generate_embedding.assert_called_once_with(query)
        self.mock_faiss.search.assert_called_once()
```

## Documentation

### Code Documentation

Document code thoroughly:

1. Include docstrings for all modules, classes, methods, and functions
2. Follow Google-style docstring format
3. Document parameters, return values, and exceptions
4. Include examples for complex functions

Example:

```python
def search_documents(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Search for documents similar to the query.
    
    This function performs a semantic search using vector embeddings to find
    documents that are conceptually similar to the query, regardless of
    exact keyword matches.
    
    Args:
        query: The search query text
        top_k: Maximum number of results to return (default: 5)
        filters: Optional dictionary of filters to apply to results
              Example: {"status": "available", "uploader_id": "user123"}
    
    Returns:
        List of dictionaries containing document information and similarity scores
        Example:
        [
            {
                "document_id": "abc123",
                "title": "Example Document",
                "similarity": 0.89,
                "content": "Document content snippet..."
            },
            ...
        ]
    
    Raises:
        VectorSearchError: If the search operation fails
        EmbeddingError: If generating query embedding fails
    """
    # Implementation
```

### API Documentation

Document API endpoints thoroughly:

1. Use FastAPI's built-in documentation capabilities
2. Include detailed descriptions for endpoints, parameters, and responses
3. Document error responses and status codes
4. Provide examples for request and response bodies

Example:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.schemas.query import QueryRequest, QueryResponse
from app.services.vector_search import VectorSearchService
from app.api.dependencies import get_current_user, get_vector_search_service
from app.models.user import User

router = APIRouter()

@router.post(
    "/",
    response_model=QueryResponse,
    summary="Search documents",
    description="Perform a semantic search across documents using the provided query text."
)
async def search_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    vector_search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """Search for documents similar to the query.
    
    This endpoint performs a semantic search to find documents that are
    conceptually similar to the query, regardless of exact keyword matches.
    
    - **query**: Search query text
    - **top_k**: Maximum number of results to return (default: 5)
    - **filters**: Optional filters to apply to results
    
    Returns a list of relevant documents with similarity scores and an AI-generated
    response based on the document content.
    """
    try:
        results = await vector_search_service.search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        return QueryResponse(
            query_id=str(uuid.uuid4()),
            query=request.query,
            relevant_documents=results,
            response="AI-generated response based on documents"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Project Documentation

Maintain comprehensive project documentation:

1. README.md with project overview and setup instructions
2. Architecture documentation explaining system design
3. API documentation for external consumers
4. Development guides for contributors

All documentation should be kept up-to-date as the codebase evolves.

## Code Review Process

### Pull Request Requirements

All code changes must be submitted through pull requests that meet these requirements:

1. Reference an issue or user story
2. Include a clear description of changes
3. Pass all automated checks (linting, tests, etc.)
4. Include appropriate tests for new functionality
5. Follow all coding standards outlined in this document

Pull requests that don't meet these requirements will be rejected.

### Code Review Checklist

Reviewers should check for the following during code reviews:

1. **Functionality**: Does the code work as expected?
2. **Code Quality**: Is the code well-structured, readable, and maintainable?
3. **Performance**: Are there any performance concerns?
4. **Security**: Are there any security vulnerabilities?
5. **Testing**: Are tests comprehensive and well-written?
6. **Documentation**: Is the code properly documented?
7. **Standards Compliance**: Does the code follow project standards?

Provide constructive feedback and suggest improvements rather than just pointing out issues.

### Review Process

Follow this process for code reviews:

1. Author submits pull request
2. CI pipeline runs automated checks
3. Reviewer(s) examine the code and provide feedback
4. Author addresses feedback and updates the pull request
5. Reviewer(s) approve the changes
6. Code is merged to the target branch

Aim to complete reviews within 2 business days to maintain development velocity.

## Version Control Practices

### Branching Strategy

The project uses a simplified Git Flow branching strategy:

1. `main`: Production-ready code
2. `develop`: Integration branch for features
3. `feature/*`: Feature branches
4. `bugfix/*`: Bug fix branches
5. `release/*`: Release preparation branches

Feature and bugfix branches should be created from `develop` and merged back to `develop` when complete.

### Commit Messages

Write clear, descriptive commit messages following these guidelines:

1. Use the imperative mood ("Add feature" not "Added feature")
2. First line is a concise summary (50 chars or less)
3. Followed by a blank line
4. Followed by a detailed description if necessary
5. Reference issue numbers when applicable

Example:

```
Add vector search caching for improved performance

Implement LRU cache for vector search results to reduce
redundant FAISS operations and improve query response time.
Cache is configurable with TTL and size limits.

Resolves #123
```

### Pull Request Naming

Name pull requests clearly with a prefix indicating the type of change:

1. `feat:` for new features
2. `fix:` for bug fixes
3. `docs:` for documentation changes
4. `refactor:` for code refactoring
5. `test:` for adding or modifying tests
6. `chore:` for maintenance tasks

Example: `feat: Implement vector search caching`

## Conclusion

These coding standards are designed to ensure code quality, maintainability, and consistency across the Document Management and AI Chatbot System. All developers contributing to the project are expected to follow these guidelines.

The standards will evolve over time as the project grows and new best practices emerge. Suggestions for improvements are welcome and should be submitted as issues or pull requests.

For questions or clarifications about these standards, please contact the project maintainers.