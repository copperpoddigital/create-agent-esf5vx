"""
Defines pytest fixtures for the Document Management and AI Chatbot System's test suite.
This module provides reusable test components such as database sessions, test clients, mock users, sample documents, and mock vector store for both unit and integration tests.
"""
import os  # standard library
import tempfile  # standard library
import uuid  # standard library
from datetime import datetime  # standard library
from typing import AsyncGenerator, Generator  # standard library

import pytest  # pytest 7.0.0+
import pytest_asyncio  # pytest-asyncio 0.20.0+
import numpy as np  # numpy 1.24.0+
from sqlalchemy import create_engine  # sqlalchemy 2.0.0+
from sqlalchemy.orm import sessionmaker, Session  # sqlalchemy 2.0.0+
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # sqlalchemy 2.0.0+
from fastapi import FastAPI  # fastapi 0.95.0+
from fastapi.testclient import TestClient  # fastapi 0.95.0+
import httpx  # httpx 0.24.0+

from ..app.db.session import SessionLocal, AsyncSessionLocal  # Import session factory for creating test database sessions
from ..app.db.base import Base  # Import SQLAlchemy base class for creating test database schema
from ..app.models.user import User, UserRole  # Import User model for creating test users
from ..app.models.document import Document, DocumentStatus  # Import Document model for creating test documents
from ..app.core.security import get_password_hash, create_access_token  # Import password hashing function for test user creation
from ..app.vector_store.faiss_store import FAISSStore  # Import FAISS vector store for mocking in tests
from ..app.main import app  # Import FastAPI application for test client
from ..app.api.dependencies import get_db_dependency, get_async_db_dependency  # Import database dependency for overriding in tests

TEST_DATABASE_URL = "sqlite:///./test.db"


def setup_test_db() -> None:
    """
    Creates a new test database with schema
    """
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)


def teardown_test_db() -> None:
    """
    Drops all tables from the test database
    """
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """
    Sets up and tears down the test database for the entire test session
    """
    setup_test_db()
    yield
    teardown_test_db()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """
    Provide a database session for tests
    """
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocalTest()
    try:
        yield db
    finally:
        db.close()


@pytest_asyncio.fixture()
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session for tests
    """
    engine = create_async_engine(TEST_DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"))
    AsyncSessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    async with AsyncSessionLocalTest() as db:
        try:
            yield db
        finally:
            await db.close()


@pytest.fixture()
def override_get_db(db_session: Session):
    """
    Override database dependency to use test database
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db_dependency] = _override_get_db
    return _override_get_db


@pytest_asyncio.fixture()
async def override_get_async_db(async_db_session: AsyncSession):
    """
    Override async database dependency to use test database
    """
    async def _override_get_async_db():
        try:
            yield async_db_session
        finally:
            await async_db_session.rollback()

    app.dependency_overrides[get_async_db_dependency] = _override_get_async_db
    return _override_get_async_db


@pytest.fixture()
def client(db_session: Session, override_get_db) -> TestClient:
    """
    Provide a FastAPI TestClient for API testing
    """
    override_get_db(db_session)
    client = TestClient(app)
    return client


@pytest_asyncio.fixture()
async def async_client(async_db_session: AsyncSession, override_get_async_db) -> httpx.AsyncClient:
    """
    Provide an async client for async API testing
    """
    override_get_async_db(async_db_session)
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture()
def test_user(db_session: Session) -> User:
    """
    Provide a regular test user
    """
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        role=UserRole.regular,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def test_admin(db_session: Session) -> User:
    """
    Provide an admin test user
    """
    admin = User(
        id=uuid.uuid4(),
        username="testadmin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture()
def test_user_token(client: TestClient, test_user: User) -> str:
    """
    Provide a JWT token for regular test user
    """
    response = client.post(
        "/auth/token", data={"username": test_user.username, "password": "testpassword"}
    )
    return response.json()["access_token"]


@pytest.fixture()
def test_admin_token(client: TestClient, test_admin: User) -> str:
    """
    Provide a JWT token for admin test user
    """
    response = client.post(
        "/auth/token", data={"username": test_admin.username, "password": "adminpassword"}
    )
    return response.json()["access_token"]


@pytest.fixture()
def test_document(db_session: Session, test_user: User) -> Document:
    """
    Provide a test document
    """
    document = Document(
        id=uuid.uuid4(),
        title="Test Document",
        filename="test.pdf",
        size_bytes=1024,
        file_path="test/path/test.pdf",
        uploader_id=test_user.id,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture()
def mock_vector_store() -> FAISSStore:
    """
    Provide a mock FAISS vector store
    """
    vector_dimension = 128
    mock_store = FAISSStore(vector_dimension=vector_dimension)
    mock_index = np.random.rand(10, vector_dimension).astype("float32")
    mock_ids = [str(uuid.uuid4()) for _ in range(10)]
    mock_store.add_vectors(mock_index, mock_ids)
    return mock_store


@pytest.fixture()
def mock_pdf_file() -> Generator[str, None, None]:
    """
    Provide a mock PDF file for document upload tests
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(b"%PDF-1.0\n")  # Minimal PDF content
        tmp_file.flush()
        yield tmp_file.name
    os.remove(tmp_file.name)


@pytest.fixture()
def mock_llm_service():
    """
    Provide a mock LLM service for response generation tests
    """
    class MockLLMService:
        def generate_response(self, query, context_documents):
            return "Mock response"

    return MockLLMService()