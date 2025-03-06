import pytest  # pytest 7.0.0+
import uuid  # standard library
from fastapi import status  # fastapi 0.95.0+
from datetime import datetime  # standard library
import httpx  # httpx 0.24.0+

from ..conftest import test_client, test_user, test_admin_user, override_get_current_user, override_get_current_admin_user, test_db  # Internal imports

FEEDBACK_ENDPOINT = "/api/v1/feedback"


def test_submit_feedback(client, test_user):
    """
    Tests submitting feedback for a query
    """
    # Create a test query in the database
    test_query_id = uuid.uuid4()
    test_query_data = {"id": test_query_id, "user_id": test_user.id, "query_text": "test query", "response_text": "test response", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data)

    # Create feedback data with query_id, rating, and comments
    feedback_data = {"query_id": str(test_query_id), "rating": 5, "comments": "Great response!"}

    # Send POST request to feedback endpoint with feedback data
    response = client.post(FEEDBACK_ENDPOINT, json=feedback_data)

    # Assert response status code is 201 (Created)
    assert response.status_code == status.HTTP_201_CREATED

    # Assert response JSON contains expected feedback data
    response_json = response.json()
    assert "id" in response_json
    assert response_json["user_id"] == str(test_user.id)
    assert response_json["query_id"] == str(test_query_id)
    assert response_json["rating"] == 5
    assert response_json["comments"] == "Great response!"


def test_submit_feedback_invalid_query(client, test_user):
    """
    Tests submitting feedback for a non-existent query
    """
    # Create feedback data with non-existent query_id, rating, and comments
    feedback_data = {"query_id": str(uuid.uuid4()), "rating": 5, "comments": "Great response!"}

    # Send POST request to feedback endpoint with feedback data
    response = client.post(FEEDBACK_ENDPOINT, json=feedback_data)

    # Assert response status code is 404 (Not Found)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Assert response JSON contains error detail about query not found
    assert "detail" in response.json()
    assert response.json()["detail"] == "Query not found"


def test_submit_feedback_invalid_rating(client, test_user):
    """
    Tests submitting feedback with an invalid rating value
    """
    # Create a test query in the database
    test_query_id = uuid.uuid4()
    test_query_data = {"id": test_query_id, "user_id": test_user.id, "query_text": "test query", "response_text": "test response", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data)

    # Create feedback data with query_id, invalid rating (6), and comments
    feedback_data = {"query_id": str(test_query_id), "rating": 6, "comments": "Great response!"}

    # Send POST request to feedback endpoint with feedback data
    response = client.post(FEEDBACK_ENDPOINT, json=feedback_data)

    # Assert response status code is 422 (Unprocessable Entity)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Assert response JSON contains validation error about rating
    assert "detail" in response.json()
    assert "rating" in response.json()["detail"][0]["loc"]


def test_get_feedback_by_id(client, test_user, test_db):
    """
    Tests retrieving feedback by ID
    """
    # Create a test query in the database
    test_query_id = uuid.uuid4()
    test_query_data = {"id": test_query_id, "user_id": test_user.id, "query_text": "test query", "response_text": "test response", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data)

    # Create test feedback in the database
    test_feedback_id = uuid.uuid4()
    test_feedback_data = {"id": test_feedback_id, "query_id": test_query_id, "user_id": test_user.id, "rating": 5, "comments": "Great response!", "feedback_time": datetime.now()}
    client.post(FEEDBACK_ENDPOINT, json=test_feedback_data)

    # Send GET request to feedback endpoint with feedback ID
    response = client.get(f"{FEEDBACK_ENDPOINT}/{test_feedback_id}")

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON contains expected feedback data
    response_json = response.json()
    assert response_json["id"] == str(test_feedback_id)
    assert response_json["user_id"] == str(test_user.id)
    assert response_json["query_id"] == str(test_query_id)
    assert response_json["rating"] == 5
    assert response_json["comments"] == "Great response!"


def test_get_feedback_by_id_not_found(client):
    """
    Tests retrieving non-existent feedback by ID
    """
    # Generate a random UUID for non-existent feedback
    non_existent_feedback_id = uuid.uuid4()

    # Send GET request to feedback endpoint with non-existent feedback ID
    response = client.get(f"{FEEDBACK_ENDPOINT}/{non_existent_feedback_id}")

    # Assert response status code is 404 (Not Found)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Assert response JSON contains error detail about feedback not found
    assert "detail" in response.json()
    assert response.json()["detail"] == "Feedback not found"


def test_get_feedback_by_query(client, test_user, test_db):
    """
    Tests retrieving all feedback for a specific query
    """
    # Create a test query in the database
    test_query_id = uuid.uuid4()
    test_query_data = {"id": test_query_id, "user_id": test_user.id, "query_text": "test query", "response_text": "test response", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data)

    # Create multiple test feedback entries for the query
    feedback_data1 = {"query_id": str(test_query_id), "rating": 5, "comments": "Great response!"}
    feedback_data2 = {"query_id": str(test_query_id), "rating": 4, "comments": "Good response."}
    client.post(FEEDBACK_ENDPOINT, json=feedback_data1)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data2)

    # Send GET request to feedback/query/{query_id} endpoint
    response = client.get(f"{FEEDBACK_ENDPOINT}/query/{test_query_id}")

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON is a list with the expected number of feedback items
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 2

    # Assert each feedback item contains expected data
    for feedback_item in response_json:
        assert feedback_item["query_id"] == str(test_query_id)
        assert feedback_item["user_id"] == str(test_user.id)
        assert "rating" in feedback_item
        assert "comments" in feedback_item


def test_get_feedback_by_query_not_found(client):
    """
    Tests retrieving feedback for a non-existent query
    """
    # Generate a random UUID for non-existent query
    non_existent_query_id = uuid.uuid4()

    # Send GET request to feedback/query/{query_id} endpoint with non-existent query ID
    response = client.get(f"{FEEDBACK_ENDPOINT}/query/{non_existent_query_id}")

    # Assert response status code is 404 (Not Found)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Assert response JSON contains error detail about query not found
    assert "detail" in response.json()
    assert response.json()["detail"] == "Query not found"


def test_get_user_feedback(client, test_user, test_db):
    """
    Tests retrieving all feedback submitted by the current user
    """
    # Create test queries in the database
    test_query_id1 = uuid.uuid4()
    test_query_data1 = {"id": test_query_id1, "user_id": test_user.id, "query_text": "test query 1", "response_text": "test response 1", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data1)
    test_query_id2 = uuid.uuid4()
    test_query_data2 = {"id": test_query_id2, "user_id": test_user.id, "query_text": "test query 2", "response_text": "test response 2", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data2)

    # Create multiple test feedback entries by the user
    feedback_data1 = {"query_id": str(test_query_id1), "rating": 5, "comments": "Great response!"}
    feedback_data2 = {"query_id": str(test_query_id2), "rating": 4, "comments": "Good response."}
    client.post(FEEDBACK_ENDPOINT, json=feedback_data1)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data2)

    # Send GET request to feedback/user/me endpoint
    response = client.get(f"{FEEDBACK_ENDPOINT}/user/me")

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON is a list with the expected number of feedback items
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 2

    # Assert each feedback item has user_id matching test_user.id
    for feedback_item in response_json:
        assert feedback_item["user_id"] == str(test_user.id)
        assert "query_id" in feedback_item
        assert "rating" in feedback_item
        assert "comments" in feedback_item


def test_get_filtered_feedback_as_admin(client, test_admin_user, test_db):
    """
    Tests retrieving filtered feedback as admin user
    """
    # Create test queries in the database
    test_query_id1 = uuid.uuid4()
    test_query_data1 = {"id": test_query_id1, "user_id": test_admin_user.id, "query_text": "test query 1", "response_text": "test response 1", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data1)
    test_query_id2 = uuid.uuid4()
    test_query_data2 = {"id": test_query_id2, "user_id": test_admin_user.id, "query_text": "test query 2", "response_text": "test response 2", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data2)

    # Create multiple test feedback entries with different ratings
    feedback_data1 = {"query_id": str(test_query_id1), "rating": 5, "comments": "Great response!"}
    feedback_data2 = {"query_id": str(test_query_id2), "rating": 3, "comments": "Okay response."}
    client.post(FEEDBACK_ENDPOINT, json=feedback_data1)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data2)

    # Create filter criteria (min_rating=4)
    filter_data = {"min_rating": 4}

    # Send POST request to feedback/filter endpoint with filter criteria
    response = client.post(f"{FEEDBACK_ENDPOINT}/filter", json=filter_data)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON is a list containing only feedback with rating >= 4
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 1
    assert response_json[0]["rating"] >= 4

    # Assert each feedback item contains expected data
    for feedback_item in response_json:
        assert "query_id" in feedback_item
        assert "user_id" in feedback_item
        assert "rating" in feedback_item
        assert "comments" in feedback_item


def test_get_filtered_feedback_as_regular_user(client, test_user, test_db):
    """
    Tests retrieving filtered feedback as regular user (should only see own feedback)
    """
    # Create test queries in the database
    test_query_id1 = uuid.uuid4()
    test_query_data1 = {"id": test_query_id1, "user_id": test_user.id, "query_text": "test query 1", "response_text": "test response 1", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data1)
    test_query_id2 = uuid.uuid4()
    test_query_data2 = {"id": test_query_id2, "user_id": test_user.id, "query_text": "test query 2", "response_text": "test response 2", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data2)

    # Create test feedback entries by test_user
    feedback_data1 = {"query_id": str(test_query_id1), "rating": 5, "comments": "Great response!"}
    feedback_data2 = {"query_id": str(test_query_id2), "rating": 3, "comments": "Okay response."}
    client.post(FEEDBACK_ENDPOINT, json=feedback_data1)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data2)

    # Create test feedback entries by another user
    another_user_id = uuid.uuid4()
    feedback_data3 = {"query_id": str(test_query_id1), "rating": 2, "comments": "Bad response."}
    # Send POST request to feedback endpoint with feedback data
    response = client.post(FEEDBACK_ENDPOINT, json=feedback_data3)

    # Create filter criteria (min_rating=3)
    filter_data = {"min_rating": 3}

    # Send POST request to feedback/filter endpoint with filter criteria
    response = client.post(f"{FEEDBACK_ENDPOINT}/filter", json=filter_data)

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON is a list containing only feedback by test_user with rating >= 3
    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == 2
    for feedback_item in response_json:
        assert feedback_item["user_id"] == str(test_user.id)
        assert feedback_item["rating"] >= 3

    # Assert no feedback from other users is included in the response
    for feedback_item in response_json:
        assert feedback_item["user_id"] != str(another_user_id)


def test_get_feedback_statistics_as_admin(client, test_admin_user, test_db):
    """
    Tests retrieving feedback statistics as admin user
    """
    # Create test queries in the database
    test_query_id1 = uuid.uuid4()
    test_query_data1 = {"id": test_query_id1, "user_id": test_admin_user.id, "query_text": "test query 1", "response_text": "test response 1", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data1)
    test_query_id2 = uuid.uuid4()
    test_query_data2 = {"id": test_query_id2, "user_id": test_admin_user.id, "query_text": "test query 2", "response_text": "test response 2", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data2)

    # Create multiple test feedback entries with different ratings
    feedback_data1 = {"query_id": str(test_query_id1), "rating": 5, "comments": "Great response!"}
    feedback_data2 = {"query_id": str(test_query_id2), "rating": 3, "comments": "Okay response."}
    feedback_data3 = {"query_id": str(test_query_id1), "rating": 4, "comments": "Good response."}
    client.post(FEEDBACK_ENDPOINT, json=feedback_data1)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data2)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data3)

    # Send POST request to feedback/statistics endpoint
    response = client.post(f"{FEEDBACK_ENDPOINT}/statistics")

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON contains average_rating field with expected value
    response_json = response.json()
    assert "average_rating" in response_json
    assert response_json["average_rating"] == 4.0

    # Assert response JSON contains total_feedback field with expected count
    assert "total_feedback" in response_json
    assert response_json["total_feedback"] == 3

    # Assert response JSON contains rating_distribution with counts for each rating value
    assert "rating_distribution" in response_json
    assert response_json["rating_distribution"] == {1: 0, 2: 0, 3: 1, 4: 1, 5: 1}


def test_get_feedback_statistics_as_regular_user(client, test_user, test_db):
    """
    Tests retrieving feedback statistics as regular user (should only see own feedback stats)
    """
    # Create test queries in the database
    test_query_id1 = uuid.uuid4()
    test_query_data1 = {"id": test_query_id1, "user_id": test_user.id, "query_text": "test query 1", "response_text": "test response 1", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data1)
    test_query_id2 = uuid.uuid4()
    test_query_data2 = {"id": test_query_id2, "user_id": test_user.id, "query_text": "test query 2", "response_text": "test response 2", "context_documents": {}}
    client.post("/api/v1/query", json=test_query_data2)

    # Create test feedback entries by test_user
    feedback_data1 = {"query_id": str(test_query_id1), "rating": 5, "comments": "Great response!"}
    feedback_data2 = {"query_id": str(test_query_id2), "rating": 3, "comments": "Okay response."}
    client.post(FEEDBACK_ENDPOINT, json=feedback_data1)
    client.post(FEEDBACK_ENDPOINT, json=feedback_data2)

    # Create test feedback entries by another user
    another_user_id = uuid.uuid4()
    feedback_data3 = {"query_id": str(test_query_id1), "rating": 2, "comments": "Bad response."}
    # Send POST request to feedback endpoint with feedback data
    response = client.post(FEEDBACK_ENDPOINT, json=feedback_data3)

    # Send POST request to feedback/statistics endpoint
    response = client.post(f"{FEEDBACK_ENDPOINT}/statistics")

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON contains statistics only for test_user's feedback
    response_json = response.json()
    assert "average_rating" in response_json
    assert response_json["average_rating"] == 4.0
    assert "total_feedback" in response_json
    assert response_json["total_feedback"] == 2
    assert "rating_distribution" in response_json
    assert response_json["rating_distribution"] == {1: 0, 2: 0, 3: 1, 4: 0, 5: 1}


def test_trigger_reinforcement_learning_as_admin(client, test_admin_user):
    """
    Tests triggering reinforcement learning as admin user
    """
    # Send POST request to feedback/reinforce endpoint
    response = client.post(f"{FEEDBACK_ENDPOINT}/reinforce")

    # Assert response status code is 200 (OK)
    assert response.status_code == status.HTTP_200_OK

    # Assert response JSON contains success status
    response_json = response.json()
    assert "status" in response_json
    assert response_json["status"] == "skipped"

    # Assert response JSON contains message about reinforcement learning process
    assert "message" in response_json
    assert "Reinforcement learning process" in response_json["message"]


def test_trigger_reinforcement_learning_as_regular_user(client, test_user):
    """
    Tests triggering reinforcement learning as regular user (should be forbidden)
    """
    # Send POST request to feedback/reinforce endpoint
    response = client.post(f"{FEEDBACK_ENDPOINT}/reinforce")

    # Assert response status code is 403 (Forbidden)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Assert response JSON contains error detail about insufficient permissions
    assert "detail" in response.json()
    assert "The user doesn't have enough permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_submit_feedback_async(async_client, test_user):
    """
    Tests submitting feedback using the async endpoint
    """
    # Create a test query in the database
    test_query_id = uuid.uuid4()
    test_query_data = {"id": test_query_id, "user_id": test_user.id, "query_text": "test query", "response_text": "test response", "context_documents": {}}
    response = await async_client.post("/api/v1/query", json=test_query_data)

    # Create feedback data with query_id, rating, and comments
    feedback_data = {"query_id": str(test_query_id), "rating": 5, "comments": "Great response!"}

    # Send POST request to feedback/async endpoint with feedback data
    response = await async_client.post(f"{FEEDBACK_ENDPOINT}/async", json=feedback_data)

    # Assert response status code is 201 (Created)
    assert response.status_code == status.HTTP_201_CREATED

    # Assert response JSON contains expected feedback data
    response_json = response.json()
    assert "id" in response_json
    assert response_json["user_id"] == str(test_user.id)
    assert response_json["query_id"] == str(test_query_id)