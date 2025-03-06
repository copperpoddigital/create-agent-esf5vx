# Document Management API

The Document Management API provides endpoints for uploading, retrieving, listing, and deleting documents in the Document Management and AI Chatbot System. These endpoints enable the core document management functionality that serves as the foundation for vector search and AI-powered responses.

## Overview

The Document Management API allows users to upload PDF documents, which are then processed to extract text content and generate vector embeddings for similarity search. The API also provides endpoints for retrieving document metadata, downloading original documents, and managing the document lifecycle.

## Authentication

All document management endpoints require authentication using JWT tokens. See the [Authentication API](./authentication.md) documentation for details on obtaining and using authentication tokens.

## Performance Expectations

Document upload and processing is designed to complete within 10 seconds for documents up to 10MB in size. Actual processing time may vary based on document complexity and system load.

# API Endpoints

The following endpoints are available for document management operations:

## Upload Document

**POST /api/v1/documents/**

Upload a new document to the system.

**Request:**
- Content-Type: multipart/form-data
- Authorization: Bearer {access_token}

**Request Body:**
- `file`: PDF document file (required)
- `title`: Document title (optional, defaults to filename)

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Introduction to Vector Databases",
  "filename": "intro_vector_db.pdf",
  "size_bytes": 2048576,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "processing",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
}
```

**Status Codes:**
- `201 Created`: Document uploaded successfully and processing started
- `400 Bad Request`: Invalid request or document format
- `401 Unauthorized`: Missing or invalid authentication
- `413 Payload Too Large`: Document exceeds maximum size limit (10MB)
- `415 Unsupported Media Type`: File format not supported (only PDF allowed)
- `422 Unprocessable Entity`: Document validation error

**Notes:**
- Document processing occurs asynchronously after the upload response
- Initial document status will be 'processing'
- Use the Get Document endpoint to check when processing is complete (status changes to 'available')

### Example Request

```bash
curl -X POST "https://api.example.com/api/v1/documents/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/document.pdf" \
  -F "title=Introduction to Vector Databases"
```

### Example Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Introduction to Vector Databases",
  "filename": "document.pdf",
  "size_bytes": 2048576,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "processing",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
}
```

## List Documents

**GET /api/v1/documents/**

Retrieve a list of documents with pagination and filtering options.

**Request:**
- Authorization: Bearer {access_token}

**Query Parameters:**
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100)
- `title`: Filter by document title (optional)
- `status`: Filter by document status (optional)
- `upload_date_from`: Filter by upload date, starting from (optional)
- `upload_date_to`: Filter by upload date, ending at (optional)

**Response:**
```json
{
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Introduction to Vector Databases",
      "filename": "intro_vector_db.pdf",
      "size_bytes": 2048576,
      "upload_date": "2023-06-15T10:30:00Z",
      "status": "available",
      "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
    },
    {
      "id": "456e4567-e89b-12d3-a456-426614174000",
      "title": "Vector Search Techniques",
      "filename": "vector_search.pdf",
      "size_bytes": 1548576,
      "upload_date": "2023-06-16T14:45:00Z",
      "status": "available",
      "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
    }
  ],
  "total": 24
}
```

**Status Codes:**
- `200 OK`: Request successful
- `400 Bad Request`: Invalid filter parameters
- `401 Unauthorized`: Missing or invalid authentication

**Notes:**
- Regular users can only see their own documents
- Admin users can see all documents in the system
- The response includes the total count of documents matching the filter criteria

### Example Request with Filters

```bash
curl -X GET "https://api.example.com/api/v1/documents/?status=available&limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Get Document

**GET /api/v1/documents/{document_id}**

Retrieve a specific document by ID.

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `document_id`: UUID of the document

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Introduction to Vector Databases",
  "filename": "intro_vector_db.pdf",
  "size_bytes": 2048576,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "available",
  "file_path": "documents/123e4567-e89b-12d3-a456-426614174000.pdf",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000",
  "uploader": {
    "id": "789e4567-e89b-12d3-a456-426614174000",
    "username": "johndoe",
    "email": "john.doe@example.com"
  }
}
```

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have access to this document
- `404 Not Found`: Document not found

### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Get Document with Chunks

**GET /api/v1/documents/{document_id}/chunks**

Retrieve a document with its text chunks.

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `document_id`: UUID of the document

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Introduction to Vector Databases",
  "filename": "intro_vector_db.pdf",
  "size_bytes": 2048576,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "available",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000",
  "chunks": [
    {
      "id": "abc12345-e89b-12d3-a456-426614174000",
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "chunk_index": 0,
      "content": "Vector databases are specialized database systems designed to store and query high-dimensional vectors efficiently. These vectors typically represent embeddings of text, images, or other data types.",
      "token_count": 128,
      "embedding_id": "vec_123456"
    },
    {
      "id": "def67890-e89b-12d3-a456-426614174000",
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "chunk_index": 1,
      "content": "Unlike traditional databases that excel at exact matches, vector databases are optimized for similarity search. They can quickly find the most similar vectors to a query vector using algorithms like approximate nearest neighbors.",
      "token_count": 142,
      "embedding_id": "vec_234567"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have access to this document
- `404 Not Found`: Document not found

### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/chunks" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Download Document

**GET /api/v1/documents/{document_id}/download**

Download the original document file.

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `document_id`: UUID of the document

**Response:**
- Content-Type: application/pdf
- Content-Disposition: attachment; filename="document_title.pdf"
- Binary file content

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have access to this document
- `404 Not Found`: Document not found

### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/download" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --output document.pdf
```

## Delete Document

**DELETE /api/v1/documents/{document_id}**

Soft delete a document (mark as deleted).

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `document_id`: UUID of the document

**Response:**
```json
{
  "message": "Document successfully deleted",
  "document_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Status Codes:**
- `200 OK`: Document successfully deleted
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have access to delete this document
- `404 Not Found`: Document not found

**Notes:**
- This operation performs a soft delete (sets status to 'deleted')
- The document remains in the database but is excluded from search results
- Only the document owner or an admin can delete a document

### Example Request

```bash
curl -X DELETE "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Permanently Delete Document

**DELETE /api/v1/documents/{document_id}/permanent**

Permanently delete a document and its associated data (admin only).

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `document_id`: UUID of the document

**Response:**
```json
{
  "message": "Document permanently deleted",
  "document_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Status Codes:**
- `200 OK`: Document permanently deleted
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have admin privileges
- `404 Not Found`: Document not found

**Notes:**
- This operation permanently removes the document from the database
- Document chunks and vector embeddings are also removed
- The original file is deleted from storage
- This operation can only be performed by administrators

### Example Request

```bash
curl -X DELETE "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/permanent" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

# Document Data Models

The following data models are used in the Document API:

## Document

```json
{
  "id": "UUID",
  "title": "string (3-255 characters)",
  "filename": "string",
  "size_bytes": "integer",
  "upload_date": "datetime",
  "status": "string (processing, available, error, deleted)",
  "file_path": "string (optional)",
  "uploader_id": "UUID",
  "uploader": "User object (optional)"
}
```

## DocumentChunk

```json
{
  "id": "UUID",
  "document_id": "UUID",
  "chunk_index": "integer",
  "content": "string",
  "token_count": "integer",
  "embedding_id": "string"
}
```

## DocumentWithChunks

```json
{
  "id": "UUID",
  "title": "string",
  "filename": "string",
  "size_bytes": "integer",
  "upload_date": "datetime",
  "status": "string",
  "uploader_id": "UUID",
  "chunks": [
    {
      "id": "UUID",
      "document_id": "UUID",
      "chunk_index": "integer",
      "content": "string",
      "token_count": "integer",
      "embedding_id": "string"
    }
  ]
}
```

## DocumentFilter

```json
{
  "title": "string (optional)",
  "status": "string (optional)",
  "uploader_id": "UUID (optional)",
  "upload_date_from": "datetime (optional)",
  "upload_date_to": "datetime (optional)"
}
```

# Document Processing

When a document is uploaded, it goes through the following processing steps:

## Processing Workflow

1. **Upload**: Document is uploaded and stored in the file system
2. **Text Extraction**: Text content is extracted from the PDF document
3. **Chunking**: The text is split into manageable chunks for processing
4. **Vector Embedding**: Each chunk is converted to a vector embedding
5. **Indexing**: Vector embeddings are stored in the FAISS index for similarity search
6. **Status Update**: Document status is updated to 'available' when processing is complete

## Processing Status

Documents can have the following status values:

- **processing**: Document has been uploaded and is being processed
- **available**: Document has been successfully processed and is available for search
- **error**: An error occurred during document processing
- **deleted**: Document has been marked as deleted

## Error Handling

If an error occurs during document processing, the document status will be set to 'error'. Common causes of processing errors include:

- Corrupted PDF files
- Password-protected PDF files
- PDF files with no extractable text (e.g., scanned documents without OCR)
- System resource limitations

When a document has an 'error' status, it will not be included in search results. The original file can still be downloaded, but vector search functionality will not be available for that document.

# Error Handling

The Document API uses standard HTTP status codes and returns error details in a consistent format:

## Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

## Common Error Codes

- `400 Bad Request`: Invalid request parameters or body
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Authenticated user does not have permission for the requested operation
- `404 Not Found`: Requested document does not exist
- `413 Payload Too Large`: Document exceeds maximum size limit (10MB)
- `415 Unsupported Media Type`: File format not supported (only PDF allowed)
- `422 Unprocessable Entity`: Request validation error
- `500 Internal Server Error`: Server-side error

## Validation Errors

- Document title must be between 3 and 255 characters
- Document size must not exceed 10MB
- Only PDF files are supported
- Filter parameters must be valid (e.g., dates in ISO format)

# Implementation Examples

Code examples for common document operations:

## Upload Document Example (JavaScript)

```javascript
async function uploadDocument(file, title, accessToken) {
  const formData = new FormData();
  formData.append('file', file);
  if (title) {
    formData.append('title', title);
  }

  const response = await fetch('/api/v1/documents/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    body: formData
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  return await response.json();
}
```

## List Documents Example (JavaScript)

```javascript
async function listDocuments(accessToken, skip = 0, limit = 100, filters = {}) {
  // Convert filters to query parameters
  const queryParams = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
    ...filters
  });

  const response = await fetch(`/api/v1/documents/?${queryParams}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to list documents: ${response.status}`);
  }

  return await response.json();
}
```

## Download Document Example (JavaScript)

```javascript
async function downloadDocument(documentId, accessToken) {
  const response = await fetch(`/api/v1/documents/${documentId}/download`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`);
  }

  // Create a blob from the PDF stream
  const blob = await response.blob();
  
  // Create a link element and trigger download
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/\"/g, '') || 'document.pdf';
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(downloadUrl);
  a.remove();
}
```

# Related Documentation

Additional resources for working with the Document API:

## References

- [Authentication API](./authentication.md) - Authentication and authorization for API access
- Query API - For searching documents and generating AI responses based on document content
- [Feedback API](./feedback.md) - Providing feedback on query responses
- [OpenAPI Specification](./openapi.json) - Complete API specification including document endpoints