# Standard library imports
import json
import uuid
from typing import Optional

# Third-party library imports
import pytest  # pytest version: latest
from pytest import mark
from typing import List

# Internal module imports
from ...conftest import test_client, test_user, mock_vector_search_service, mock_llm_service  # Assuming these fixtures are defined in conftest.py
from ....app.schemas.query import QueryCreate, QueryResponse  # Assuming QueryCreate and QueryResponse are defined here
from ....app.schemas.document_chunk import DocumentChunkWithSimilarity


# Define test query text and mock response text as global constants
TEST_QUERY_TEXT = "What is vector search?"
MOCK_RESPONSE_TEXT = "Vector search is a technique that uses vector embeddings to find similar documents."

@pytest.mark.parametrize("max_results,similarity_threshold", [(None, None), (5, None), (None, 0.7), (5, 0.7)])
def test_submit_query_success(
    test_client,
    test_user,
    mock_vector_search_service,
    mock_llm_service,
    max_results: Optional[int],
    similarity_threshold: Optional[float]
):
    """
    Tests successful query submission and response generation.

    Configures mock_vector_search_service.search to return sample search results.
    Configures mock_llm_service.create_query_response to return a sample response.
    Creates a query request with test query text and optional parameters.
    Sends POST request to /query/ endpoint.
    Verifies response status code is 200.
    Verifies response JSON contains expected fields (query_id, query_text, response_text, relevant_documents).
    Verifies query_text matches the submitted query.
    Verifies response_text contains the expected mock response.
    Verifies relevant_documents contains the expected search results.
    """
    # Arrange
    mock_vector_search_service.search.return_value = [
        DocumentChunkWithSimilarity(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content="Sample document content",
            similarity_score=0.8,
            chunk_index=0
        )
    ]
    mock_llm_service.create_query_response.return_value = QueryResponse(
        query_id=uuid.uuid4(),
        query_text=TEST_QUERY_TEXT,
        response_text=MOCK_RESPONSE_TEXT,
        relevant_documents=mock_vector_search_service.search.return_value
    )

    query_create = QueryCreate(
        query_text=TEST_QUERY_TEXT,
        max_results=max_results,
        similarity_threshold=similarity_threshold
    )

    # Act
    response = test_client.post(
        "/query/",
        json=query_create.model_dump()
    )

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert "query_id" in response_json
    assert response_json["query_text"] == TEST_QUERY_TEXT
    assert response_json["response_text"] == MOCK_RESPONSE_TEXT
    assert "relevant_documents" in response_json
    assert len(response_json["relevant_documents"]) == 1
    assert response_json["relevant_documents"][0]["content"] == "Sample document content"

def test_submit_query_empty_text(test_client):
    """
    Tests query submission with empty query text.

    Creates a query request with empty query text.
    Sends POST request to /query/ endpoint.
    Verifies response status code is 422 (Unprocessable Entity).
    Verifies response contains validation error for query_text.
    """
    # Arrange
    query_create = QueryCreate(query_text="")

    # Act
    response = test_client.post(
        "/query/",
        json=query_create.model_dump()
    )

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "query_text" in response.json()["detail"][0]["loc"]

@pytest.mark.parametrize(
    "max_results,similarity_threshold,expected_status",
    [
        (0, None, 422),
        (None, -0.1, 422),
        (0, -0.1, 422)
    ]
)
def test_submit_query_invalid_parameters(
    test_client,
    max_results: Optional[int],
    similarity_threshold: Optional[float],
    expected_status: int
):
    """
    Tests query submission with invalid parameters.

    Creates a query request with test query text and invalid parameters.
    Sends POST request to /query/ endpoint.
    Verifies response status code matches expected status code.
    Verifies response contains validation errors for the invalid parameters.
    """
    # Arrange
    query_create = QueryCreate(
        query_text=TEST_QUERY_TEXT,
        max_results=max_results,
        similarity_threshold=similarity_threshold
    )

    # Act
    response = test_client.post(
        "/query/",
        json=query_create.model_dump()
    )

    # Assert
    assert response.status_code == expected_status
    assert "detail" in response.json()

def test_get_query_success(test_client, test_user, db_session):
    """
    Tests successful retrieval of a specific query by ID.

    Creates a test query in the database.
    Sends GET request to /query/{query_id} endpoint.
    Verifies response status code is 200.
    Verifies response JSON contains expected fields (id, query_text, response_text).
    Verifies query data matches the test query.
    """
    # Arrange
    from ....app.models.query import Query
    from ....app.schemas.query import QueryCreate
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)
    query = Query(
        id=uuid.uuid4(),
        user_id=test_user.id,
        query_text=query_create.query_text,
        response_text=MOCK_RESPONSE_TEXT,
        context_documents={}
    )
    db_session.add(query)
    db_session.commit()
    db_session.refresh(query)

    # Act
    response = test_client.get(f"/query/{query.id}")

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == str(query.id)
    assert response_json["query_text"] == TEST_QUERY_TEXT
    assert response_json["response_text"] == MOCK_RESPONSE_TEXT

def test_get_query_not_found(test_client):
    """
    Tests retrieval of a non-existent query.

    Generates a random UUID for a non-existent query.
    Sends GET request to /query/{query_id} endpoint.
    Verifies response status code is 404 (Not Found).
    Verifies response contains error message about query not found.
    """
    # Arrange
    query_id = uuid.uuid4()

    # Act
    response = test_client.get(f"/query/{query_id}")

    # Assert
    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Query not found"

def test_get_query_unauthorized(test_client, db_session, test_user, test_admin):
    """
    Tests retrieval of a query by an unauthorized user.

    Creates a test query in the database owned by test_admin_user.
    Configures test_client to use test_user (not the owner).
    Sends GET request to /query/{query_id} endpoint.
    Verifies response status code is 403 (Forbidden).
    Verifies response contains error message about permission denied.
    """
    # Arrange
    from ....app.models.query import Query
    from ....app.schemas.query import QueryCreate
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)
    query = Query(
        id=uuid.uuid4(),
        user_id=test_admin.id,
        query_text=query_create.query_text,
        response_text=MOCK_RESPONSE_TEXT,
        context_documents={}
    )
    db_session.add(query)
    db_session.commit()
    db_session.refresh(query)

    # Act
    response = test_client.get(f"/query/{query.id}")

    # Assert
    assert response.status_code == 403
    assert "detail" in response.json()
    assert response.json()["detail"] == "You don't have permission to access this query"

@pytest.mark.parametrize(
    "skip,limit,expected_count",
    [
        (None, None, 3),
        (0, 2, 2),
        (1, 1, 1)
    ]
)
def test_list_queries(test_client, db_session, test_user, skip, limit, expected_count):
    """
    Tests listing of queries with pagination and filtering.

    Creates multiple test queries in the database.
    Sends GET request to /query/ endpoint with pagination parameters.
    Verifies response status code is 200.
    Verifies response JSON contains a list of queries.
    Verifies the number of queries matches the expected count based on pagination.
    """
    # Arrange
    from ....app.models.query import Query
    from ....app.schemas.query import QueryCreate
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)
    for i in range(3):
        query = Query(
            id=uuid.uuid4(),
            user_id=test_user.id,
            query_text=query_create.query_text,
            response_text=MOCK_RESPONSE_TEXT,
            context_documents={}
        )
        db_session.add(query)
    db_session.commit()

    # Act
    params = {}
    if skip is not None:
        params["skip"] = skip
    if limit is not None:
        params["limit"] = limit
    response = test_client.get("/query/", params=params)

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == expected_count

def test_list_user_queries(test_client, db_session, test_user, test_admin):
    """
    Tests listing of queries for the current user.

    Creates test queries in the database for both test_user and test_admin_user.
    Configures test_client to use test_user.
    Sends GET request to /query/me endpoint.
    Verifies response status code is 200.
    Verifies response JSON contains only queries owned by test_user.
    Verifies no queries from test_admin_user are included.
    """
    # Arrange
    from ....app.models.query import Query
    from ....app.schemas.query import QueryCreate
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)
    query1 = Query(
        id=uuid.uuid4(),
        user_id=test_user.id,
        query_text=query_create.query_text,
        response_text=MOCK_RESPONSE_TEXT,
        context_documents={}
    )
    query2 = Query(
        id=uuid.uuid4(),
        user_id=test_admin.id,
        query_text=query_create.query_text,
        response_text=MOCK_RESPONSE_TEXT,
        context_documents={}
    )
    db_session.add(query1)
    db_session.add(query2)
    db_session.commit()

    # Act
    response = test_client.get("/query/me")

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 1
    assert response_json[0]["user_id"] == str(test_user.id)

def test_get_query_with_feedback(test_client, db_session, test_user):
    """
    Tests retrieval of a query with its feedback.

    Creates a test query in the database.
    Adds test feedback for the query.
    Sends GET request to /query/{query_id}/feedback endpoint.
    Verifies response status code is 200.
    Verifies response JSON contains the query data with feedback.
    Verifies feedback data matches the test feedback.
    """
    # Arrange
    from ....app.models.query import Query
    from ....app.models.feedback import Feedback
    from ....app.schemas.query import QueryCreate
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)
    query = Query(
        id=uuid.uuid4(),
        user_id=test_user.id,
        query_text=query_create.query_text,
        response_text=MOCK_RESPONSE_TEXT,
        context_documents={}
    )
    db_session.add(query)
    feedback_item = Feedback(
        id=uuid.uuid4(),
        query_id=query.id,
        user_id=test_user.id,
        rating=5,
        comments="Great response!"
    )
    db_session.add(feedback_item)
    db_session.commit()
    db_session.refresh(query)

    # Act
    response = test_client.get(f"/query/{query.id}/feedback")

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == str(query.id)
    assert "feedback" in response_json
    assert len(response_json["feedback"]) == 1
    assert response_json["feedback"][0]["rating"] == 5
    assert response_json["feedback"][0]["comments"] == "Great response!"

def test_search_with_vector_search_error(test_client, mock_vector_search_service):
    """
    Tests error handling when vector search service fails.

    Configures mock_vector_search_service.search to raise an exception.
    Creates a query request with test query text.
    Sends POST request to /query/ endpoint.
    Verifies response status code is 500 (Internal Server Error).
    Verifies response contains error message about search failure.
    """
    # Arrange
    mock_vector_search_service.search.side_effect = Exception("Vector search failed")
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)

    # Act
    response = test_client.post(
        "/query/",
        json=query_create.model_dump()
    )

    # Assert
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "search failed" in response.json()["detail"].lower()

def test_search_with_llm_error(test_client, mock_vector_search_service, mock_llm_service):
    """
    Tests error handling when LLM service fails.

    Configures mock_vector_search_service.search to return sample search results.
    Configures mock_llm_service.create_query_response to raise an exception.
    Creates a query request with test query text.
    Sends POST request to /query/ endpoint.
    Verifies response status code is 500 (Internal Server Error).
    Verifies response contains error message about response generation failure.
    """
    # Arrange
    mock_vector_search_service.search.return_value = [
        DocumentChunkWithSimilarity(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content="Sample document content",
            similarity_score=0.8,
            chunk_index=0
        )
    ]
    mock_llm_service.create_query_response.side_effect = Exception("LLM response generation failed")
    query_create = QueryCreate(query_text=TEST_QUERY_TEXT)

    # Act
    response = test_client.post(
        "/query/",
        json=query_create.model_dump()
    )

    # Assert
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "response generation failed" in response.json()["detail"].lower()