import json  # standard library
import uuid  # standard library
from typing import Optional  # standard library

import pytest  # pytest 7.0.0+
from fastapi.testclient import TestClient  # fastapi 0.95.0+

from src.backend.app.schemas.query import QueryCreate  # Import QueryCreate schema
from src.backend.app.schemas.feedback import FeedbackCreate, FeedbackFilter  # Import FeedbackCreate and FeedbackFilter schemas
from src.backend.tests.conftest import test_client, test_user, test_admin_user, mock_vector_search_service, mock_llm_service  # Import test fixtures


@pytest.mark.integration
def test_submit_feedback_success(
    client: TestClient,
    test_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests successful feedback submission for a query response.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query to create a query record
    query_data = {"query_text": "test query"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()

    # Extract query_id from the response
    query_id = query_response["query_id"]

    # Create a feedback object with rating=4 and comments
    feedback_data = {"query_id": query_id, "rating": 4, "comments": "test comments"}

    # Send POST request to /api/v1/feedback/ endpoint with the feedback
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )

    # Verify response status code is 201 (Created)
    assert response.status_code == 201

    # Verify response JSON structure matches Feedback schema
    feedback_response = response.json()
    assert "id" in feedback_response
    assert feedback_response["query_id"] == query_id
    assert feedback_response["rating"] == 4
    assert feedback_response["comments"] == "test comments"

    # Verify feedback rating and comments match submitted values
    assert feedback_response["rating"] == feedback_data["rating"]
    assert feedback_response["comments"] == feedback_data["comments"]

    # Verify feedback is associated with the correct query_id
    assert feedback_response["query_id"] == feedback_data["query_id"]


@pytest.mark.integration
def test_submit_feedback_invalid_rating(
    client: TestClient,
    test_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests feedback submission with invalid rating value.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query to create a query record
    query_data = {"query_text": "test query"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()

    # Extract query_id from the response
    query_id = query_response["query_id"]

    # Create a feedback object with invalid rating=6
    feedback_data = {"query_id": query_id, "rating": 6, "comments": "test comments"}

    # Send POST request to /api/v1/feedback/ endpoint with the invalid feedback
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )

    # Verify response status code is 422 (Unprocessable Entity)
    assert response.status_code == 422

    # Verify error message indicates rating must be between 1 and 5
    assert "Rating must be between 1 and 5" in response.text


@pytest.mark.integration
def test_submit_feedback_invalid_query_id(
    client: TestClient,
    test_user: "User",
) -> None:
    """
    Tests feedback submission with non-existent query ID.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
    """
    # Generate a random UUID for a non-existent query
    random_uuid = str(uuid.uuid4())

    # Create a feedback object with rating=3 and the random query_id
    feedback_data = {"query_id": random_uuid, "rating": 3, "comments": "test comments"}

    # Send POST request to /api/v1/feedback/ endpoint with the feedback
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )

    # Verify response status code is 404 (Not Found)
    assert response.status_code == 404

    # Verify error message indicates query not found
    assert "Query not found" in response.text


@pytest.mark.integration
def test_get_feedback_by_id(
    client: TestClient,
    test_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests retrieving a specific feedback by ID.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query to create a query record
    query_data = {"query_text": "test query"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()
    query_id = query_response["query_id"]

    # Submit feedback for the query
    feedback_data = {"query_id": query_id, "rating": 5, "comments": "Excellent response"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )
    assert response.status_code == 201
    feedback_response = response.json()
    feedback_id = feedback_response["id"]

    # Send GET request to /api/v1/feedback/{feedback_id} endpoint
    response = client.get(
        f"/api/v1/feedback/{feedback_id}", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response JSON contains the correct rating and comments
    feedback_get_response = response.json()
    assert feedback_get_response["rating"] == 5
    assert feedback_get_response["comments"] == "Excellent response"

    # Verify feedback_id in response matches the requested ID
    assert feedback_get_response["id"] == feedback_id


@pytest.mark.integration
def test_get_feedback_not_found(
    client: TestClient,
    test_user: "User",
) -> None:
    """
    Tests retrieving a non-existent feedback by ID.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
    """
    # Generate a random UUID for a non-existent feedback
    random_uuid = str(uuid.uuid4())

    # Send GET request to /api/v1/feedback/{random_uuid} endpoint
    response = client.get(
        f"/api/v1/feedback/{random_uuid}", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )

    # Verify response status code is 404 (Not Found)
    assert response.status_code == 404

    # Verify error message indicates feedback not found
    assert "Feedback not found" in response.text


@pytest.mark.integration
def test_get_feedback_by_query(
    client: TestClient,
    test_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests retrieving all feedback for a specific query.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query to create a query record
    query_data = {"query_text": "test query"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()
    query_id = query_response["query_id"]

    # Submit multiple feedback entries for the query with different ratings
    feedback_data1 = {"query_id": query_id, "rating": 1, "comments": "Very poor"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data1,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )
    assert response.status_code == 201

    feedback_data2 = {"query_id": query_id, "rating": 5, "comments": "Excellent"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data2,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )
    assert response.status_code == 201

    # Send GET request to /api/v1/feedback/query/{query_id} endpoint
    response = client.get(
        f"/api/v1/feedback/query/{query_id}", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response is a list of feedback objects
    feedback_list = response.json()
    assert isinstance(feedback_list, list)
    assert len(feedback_list) == 2

    # Verify all feedback in the response is associated with the query_id
    for feedback_item in feedback_list:
        assert feedback_item["query_id"] == query_id

    # Verify the feedback contains the expected rating values
    ratings = [item["rating"] for item in feedback_list]
    assert 1 in ratings
    assert 5 in ratings


@pytest.mark.integration
def test_get_user_feedback(
    client: TestClient,
    test_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests retrieving all feedback submitted by the current user.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit multiple test queries to create query records
    query_data1 = {"query_text": "test query 1"}
    response = client.post(
        "/api/v1/query/", json=query_data1, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response1 = response.json()
    query_id1 = query_response1["query_id"]

    query_data2 = {"query_text": "test query 2"}
    response = client.post(
        "/api/v1/query/", json=query_data2, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response2 = response.json()
    query_id2 = query_response2["query_id"]

    # Submit feedback for each query
    feedback_data1 = {"query_id": query_id1, "rating": 2, "comments": "Poor"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data1,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )
    assert response.status_code == 201

    feedback_data2 = {"query_id": query_id2, "rating": 4, "comments": "Good"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data2,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )
    assert response.status_code == 201

    # Send GET request to /api/v1/feedback/user/me endpoint
    response = client.get(
        "/api/v1/feedback/user/me", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response is a list of feedback objects
    feedback_list = response.json()
    assert isinstance(feedback_list, list)
    assert len(feedback_list) == 2

    # Verify all feedback in the response belongs to the test user
    for feedback_item in feedback_list:
        assert feedback_item["user_id"] == str(test_user.id)

    # Verify the feedback contains the expected rating values
    ratings = [item["rating"] for item in feedback_list]
    assert 2 in ratings
    assert 4 in ratings


@pytest.mark.integration
def test_get_filtered_feedback(
    client: TestClient,
    test_admin_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests retrieving feedback based on filter criteria.

    Args:
        client (TestClient): FastAPI test client.
        test_admin_user (User): Test admin user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query to create a query record
    query_data = {"query_text": "test query"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_admin_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()
    query_id = query_response["query_id"]

    # Submit multiple feedback entries with different ratings
    feedback_data1 = {"query_id": query_id, "rating": 3, "comments": "Neutral"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data1,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )
    assert response.status_code == 201

    feedback_data2 = {"query_id": query_id, "rating": 5, "comments": "Excellent"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data2,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )
    assert response.status_code == 201

    # Create a filter for high ratings (min_rating=4)
    filter_data = {"min_rating": 4}

    # Send POST request to /api/v1/feedback/filter endpoint with the filter
    response = client.post(
        "/api/v1/feedback/filter",
        json=filter_data,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response is a list of feedback objects
    feedback_list = response.json()
    assert isinstance(feedback_list, list)
    assert len(feedback_list) == 1

    # Verify all feedback in the response has rating >= 4
    for feedback_item in feedback_list:
        assert feedback_item["rating"] >= 4

    # Create a filter for specific query_id
    filter_data = {"query_id": query_id}

    # Send POST request to /api/v1/feedback/filter endpoint with the query filter
    response = client.post(
        "/api/v1/feedback/filter",
        json=filter_data,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )

    # Verify all feedback in the response is associated with the specified query_id
    feedback_list = response.json()
    assert isinstance(feedback_list, list)
    assert len(feedback_list) == 2
    for feedback_item in feedback_list:
        assert feedback_item["query_id"] == query_id


@pytest.mark.integration
def test_get_feedback_statistics(
    client: TestClient,
    test_admin_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests retrieving statistics for feedback based on filter criteria.

    Args:
        client (TestClient): FastAPI test client.
        test_admin_user (User): Test admin user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query to create a query record
    query_data = {"query_text": "test query"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_admin_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()
    query_id = query_response["query_id"]

    # Submit multiple feedback entries with different ratings
    feedback_data1 = {"query_id": query_id, "rating": 1, "comments": "Very poor"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data1,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )
    assert response.status_code == 201

    feedback_data2 = {"query_id": query_id, "rating": 3, "comments": "Neutral"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data2,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )
    assert response.status_code == 201

    feedback_data3 = {"query_id": query_id, "rating": 5, "comments": "Excellent"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data3,
        headers={"Authorization": f"Bearer {client.app.test_admin_token}"},
    )
    assert response.status_code == 201

    # Send POST request to /api/v1/feedback/statistics endpoint
    response = client.post(
        "/api/v1/feedback/statistics", headers={"Authorization": f"Bearer {client.app.test_admin_token}"}
    )

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains average_rating, total_feedback, and rating_distribution
    statistics_response = response.json()
    assert "average_rating" in statistics_response
    assert "total_feedback" in statistics_response
    assert "rating_distribution" in statistics_response

    # Verify average_rating is calculated correctly
    assert statistics_response["average_rating"] == 3.0

    # Verify total_feedback matches the number of submitted feedback entries
    assert statistics_response["total_feedback"] == 3

    # Verify rating_distribution contains counts for each rating value
    rating_distribution = statistics_response["rating_distribution"]
    assert rating_distribution["1"] == 1
    assert rating_distribution["3"] == 1
    assert rating_distribution["5"] == 1


@pytest.mark.integration
def test_trigger_reinforcement_learning(
    client: TestClient,
    test_admin_user: "User",
) -> None:
    """
    Tests triggering reinforcement learning based on accumulated feedback.

    Args:
        client (TestClient): FastAPI test client.
        test_admin_user (User): Test admin user object.
    """
    # Send POST request to /api/v1/feedback/reinforce endpoint
    response = client.post(
        "/api/v1/feedback/reinforce", headers={"Authorization": f"Bearer {client.app.test_admin_token}"}
    )

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains status information about the reinforcement learning process
    reinforce_response = response.json()
    assert "status" in reinforce_response
    assert "message" in reinforce_response


@pytest.mark.integration
def test_trigger_reinforcement_learning_unauthorized(
    client: TestClient,
    test_user: "User",
) -> None:
    """
    Tests that non-admin users cannot trigger reinforcement learning.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
    """
    # Send POST request to /api/v1/feedback/reinforce endpoint with regular user
    response = client.post(
        "/api/v1/feedback/reinforce", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )

    # Verify response status code is 403 (Forbidden)
    assert response.status_code == 403

    # Verify error message indicates insufficient permissions
    assert "The user doesn't have enough permissions" in response.text


@pytest.mark.integration
def test_feedback_workflow_end_to_end(
    client: TestClient,
    test_user: "User",
    mock_vector_search_service: "VectorSearchService",
    mock_llm_service: "LLMService",
) -> None:
    """
    Tests the complete feedback workflow from query submission to feedback statistics.

    Args:
        client (TestClient): FastAPI test client.
        test_user (User): Test user object.
        mock_vector_search_service (VectorSearchService): Mock vector search service.
        mock_llm_service (LLMService): Mock LLM service.
    """
    # Submit a test query about document content
    query_data = {"query_text": "test query about document content"}
    response = client.post(
        "/api/v1/query/", json=query_data, headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    query_response = response.json()

    # Verify query response contains AI response
    assert "response_text" in query_response
    assert query_response["response_text"] == "Mock response"

    # Extract query_id from the response
    query_id = query_response["query_id"]

    # Submit positive feedback (rating=5) for the query
    feedback_data = {"query_id": query_id, "rating": 5, "comments": "Very helpful"}
    response = client.post(
        "/api/v1/feedback/",
        json=feedback_data,
        headers={"Authorization": f"Bearer {client.app.test_user_token}"},
    )
    assert response.status_code == 201
    feedback_response = response.json()
    feedback_id = feedback_response["id"]

    # Verify feedback is successfully created
    assert feedback_response["rating"] == 5
    assert feedback_response["comments"] == "Very helpful"

    # Retrieve the feedback by ID
    response = client.get(
        f"/api/v1/feedback/{feedback_id}", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    feedback_get_response = response.json()

    # Verify retrieved feedback matches the submitted feedback
    assert feedback_get_response["rating"] == 5
    assert feedback_get_response["comments"] == "Very helpful"

    # Retrieve all feedback for the query
    response = client.get(
        f"/api/v1/feedback/query/{query_id}", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    feedback_list = response.json()

    # Verify the query's feedback includes the submitted feedback
    assert len(feedback_list) >= 1
    assert any(item["id"] == feedback_id for item in feedback_list)

    # Retrieve all feedback for the user
    response = client.get(
        "/api/v1/feedback/user/me", headers={"Authorization": f"Bearer {client.app.test_user_token}"}
    )
    assert response.status_code == 200
    user_feedback_list = response.json()

    # Verify the user's feedback includes the submitted feedback
    assert len(user_feedback_list) >= 1
    assert any(item["id"] == feedback_id for item in user_feedback_list)

    # Verify the complete workflow functions as expected
    assert True