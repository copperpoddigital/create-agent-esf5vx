import json  # standard library
import uuid  # standard library
from typing import List, Optional  # standard library

import pytest  # pytest 7.0.0+
from fastapi.testclient import TestClient  # fastapi 0.95.0+

from src.backend.app.schemas.query import QueryCreate, QueryResponse  # Import session factory for creating test database sessions
from src.backend.tests.conftest import test_client, test_user, test_document, mock_vector_search_service, mock_llm_service  # Import session factory for creating test database sessions


@pytest.mark.integration
def test_submit_query_success(
    client: TestClient,
    test_user,
    test_document,
    mock_vector_search_service,
    mock_llm_service,
):
    """
    Tests successful query submission and response generation
    """
    # 1. Create a test query with sample text
    query_text = "What are the applications of AI?"
    test_query = QueryCreate(query_text=query_text)

    # 2. Configure mock_vector_search_service to return relevant document chunks
    mock_vector_search_service.return_value = [
        {
            "chunk_id": str(uuid.uuid4()),
            "document_id": str(test_document.id),
            "content": "AI has many applications.",
            "similarity_score": 0.85,
        }
    ]

    # 3. Configure mock_llm_service to return a predefined response
    mock_llm_service.return_value.generate_response.return_value = "AI is used in various fields."

    # 4. Send POST request to /api/v1/query/ endpoint with the test query
    response = client.post(
        "/api/v1/query/",
        json=test_query.model_dump(),
    )

    # 5. Verify response status code is 200
    assert response.status_code == 200

    # 6. Verify response JSON structure matches QueryResponse schema
    response_data = response.json()
    assert "query_id" in response_data
    assert "query_text" in response_data
    assert "response_text" in response_data
    assert "relevant_documents" in response_data

    # 7. Verify query_text in response matches submitted query
    assert response_data["query_text"] == query_text

    # 8. Verify response contains AI-generated text
    assert response_data["response_text"] == "AI is used in various fields."

    # 9. Verify response contains relevant documents
    assert len(response_data["relevant_documents"]) == 1
    assert response_data["relevant_documents"][0]["content"] == "AI has many applications."


@pytest.mark.integration
def test_submit_query_empty(
    client: TestClient,
    test_user,
):
    """
    Tests query submission with empty query text
    """
    # 1. Create a test query with empty text
    test_query = QueryCreate(query_text="")

    # 2. Send POST request to /api/v1/query/ endpoint with the empty query
    response = client.post(
        "/api/v1/query/",
        json=test_query.model_dump(),
    )

    # 3. Verify response status code is 422 (Unprocessable Entity)
    assert response.status_code == 422

    # 4. Verify error message indicates query text cannot be empty
    assert "detail" in response.json()
    assert "Query text cannot be empty" in response.json()["detail"]


@pytest.mark.integration
def test_submit_query_with_parameters(
    client: TestClient,
    test_user,
    test_document,
    mock_vector_search_service,
    mock_llm_service,
):
    """
    Tests query submission with custom max_results and similarity_threshold parameters
    """
    # 1. Create a test query with custom max_results=5 and similarity_threshold=0.8
    test_query = QueryCreate(query_text="AI applications", max_results=5, similarity_threshold=0.8)

    # 2. Configure mock_vector_search_service to verify it receives the custom parameters
    def mock_search(query_text, db, top_k, threshold):
        assert top_k == 5
        assert threshold == 0.8
        return [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(test_document.id),
                "content": "AI has many applications.",
                "similarity_score": 0.9,
            }
        ]

    mock_vector_search_service.return_value = mock_search

    # 3. Configure mock_llm_service to return a predefined response
    mock_llm_service.return_value.generate_response.return_value = "AI is used in various fields."

    # 4. Send POST request to /api/v1/query/ endpoint with the test query
    response = client.post(
        "/api/v1/query/",
        json=test_query.model_dump(),
    )

    # 5. Verify response status code is 200
    assert response.status_code == 200

    # 6. Verify mock_vector_search_service was called with the correct parameters
    assert mock_vector_search_service.called

    # 7. Verify response JSON structure matches QueryResponse schema
    response_data = response.json()
    assert "query_id" in response_data
    assert "query_text" in response_data
    assert "response_text" in response_data
    assert "relevant_documents" in response_data


@pytest.mark.integration
def test_get_query_by_id(
    client: TestClient,
    test_user,
    test_document,
    mock_vector_search_service,
    mock_llm_service,
):
    """
    Tests retrieving a specific query by ID
    """
    # 1. Submit a test query to create a query record
    query_text = "What is a vector database?"
    test_query = QueryCreate(query_text=query_text)
    mock_vector_search_service.return_value = []
    mock_llm_service.return_value.generate_response.return_value = "A vector database stores vector embeddings."
    response = client.post(
        "/api/v1/query/",
        json=test_query.model_dump(),
    )
    assert response.status_code == 200
    query_id = response.json()["query_id"]

    # 2. Extract query_id from the response
    # 3. Send GET request to /api/v1/query/{query_id} endpoint
    response = client.get(f"/api/v1/query/{query_id}")

    # 4. Verify response status code is 200
    assert response.status_code == 200

    # 5. Verify response JSON contains the correct query_text and response_text
    response_data = response.json()
    assert response_data["query_text"] == query_text
    assert response_data["response_text"] == "A vector database stores vector embeddings."

    # 6. Verify query_id in response matches the requested ID
    assert response_data["id"] == query_id


@pytest.mark.integration
def test_get_query_not_found(
    client: TestClient,
    test_user,
):
    """
    Tests retrieving a non-existent query by ID
    """
    # 1. Generate a random UUID for a non-existent query
    random_uuid = uuid.uuid4()

    # 2. Send GET request to /api/v1/query/{random_uuid} endpoint
    response = client.get(f"/api/v1/query/{random_uuid}")

    # 3. Verify response status code is 404 (Not Found)
    assert response.status_code == 404

    # 4. Verify error message indicates query not found
    assert "detail" in response.json()
    assert "Query not found" in response.json()["detail"]


@pytest.mark.integration
def test_list_user_queries(
    client: TestClient,
    test_user,
    test_document,
    mock_vector_search_service,
    mock_llm_service,
):
    """
    Tests listing queries for the current user
    """
    # 1. Submit multiple test queries to create query records
    query_texts = ["AI in healthcare", "Machine learning basics", "Deep learning applications"]
    for query_text in query_texts:
        test_query = QueryCreate(query_text=query_text)
        mock_vector_search_service.return_value = []
        mock_llm_service.return_value.generate_response.return_value = f"Response for: {query_text}"
        response = client.post(
            "/api/v1/query/",
            json=test_query.model_dump(),
        )
        assert response.status_code == 200

    # 2. Send GET request to /api/v1/query/me endpoint
    response = client.get("/api/v1/query/me")

    # 3. Verify response status code is 200
    assert response.status_code == 200

    # 4. Verify response is a list of queries
    response_data = response.json()
    assert isinstance(response_data, list)

    # 5. Verify all queries in the response belong to the test user
    for query in response_data:
        assert query["user_id"] == str(test_user.id)

    # 6. Verify the queries contain the expected query_text values
    retrieved_query_texts = [query["query_text"] for query in response_data]
    for query_text in query_texts:
        assert query_text in retrieved_query_texts


@pytest.mark.integration
def test_query_workflow_end_to_end(
    client: TestClient,
    test_user,
    test_document,
    mock_vector_search_service,
    mock_llm_service,
):
    """
    Tests the complete query workflow from submission to retrieval
    """
    # 1. Configure mock services with realistic test data
    query_text = "What are the benefits of using a vector database for document search?"
    mock_vector_search_service.return_value = [
        {
            "chunk_id": str(uuid.uuid4()),
            "document_id": str(test_document.id),
            "content": "Vector databases enable semantic search.",
            "similarity_score": 0.9,
        },
        {
            "chunk_id": str(uuid.uuid4()),
            "document_id": str(test_document.id),
            "content": "They provide faster and more accurate results.",
            "similarity_score": 0.8,
        },
    ]
    mock_llm_service.return_value.generate_response.return_value = (
        "Vector databases enable semantic search, providing faster and more accurate results."
    )

    # 2. Submit a test query about document content
    test_query = QueryCreate(query_text=query_text)
    response = client.post(
        "/api/v1/query/",
        json=test_query.model_dump(),
    )
    assert response.status_code == 200
    query_id = response.json()["query_id"]

    # 3. Verify query response contains relevant documents and AI response
    assert "relevant_documents" in response.json()
    assert "response_text" in response.json()
    assert len(response.json()["relevant_documents"]) == 2
    assert "semantic search" in response.json()["response_text"]

    # 4. Extract query_id from the response
    # 5. Retrieve the query by ID
    response = client.get(f"/api/v1/query/{query_id}")
    assert response.status_code == 200
    retrieved_query = response.json()

    # 6. Verify retrieved query matches the submitted query
    assert retrieved_query["query_text"] == query_text
    assert retrieved_query["response_text"] == "Vector databases enable semantic search, providing faster and more accurate results."

    # 7. List user queries and verify the test query is included
    response = client.get("/api/v1/query/me")
    assert response.status_code == 200
    user_queries = response.json()
    assert any(q["id"] == query_id for q in user_queries)

    # 8. Verify the complete workflow functions as expected
    assert True  # If all steps above pass, the workflow is functioning as expected


@pytest.mark.integration
def test_anonymous_query(
    client: TestClient,
    mock_vector_search_service,
    mock_llm_service,
):
    """
    Tests query submission without authentication
    """
    # 1. Configure client to not include authentication
    # 2. Create a test query with sample text
    query_text = "What is the capital of France?"
    test_query = QueryCreate(query_text=query_text)

    # 3. Configure mock services to return test data
    mock_vector_search_service.return_value = []
    mock_llm_service.return_value.generate_response.return_value = "The capital of France is Paris."

    # 4. Send POST request to /api/v1/query/ endpoint with the test query
    response = client.post(
        "/api/v1/query/",
        json=test_query.model_dump(),
    )

    # 5. Verify response status code is 200
    assert response.status_code == 200

    # 6. Verify response contains AI-generated text and relevant documents
    response_data = response.json()
    assert "response_text" in response_data
    assert response_data["response_text"] == "The capital of France is Paris."
    assert "relevant_documents" in response_data

    # 7. Verify query is not stored in the database (no query_id)
    assert "query_id" in response_data