import os  # standard library
import time  # standard library
import uuid  # standard library

import pytest  # pytest 7.0.0+

from fastapi.testclient import TestClient  # fastapi 0.95.0+

from src.backend.app.models.document import DocumentStatus  # Import document status enum for status verification
from src.backend.tests.conftest import (  # Import session factory for creating test database sessions
    override_get_current_admin_user,
    override_get_current_user,
    sample_pdf_path,
    test_client,
    test_user,
)


@pytest.mark.integration
def test_upload_document(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the document upload API endpoint"""
    # Open the sample PDF file
    with open(sample_pdf_path, "rb") as f:
        # Create a files dictionary with the PDF file
        files = {"file": f}
        # Send a POST request to the /documents/ endpoint
        response = client.post("/documents/", files=files)
    # Verify the response status code is 201 Created
    assert response.status_code == 201
    # Verify the response contains the expected document metadata
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert data["title"] == "Sample PDF Document"
    assert "filename" in data
    assert data["filename"] == "sample_document.pdf"
    assert "size_bytes" in data
    # Verify the document status is 'processing'
    assert "status" in data
    assert data["status"] == "processing"


@pytest.mark.integration
def test_list_documents(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the document listing API endpoint"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Send a GET request to the /documents/ endpoint
    response = client.get("/documents/")
    # Verify the response status code is 200 OK
    assert response.status_code == 200
    # Verify the response contains a list of documents
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    # Verify the response includes pagination information
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    # Verify the uploaded document is in the list
    document_ids = [item["id"] for item in data["items"]]
    assert upload_response.json()["id"] in document_ids


@pytest.mark.integration
def test_get_document(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the document retrieval API endpoint"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]
    # Send a GET request to the /documents/{document_id} endpoint
    response = client.get(f"/documents/{document_id}")
    # Verify the response status code is 200 OK
    assert response.status_code == 200
    # Verify the response contains the correct document metadata
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert "filename" in data
    assert "size_bytes" in data
    # Verify the document ID matches the uploaded document
    assert data["id"] == document_id


@pytest.mark.integration
def test_get_document_with_chunks(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the document retrieval with chunks API endpoint"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]

    # Wait for document processing to complete (status changes to 'available')
    def wait_for_document_processing(client: TestClient, document_id: str, max_wait_seconds: int = 10, check_interval_seconds: int = 1) -> bool:
        end_time = time.time() + max_wait_seconds
        while time.time() < end_time:
            response = client.get(f"/documents/{document_id}")
            if response.json()["status"] == "available":
                return True
            time.sleep(check_interval_seconds)
        return False

    assert wait_for_document_processing(client, document_id)

    # Send a GET request to the /documents/{document_id}/chunks endpoint
    response = client.get(f"/documents/{document_id}/chunks")
    # Verify the response status code is 200 OK
    assert response.status_code == 200
    # Verify the response contains the document with its chunks
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert "filename" in data
    assert "size_bytes" in data
    assert "chunks" in data
    assert isinstance(data["chunks"], list)
    # Verify the chunks contain text content and token counts
    for chunk in data["chunks"]:
        assert "id" in chunk
        assert "document_id" in chunk
        assert "chunk_index" in chunk
        assert "content" in chunk
        assert "token_count" in chunk


@pytest.mark.integration
def test_download_document(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the document download API endpoint"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]
    # Send a GET request to the /documents/{document_id}/download endpoint
    response = client.get(f"/documents/{document_id}/download")
    # Verify the response status code is 200 OK
    assert response.status_code == 200
    # Verify the response content type is application/pdf
    assert response.headers["content-type"] == "application/pdf"
    # Verify the response content matches the original PDF file
    with open(sample_pdf_path, "rb") as f:
        original_content = f.read()
    assert response.content == original_content


@pytest.mark.integration
def test_delete_document(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the document deletion API endpoint"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]
    # Send a DELETE request to the /documents/{document_id} endpoint
    response = client.delete(f"/documents/{document_id}")
    # Verify the response status code is 200 OK
    assert response.status_code == 200
    # Verify the response contains a success message
    assert response.json() == {"message": "Document deleted successfully"}
    # Send a GET request to the /documents/{document_id} endpoint
    response = client.get(f"/documents/{document_id}")
    # Verify the document status is now 'deleted'
    assert response.json()["status"] == "deleted"


@pytest.mark.integration
def test_hard_delete_document(
    client: TestClient,
    sample_pdf_path: str,
    override_get_current_admin_user,  # Fixture for creating a test client for API testing
) -> None:
    """Tests the permanent document deletion API endpoint (admin only)"""
    # Override the current user dependency with admin user
    override_get_current_admin_user
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]
    # Send a DELETE request to the /documents/{document_id}/permanent endpoint
    response = client.delete(f"/documents/{document_id}/permanent")
    # Verify the response status code is 200 OK
    assert response.status_code == 200
    # Verify the response contains a success message
    assert response.json() == {"message": "Document permanently deleted"}
    # Send a GET request to the /documents/{document_id} endpoint
    response = client.get(f"/documents/{document_id}")
    # Verify the response status code is 404 Not Found (document completely removed)
    assert response.status_code == 404


@pytest.mark.integration
def test_document_processing_workflow(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests the complete document processing workflow from upload to availability"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]
    # Verify initial document status is 'processing'
    response = client.get(f"/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    # Poll the document status until it changes to 'available' or timeout
    def wait_for_document_processing(client: TestClient, document_id: str, max_wait_seconds: int = 10, check_interval_seconds: int = 1) -> bool:
        end_time = time.time() + max_wait_seconds
        while time.time() < end_time:
            response = client.get(f"/documents/{document_id}")
            if response.json()["status"] == "available":
                return True
            time.sleep(check_interval_seconds)
        return False

    # Verify the document status is eventually 'available'
    assert wait_for_document_processing(client, document_id)

    # Get document with chunks to verify processing completed
    response = client.get(f"/documents/{document_id}/chunks")
    assert response.status_code == 200
    data = response.json()
    # Verify document chunks were created and have vector embeddings
    assert len(data["chunks"]) > 0
    for chunk in data["chunks"]:
        assert "embedding_id" in chunk
        assert chunk["embedding_id"] is not None


@pytest.mark.integration
def test_document_filter_by_status(
    client: TestClient, sample_pdf_path: str
) -> None:  # Fixture for creating a test client for API testing
    """Tests filtering documents by status"""
    # Upload a test document using the upload endpoint
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    # Send a GET request to the /documents/ endpoint with status=processing filter
    response = client.get("/documents/?status=processing")
    assert response.status_code == 200
    data = response.json()
    # Verify the response contains the uploaded document
    document_ids = [item["id"] for item in data["items"]]
    assert upload_response.json()["id"] in document_ids

    # Wait for document processing to complete
    def wait_for_document_processing(client: TestClient, document_id: str, max_wait_seconds: int = 10, check_interval_seconds: int = 1) -> bool:
        end_time = time.time() + max_wait_seconds
        while time.time() < end_time:
            response = client.get(f"/documents/{document_id}")
            if response.json()["status"] == "available":
                return True
            time.sleep(check_interval_seconds)
        return False

    assert wait_for_document_processing(client, document_id)

    # Send a GET request to the /documents/ endpoint with status=available filter
    response = client.get("/documents/?status=available")
    assert response.status_code == 200
    data = response.json()
    # Verify the response contains the processed document
    document_ids = [item["id"] for item in data["items"]]
    assert upload_response.json()["id"] in document_ids

    # Send a GET request to the /documents/ endpoint with status=error filter
    response = client.get("/documents/?status=error")
    assert response.status_code == 200
    data = response.json()
    # Verify the response does not contain the document
    document_ids = [item["id"] for item in data["items"]]
    assert upload_response.json()["id"] not in document_ids


@pytest.mark.integration
def test_unauthorized_document_access(
    client: TestClient,
    sample_pdf_path: str,
    override_get_current_user,  # Fixture for creating a test client for API testing
) -> None:
    """Tests that users cannot access documents they don't own"""
    # Upload a test document using the upload endpoint with user A
    with open(sample_pdf_path, "rb") as f:
        files = {"file": f}
        upload_response = client.post("/documents/", files=files)
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    # Extract the document ID from the upload response
    document_id = upload_response.json()["id"]
    # Override the current user dependency with user B
    override_get_current_user
    # Send a GET request to the /documents/{document_id} endpoint
    response = client.get(f"/documents/{document_id}")
    # Verify the response status code is 403 Forbidden
    assert response.status_code == 403
    # Send a DELETE request to the /documents/{document_id} endpoint
    response = client.delete(f"/documents/{document_id}")
    # Verify the response status code is 403 Forbidden
    assert response.status_code == 403


def wait_for_document_processing(client: TestClient, document_id: uuid.UUID, max_wait_seconds: int = 10, check_interval_seconds: int = 1) -> bool:
    """Helper function to wait for document processing to complete"""
    # Calculate the end time based on max_wait_seconds
    end_time = time.time() + max_wait_seconds
    # Loop until current time exceeds end time:
    while time.time() < end_time:
        # Send a GET request to the /documents/{document_id} endpoint
        response = client.get(f"/documents/{document_id}")
        # Check if document status is 'available'
        if response.json()["status"] == "available":
            # If available, return True
            return True
        # Sleep for check_interval_seconds
        time.sleep(check_interval_seconds)
    # Return False if timeout is reached
    return False