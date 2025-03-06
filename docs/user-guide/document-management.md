# Document Management Guide

## Introduction

This guide provides detailed instructions for managing documents in the Document Management and AI Chatbot System. Document management is a core functionality that enables you to upload, organize, retrieve, and delete PDF documents that serve as the knowledge base for vector search and AI-powered responses.

Effective document management is essential for building a high-quality knowledge base that yields relevant search results and accurate AI responses. This guide will help you understand the document lifecycle, best practices for document preparation, and detailed instructions for all document management operations.

### Document Lifecycle

Documents in the system go through the following lifecycle stages:

1. **Upload**: Document is uploaded to the system and stored in the file system
2. **Processing**: System extracts text, creates chunks, and generates vector embeddings
3. **Available**: Document is fully processed and available for search
4. **Deleted**: Document is marked as deleted (soft delete) or permanently removed

When you upload a document, it initially has a 'processing' status while the system extracts text and generates vector embeddings. Once processing is complete, the status changes to 'available', and the document becomes searchable. If an error occurs during processing, the status changes to 'error', and the document won't be included in search results.

You can check a document's status at any time by retrieving its details through the API or user interface.

## Document Preparation

### Supported Document Formats

The system currently supports the following document format:

- **PDF (Portable Document Format)**: Standard format for document exchange

All uploaded documents must be valid PDF files with extractable text content. The system does not currently support other document formats such as DOCX, TXT, or HTML.

### Document Size Limits

Documents are subject to the following size limits:

- **Maximum file size**: 10MB per document

If you need to upload larger documents, consider splitting them into smaller files or compressing them while maintaining text quality. Very large documents may also benefit from being split into logical sections for more focused search results.

### Text Extraction Requirements

For optimal processing, documents should have the following characteristics:

- **Extractable text**: The PDF should contain actual text content, not just images of text
- **Clear formatting**: Well-structured documents with clear headings and paragraphs
- **Readable content**: Standard fonts and layouts that can be properly extracted

The system may have difficulty processing the following types of documents:

- Scanned documents without OCR (Optical Character Recognition)
- Password-protected or encrypted PDFs
- PDFs with complex layouts, tables, or charts
- PDFs with text embedded in images

If you have scanned documents, consider running them through an OCR process before uploading to ensure the text can be properly extracted.

### Document Organization Best Practices

To maximize the effectiveness of your document collection:

- **Use descriptive filenames**: Clear, descriptive filenames help with organization
- **Focus on content quality**: Higher quality content leads to better search results
- **Consider document granularity**: Smaller, focused documents often yield more precise search results than very large, broad documents
- **Maintain consistency**: Consistent document structure and terminology improves search relevance
- **Update regularly**: Keep your document collection current by replacing outdated documents with updated versions

Remember that the quality of search results and AI responses directly depends on the quality and organization of your document collection.

## Uploading Documents

### Upload Process Overview

Uploading a document involves the following steps:

1. Authenticate with the system
2. Prepare your PDF document according to the guidelines
3. Submit the document through the API
4. Receive a document ID and initial status
5. Wait for processing to complete
6. Verify the document status is 'available'

Once a document is successfully processed, it becomes available for search and can be used as context for AI-powered responses.

### Authentication Requirements

All document operations, including uploads, require authentication. You must include a valid JWT token in the Authorization header of your requests.

For details on obtaining and using authentication tokens, see the [Authentication API documentation](../api/authentication.md).

### Upload API Endpoint

To upload a document, make a POST request to the document upload endpoint:

```
POST /api/v1/documents/
Content-Type: multipart/form-data
Authorization: Bearer {your_access_token}

[file: your_document.pdf]
[title: Optional document title]
```

The request should include:
- The PDF file in multipart/form-data format
- An optional title parameter (if not provided, the filename will be used)
- A valid JWT token in the Authorization header

Example using curl:
```bash
curl -X POST "https://api.example.com/api/v1/documents/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/document.pdf" \
  -F "title=Introduction to Vector Databases"
```

Example using JavaScript:
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

### Upload Response

Upon successful upload, the system responds with document metadata including a unique document ID and initial status:

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

The initial status will be 'processing', indicating that the document is being processed for text extraction and vector embedding generation.

### Monitoring Processing Status

After uploading a document, you should monitor its processing status to ensure it becomes available for search. Processing time varies based on document size and complexity, typically ranging from a few seconds to a minute for standard documents.

To check a document's status, make a GET request to the document endpoint with the document ID:

```
GET /api/v1/documents/{document_id}
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response will include the current status:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Introduction to Vector Databases",
  "filename": "intro_vector_db.pdf",
  "size_bytes": 2048576,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "available",
  "file_path": "/storage/documents/123e4567-e89b-12d3-a456-426614174000.pdf",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
}
```

When the status changes to 'available', the document has been successfully processed and is ready for search.

### Handling Upload Errors

If the upload fails, the system will return an appropriate HTTP error code and message. Common error scenarios include:

- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid authentication token
- **413 Payload Too Large**: Document exceeds the 10MB size limit
- **415 Unsupported Media Type**: File format is not supported (only PDF allowed)
- **422 Unprocessable Entity**: Document validation failed

If a document is successfully uploaded but fails during processing, its status will be set to 'error'. You can still retrieve the document metadata and the original file, but the document won't be included in search results.

Common causes of processing errors include:
- Password-protected PDF files
- Corrupted PDF files
- PDFs with no extractable text (e.g., scanned documents without OCR)
- System resource limitations

If a document fails processing, consider checking the document for issues, applying OCR if needed, and reuploading.

### Bulk Upload Considerations

When uploading multiple documents:

- Upload documents sequentially rather than in parallel to avoid overwhelming the system
- Monitor the status of each document to ensure successful processing
- Consider implementing a retry mechanism for failed uploads
- Be mindful of rate limits that may apply to your account

For large document collections, consider developing a script that handles uploads in batches with appropriate error handling and status monitoring.

## Retrieving Documents

### Getting Document Metadata

To retrieve metadata for a specific document, make a GET request to the document endpoint with the document ID:

```
GET /api/v1/documents/{document_id}
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response includes comprehensive document metadata:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Introduction to Vector Databases",
  "filename": "intro_vector_db.pdf",
  "size_bytes": 2048576,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "available",
  "file_path": "/storage/documents/123e4567-e89b-12d3-a456-426614174000.pdf",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000",
  "uploader": {
    "id": "789e4567-e89b-12d3-a456-426614174000",
    "username": "johndoe",
    "email": "john.doe@example.com"
  }
}
```

This endpoint returns a 404 Not Found error if the document doesn't exist or a 403 Forbidden error if you don't have permission to access the document.

### Retrieving Document Content

To download the original PDF document, make a GET request to the document download endpoint:

```
GET /api/v1/documents/{document_id}/download
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/download" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --output document.pdf
```

Example using JavaScript:
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

The response will be the binary PDF file with appropriate Content-Type and Content-Disposition headers for downloading.

### Viewing Document Chunks

To retrieve a document along with its text chunks, make a GET request to the document chunks endpoint:

```
GET /api/v1/documents/{document_id}/chunks
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/chunks" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response includes the document metadata along with its text chunks:
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

Viewing document chunks can be useful for understanding how the system has processed your document and for debugging search relevance issues.

### Access Control Considerations

Document access is controlled by the following rules:

- Regular users can only access documents they have uploaded
- Admin users can access all documents in the system
- Attempting to access a document you don't have permission for results in a 403 Forbidden error

Ensure you have the appropriate permissions before attempting to retrieve document information or content.

## Listing Documents

### Basic Document Listing

To retrieve a list of documents, make a GET request to the documents endpoint:

```
GET /api/v1/documents/
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response includes a list of documents and pagination information:
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

By default, this endpoint returns up to 100 documents, starting from the first document.

### Pagination

For large document collections, you can use pagination parameters to retrieve documents in manageable batches:

```
GET /api/v1/documents/?skip=0&limit=10
Authorization: Bearer {your_access_token}
```

Pagination parameters:
- `skip`: Number of documents to skip (default: 0)
- `limit`: Maximum number of documents to return (default: 100, max: 100)

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/?skip=10&limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

This request would retrieve documents 11-20 from the collection (assuming they exist).

Example using JavaScript:
```javascript
async function listDocuments(accessToken, skip = 0, limit = 100) {
  const response = await fetch(`/api/v1/documents/?skip=${skip}&limit=${limit}`, {
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

For implementing pagination in a user interface, you can use the 'total' field in the response to calculate the total number of pages and display appropriate pagination controls.

### Filtering Documents

You can filter the document list using various query parameters:

```
GET /api/v1/documents/?status=available&title=vector
Authorization: Bearer {your_access_token}
```

Filter parameters:
- `title`: Filter by document title (substring match)
- `status`: Filter by document status ('processing', 'available', 'error', 'deleted')
- `upload_date_from`: Filter by upload date, starting from (ISO format)
- `upload_date_to`: Filter by upload date, ending at (ISO format)

Example using curl:
```bash
curl -X GET "https://api.example.com/api/v1/documents/?status=available&title=vector" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

This request would retrieve all available documents with 'vector' in the title.

Example using JavaScript:
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

// Example usage
listDocuments(accessToken, 0, 10, { status: 'available', title: 'vector' });
```

You can combine multiple filter parameters to narrow down the results, and you can also combine filtering with pagination.

### Sorting Documents

The document list is sorted by upload date in descending order by default (newest first). The current version of the API does not support custom sorting options.

If you need custom sorting in your application, you can retrieve the document list and implement client-side sorting based on your requirements.

### Access Control for Listing

Document listing is subject to the following access control rules:

- Regular users can only see documents they have uploaded
- Admin users can see all documents in the system

This means that the document list will automatically be filtered based on your user role and permissions.

## Deleting Documents

### Soft Deletion

To delete a document, make a DELETE request to the document endpoint with the document ID:

```
DELETE /api/v1/documents/{document_id}
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X DELETE "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Example using JavaScript:
```javascript
async function deleteDocument(documentId, accessToken) {
  const response = await fetch(`/api/v1/documents/${documentId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Delete failed: ${response.status}`);
  }

  return await response.json();
}
```

The response confirms the deletion:
```json
{
  "message": "Document successfully deleted",
  "document_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

This operation performs a soft delete, which means:
- The document's status is changed to 'deleted'
- The document is excluded from search results
- The document metadata remains in the database
- The original file remains in storage

Soft-deleted documents can still be retrieved by their ID, but they won't appear in document listings by default unless you specifically filter for deleted documents.

### Permanent Deletion (Admin Only)

Administrators can permanently delete a document by making a DELETE request to the permanent deletion endpoint:

```
DELETE /api/v1/documents/{document_id}/permanent
Authorization: Bearer {your_access_token}
```

Example using curl:
```bash
curl -X DELETE "https://api.example.com/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/permanent" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response confirms the permanent deletion:
```json
{
  "message": "Document permanently deleted",
  "document_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

This operation:
- Permanently removes the document metadata from the database
- Deletes the document chunks and their vector embeddings
- Removes the original file from storage

**Warning**: Permanent deletion is irreversible. Once a document is permanently deleted, it cannot be recovered. This operation is restricted to administrators only.

### Deletion Permissions

Document deletion is subject to the following permissions:

- Regular users can only delete documents they have uploaded
- Admin users can delete any document in the system
- Permanent deletion is restricted to administrators only

Attempting to delete a document you don't have permission for results in a 403 Forbidden error.

### Bulk Deletion Considerations

The current API does not provide a dedicated endpoint for bulk deletion. If you need to delete multiple documents, you'll need to make individual DELETE requests for each document.

For bulk deletion operations, consider implementing a client-side script that iterates through a list of document IDs and makes sequential delete requests with appropriate error handling.

## Document Processing Details

### Text Extraction

When a document is uploaded, the system extracts text content using the following process:

1. The PDF file is parsed using PyMuPDF (a Python binding for MuPDF)
2. Text is extracted from each page of the document
3. The extracted text is cleaned and normalized

The quality of text extraction depends on the PDF structure. Documents with actual text content (rather than scanned images) yield the best results. If a document contains scanned text without OCR, the system may not be able to extract any usable text.

### Document Chunking

After text extraction, the document content is split into smaller chunks for processing:

1. The extracted text is divided into chunks of approximately 1000 characters
2. Chunks have a 200-character overlap to maintain context across chunk boundaries
3. Each chunk is processed to count tokens (units of text used by the language model)

Chunking is necessary because:
- It allows for more precise search results by focusing on relevant sections
- It accommodates token limits in the language model context window
- It enables efficient vector storage and retrieval

The chunking parameters (chunk size and overlap) are optimized for general use cases, balancing search precision with processing efficiency.

### Vector Embedding Generation

For each document chunk, the system generates a vector embedding:

1. The chunk text is processed by a sentence transformer model
2. The model generates a high-dimensional vector (typically 768 dimensions) that represents the semantic meaning of the text
3. The vector is stored in the FAISS vector database with a reference to the original chunk

These vector embeddings enable semantic search, allowing the system to find documents based on meaning rather than just keywords. When you submit a search query, it's converted to a vector using the same process, and the system finds chunks with similar vectors.

The quality of vector embeddings depends on the underlying model and the quality of the text. Well-structured, clear text typically yields better embeddings and more relevant search results.

### Processing Status Updates

Throughout the document processing workflow, the system updates the document status:

1. **processing**: Initial status when document is uploaded
2. **available**: Status after successful processing
3. **error**: Status if processing fails

You can monitor the status by retrieving the document metadata. Processing time varies based on document size and complexity, typically ranging from a few seconds to a minute for standard documents.

## Troubleshooting

### Upload Failures

If document upload fails, check the following:

- **File format**: Ensure the file is a valid PDF
- **File size**: Verify the file is under the 10MB limit
- **Authentication**: Check that your authentication token is valid and not expired
- **Network issues**: Verify your network connection and try again

Common error codes and solutions:

- **400 Bad Request**: Check request parameters and file format
- **401 Unauthorized**: Refresh your authentication token
- **413 Payload Too Large**: Compress the PDF or split it into smaller files
- **415 Unsupported Media Type**: Convert the file to PDF format
- **422 Unprocessable Entity**: Check if the PDF is valid and not corrupted

### Processing Errors

If a document uploads successfully but ends up with an 'error' status, consider these potential causes and solutions:

- **Password protection**: Remove password protection from the PDF
- **Corrupted file**: Try repairing the PDF or recreating it
- **Scanned document**: Apply OCR to the document before uploading
- **Complex formatting**: Simplify the document structure if possible
- **Resource limitations**: Try uploading during off-peak hours or splitting the document

You can still retrieve the original file for documents with 'error' status, which may help in diagnosing and resolving the issue.

### Search Relevance Issues

If search results don't include documents you expect or aren't relevant, consider these factors:

- **Document status**: Ensure documents are in 'available' status
- **Text quality**: Check that text was properly extracted (view document chunks)
- **Query formulation**: Try rephrasing your query for better semantic matching
- **Document content**: Verify that the expected information is actually in your documents

For more information on optimizing search queries, see the [Searching Guide](./searching.md).

### Permission Denied Errors

If you receive 403 Forbidden errors when accessing documents:

- **Document ownership**: Verify that you are the uploader of the document or have admin privileges
- **Authentication**: Ensure your authentication token is valid and includes the necessary role claims
- **Account status**: Check that your user account is active and has the appropriate permissions

If you need access to documents uploaded by other users, contact your system administrator.

## Best Practices

### Document Quality Optimization

To maximize the effectiveness of your documents:

- **Use native PDFs**: Create PDFs directly from source applications rather than scanning
- **Apply OCR**: If using scanned documents, apply high-quality OCR before uploading
- **Optimize text layout**: Use clear headings, paragraphs, and formatting
- **Include metadata**: Use descriptive titles that reflect document content
- **Check text extraction**: After uploading, view document chunks to verify text quality

The quality of your documents directly impacts the quality of search results and AI responses.

### Document Organization Strategies

For effective document organization:

- **Develop a naming convention**: Use consistent, descriptive titles
- **Consider document granularity**: Split large documents into logical sections
- **Maintain document freshness**: Replace outdated documents with updated versions
- **Use consistent terminology**: Standardize terminology across related documents
- **Tag and categorize**: Use descriptive titles that include category information

Well-organized documents are easier to find and yield more relevant search results.

### Performance Considerations

To optimize system performance:

- **Manage document size**: Keep documents under 5MB when possible
- **Limit total document count**: Focus on quality over quantity
- **Batch uploads**: Space out large batch uploads to avoid system overload
- **Monitor processing status**: Ensure documents complete processing before querying
- **Clean up unused documents**: Delete documents that are no longer needed

These practices help maintain optimal system performance and search quality.

### Security and Compliance

For secure document management:

- **Review document content**: Ensure documents don't contain sensitive information before uploading
- **Manage access carefully**: Be mindful of who can access your documents
- **Use secure connections**: Always access the API over HTTPS
- **Rotate authentication tokens**: Refresh tokens regularly for security
- **Audit document access**: Periodically review your document collection

Remember that documents uploaded to the system will be processed and stored, and their content will be available to users with appropriate permissions.

## API Reference

### Document Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/documents/` | POST | Upload a new document |
| `/api/v1/documents/` | GET | List documents with filtering and pagination |
| `/api/v1/documents/{document_id}` | GET | Get document metadata |
| `/api/v1/documents/{document_id}/chunks` | GET | Get document with text chunks |
| `/api/v1/documents/{document_id}/download` | GET | Download original document file |
| `/api/v1/documents/{document_id}` | DELETE | Soft delete a document |
| `/api/v1/documents/{document_id}/permanent` | DELETE | Permanently delete a document (admin only) |

For detailed API documentation, including request and response formats, see the [Document API Reference](../api/documents.md).

### Common HTTP Status Codes

| Status Code | Description | Common Causes |
| --- | --- | --- |
| 200 OK | Request successful | Standard success response |
| 201 Created | Document created | Successful document upload |
| 400 Bad Request | Invalid request | Malformed request or parameters |
| 401 Unauthorized | Authentication required | Missing or invalid token |
| 403 Forbidden | Permission denied | Insufficient permissions |
| 404 Not Found | Resource not found | Document doesn't exist |
| 413 Payload Too Large | File too large | Document exceeds size limit |
| 415 Unsupported Media Type | Invalid file type | Non-PDF file uploaded |
| 422 Unprocessable Entity | Processing error | Invalid document content |
| 500 Internal Server Error | Server error | System failure or bug |

## Related Resources

### Related Documentation

- [Searching Guide](./searching.md) - How to search documents and understand results
- [Feedback Guide](./feedback.md) - Providing feedback on search results
- [API Integration Guide](./api-integration.md) - Technical guide for developers
- [Authentication Documentation](../api/authentication.md) - Authentication and authorization details
- [Document API Reference](../api/documents.md) - Detailed API documentation

### External Resources

- [PDF Specification](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf) - Official PDF format documentation
- [OCR Tools](https://github.com/tesseract-ocr/tesseract) - Tesseract OCR for improving scanned documents
- [PDF Compression Tools](https://www.adobe.com/acrobat/online/compress-pdf.html) - Tools for reducing PDF file size

## Conclusion

### Summary

This guide has covered all aspects of document management in the Document Management and AI Chatbot System:

- Uploading documents to the system
- Retrieving document information and content
- Listing and filtering documents
- Deleting documents from the system
- Understanding document processing
- Troubleshooting common issues
- Best practices for document management

Effective document management is the foundation for successful vector search and AI-powered responses. By following the guidelines and best practices in this document, you can build and maintain a high-quality document collection that yields relevant search results and accurate AI responses.

### Next Steps

Now that you understand document management, consider exploring these related topics:

- Learn how to perform effective searches using the [Searching Guide](./searching.md)
- Understand how to provide feedback using the [Feedback Guide](./feedback.md)
- Explore API integration options with the [API Integration Guide](./api-integration.md)

Continue to refine your document collection based on search results and user feedback to improve the overall system effectiveness.