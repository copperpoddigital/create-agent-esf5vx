import os  # File system operations for test file handling
import uuid  # Generate and handle UUIDs for document IDs
import json  # Parse JSON responses from API endpoints
from typing import TYPE_CHECKING  # Type hints for test functions
from unittest import mock  # Mock objects for isolating components in tests

import pytest  # Testing framework for writing and running tests

from ...conftest import test_client, test_user, test_admin_user, test_document, sample_pdf_path  # Import test client fixture for API testing
from ...conftest import test_client, test_user, test_admin_user, test_document, sample_pdf_path  # Import test user fixture for authentication
from ...conftest import test_client, test_user, test_admin_user, test_document, sample_pdf_path  # Import test admin user fixture for admin operations
from ...conftest import test_client, test_user, test_admin_user, test_document, sample_pdf_path  # Import test document fixture for document operations
from ...conftest import test_client, test_user, test_admin_user, test_document, sample_pdf_path  # Import sample PDF path fixture for document upload testing
from '../../../app/models/document' import DocumentStatus  # Import document status enum for test assertions

if TYPE_CHECKING:
    from fastapi.testclient import TestClient  # fastapi 0.95.0+


def test_create_document(client: "TestClient", sample_pdf_path: str) -> None:
    """
    Tests the document upload endpoint
    """
    # Open the sample PDF file
    with open(sample_pdf_path, "rb") as f:
        # Create a file object for upload
        files = {"file": f}
        # Send a POST request to the /documents/ endpoint with the file
        response = client.post("/documents/", files=files)

    # Assert that the response status code is 201 (Created)
    assert response.status_code == 201
    # Assert that the response JSON contains expected fields (id, title, filename, etc.)
    response_json = response.json()
    assert "id" in response_json
    assert "title" in response_json
    assert "filename" in response_json
    assert "size_bytes" in response_json
    assert "upload_date" in response_json
    assert "status" in response_json
    # Assert that the document status is 'processing'
    assert response_json["status"] == "processing"


def test_create_document_invalid_file(client: "TestClient") -> None:
    """
    Tests the document upload endpoint with an invalid file
    """
    # Create a non-PDF file object for upload
    files = {"file": ("invalid.txt", b"This is not a PDF", "text/plain")}
    # Send a POST request to the /documents/ endpoint with the invalid file
    response = client.post("/documents/", files=files)

    # Assert that the response status code is 400 (Bad Request)
    assert response.status_code == 400
    # Assert that the response JSON contains an error message about invalid file type
    response_json = response.json()
    assert "detail" in response_json
    assert "Only PDF files are supported" in response_json["detail"]


def test_get_documents(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests the document listing endpoint
    """
    # Send a GET request to the /documents/ endpoint
    response = client.get("/documents/")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON contains expected fields (items, total, etc.)
    response_json = response.json()
    assert "items" in response_json
    assert "total" in response_json
    assert "skip" in response_json
    assert "limit" in response_json
    # Assert that the test document is in the returned items list
    items = response_json["items"]
    assert len(items) > 0
    document_data = items[0]
    # Assert that the document data matches expected values
    assert document_data["id"] == str(test_document.id)
    assert document_data["title"] == test_document.title
    assert document_data["filename"] == test_document.filename
    assert document_data["size_bytes"] == test_document.size_bytes
    assert document_data["status"] == test_document.status.value


def test_get_documents_with_filter(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests the document listing endpoint with filtering
    """
    # Send a GET request to the /documents/ endpoint with filter parameters
    response = client.get(f"/documents/?title={test_document.title}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the filtered results contain only matching documents
    response_json = response.json()
    items = response_json["items"]
    assert len(items) > 0
    for item in items:
        assert test_document.title in item["title"]

    # Test with various filter combinations (title, status, uploader_id, etc.)
    response = client.get(f"/documents/?status={test_document.status.value}")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    for item in items:
        assert item["status"] == test_document.status.value


def test_get_document(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests the document retrieval endpoint
    """
    # Send a GET request to the /documents/{document_id} endpoint
    response = client.get(f"/documents/{test_document.id}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON contains expected document data
    response_json = response.json()
    assert response_json["id"] == str(test_document.id)
    assert response_json["title"] == test_document.title
    assert response_json["filename"] == test_document.filename
    assert response_json["size_bytes"] == test_document.size_bytes
    assert response_json["status"] == test_document.status.value
    # Assert that the document ID matches the test document ID
    assert response_json["id"] == str(test_document.id)


def test_get_document_not_found(client: "TestClient") -> None:
    """
    Tests the document retrieval endpoint with a non-existent document ID
    """
    # Generate a random UUID for a non-existent document
    non_existent_id = uuid.uuid4()
    # Send a GET request to the /documents/{document_id} endpoint
    response = client.get(f"/documents/{non_existent_id}")

    # Assert that the response status code is 404 (Not Found)
    assert response.status_code == 404
    # Assert that the response JSON contains an error message
    response_json = response.json()
    assert "detail" in response_json
    assert "Document not found" in response_json["detail"]


def test_get_document_with_chunks(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests the document retrieval endpoint with chunks
    """
    # Send a GET request to the /documents/{document_id}/chunks endpoint
    response = client.get(f"/documents/{test_document.id}/chunks")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON contains document data with chunks array
    response_json = response.json()
    assert "id" in response_json
    assert "title" in response_json
    assert "filename" in response_json
    assert "size_bytes" in response_json
    assert "status" in response_json
    assert "chunks" in response_json
    # Assert that the document ID matches the test document ID
    assert response_json["id"] == str(test_document.id)


def test_download_document(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests the document download endpoint
    """
    # Mock the file_storage.retrieve_document method to return test content
    with mock.patch("src.backend.app.services.file_storage.FileStorage.retrieve_document") as mock_retrieve:
        mock_retrieve.return_value = b"Test file content"
        # Send a GET request to the /documents/{document_id}/download endpoint
        response = client.get(f"/documents/{test_document.id}/download")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response content matches the expected file content
    assert response.content == b"Test file content"
    # Assert that the response headers contain the correct content type
    assert response.headers["content-type"] == "application/pdf"


def test_delete_document(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests the document deletion endpoint
    """
    # Send a DELETE request to the /documents/{document_id} endpoint
    response = client.delete(f"/documents/{test_document.id}")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON contains a success message
    response_json = response.json()
    assert "message" in response_json
    assert "Document deleted successfully" in response_json["message"]

    # Send a GET request to verify the document status is now 'deleted'
    response = client.get(f"/documents/{test_document.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_hard_delete_document(client: "TestClient", test_document: "app.models.document.Document", test_admin_user: "app.models.user.User") -> None:
    """
    Tests the permanent document deletion endpoint (admin only)
    """
    # Mock the document_chunk.remove_by_document_id method
    with mock.patch("src.backend.app.crud.crud_document_chunk.CRUDDocumentChunk.remove_by_document_id") as mock_remove_chunks:
        mock_remove_chunks.return_value = 1
        # Mock the file_storage.delete_document method
        with mock.patch("src.backend.app.services.file_storage.FileStorage.delete_document") as mock_delete_file:
            mock_delete_file.return_value = True
            # Send a DELETE request to the /documents/{document_id}/permanent endpoint
            response = client.delete(f"/documents/{test_document.id}/permanent")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON contains a success message
    response_json = response.json()
    assert "message" in response_json
    assert "Document permanently deleted" in response_json["message"]

    # Send a GET request to verify the document is no longer found (404)
    response = client.get(f"/documents/{test_document.id}")
    assert response.status_code == 404


def test_hard_delete_document_not_admin(client: "TestClient", test_document: "app.models.document.Document", test_user: "app.models.user.User") -> None:
    """
    Tests that regular users cannot use the permanent deletion endpoint
    """
    # Send a DELETE request to the /documents/{document_id}/permanent endpoint as a regular user
    response = client.delete(f"/documents/{test_document.id}/permanent")

    # Assert that the response status code is 403 (Forbidden)
    assert response.status_code == 403
    # Assert that the response JSON contains an error message about insufficient permissions
    response_json = response.json()
    assert "detail" in response_json
    assert "The user doesn't have enough permissions" in response_json["detail"]


def test_unauthorized_access(client: "TestClient", test_document: "app.models.document.Document") -> None:
    """
    Tests that unauthenticated users cannot access document endpoints
    """
    # Create a new test client without authentication
    unauth_client = test_client()

    # Send requests to various document endpoints
    endpoints = [
        f"/documents/{test_document.id}",
        f"/documents/{test_document.id}/chunks",
        f"/documents/{test_document.id}/download",
        f"/documents/{test_document.id}",
    ]
    for endpoint in endpoints:
        response = unauth_client.get(endpoint)
        # Assert that all responses have status code 401 (Unauthorized)
        assert response.status_code == 401
        # Assert that the response JSON contains authentication error messages
        response_json = response.json()
        assert "detail" in response_json
        assert "Not authenticated" in response_json["detail"]