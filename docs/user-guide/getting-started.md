# Getting Started with the Document Management and AI Chatbot System

## Introduction

Welcome to the Document Management and AI Chatbot System! This powerful tool combines document storage with advanced vector search and AI-powered responses to help you efficiently manage and extract insights from your document collection.

This getting started guide will walk you through the basics of using the system, from setting up your account to performing your first search and providing feedback. By the end of this guide, you'll have a solid understanding of the system's core capabilities and how to use them effectively.

### System Overview

The Document Management and AI Chatbot System provides the following key features:

- **Document Management**: Upload, organize, retrieve, and delete PDF documents
- **Vector Search**: Find semantically relevant information using natural language queries
- **AI-Powered Responses**: Get contextual answers generated from your document content
- **Feedback Collection**: Provide feedback to improve response quality over time

The system is designed as a backend solution with a comprehensive API, allowing for integration with various client applications or direct API usage.

## Setting Up Your Account

### Account Creation

To start using the Document Management and AI Chatbot System, you'll need an account. Contact your system administrator to create an account for you. You'll receive an email with your initial login credentials and instructions for accessing the system.

### First Login

When logging in for the first time:

1. Navigate to the system URL provided by your administrator
2. Enter your username (typically your email address) and the temporary password provided
3. You'll be prompted to change your password
4. Choose a strong password that meets the system requirements (minimum 10 characters, including uppercase, lowercase, numbers, and special characters)
5. After changing your password, you'll be logged into the system

Your account will have specific permissions based on your role in the organization. Standard roles include:

- **Regular User**: Can upload documents, perform searches, and provide feedback
- **Administrator**: Has additional capabilities for user management and system configuration

### Authentication Tokens

If you're using the system's API directly, you'll need to obtain authentication tokens:

1. Make a POST request to the `/api/v1/auth/token` endpoint with your credentials:

```
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "your_email@example.com",
  "password": "your_password"
}
```

2. The system will respond with an access token and refresh token:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "6fd8d272-375a-4d8f-b2ba-edfbf596592f"
}
```

3. Include the access token in the Authorization header for all subsequent API requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

For more details on authentication, see the [Authentication API documentation](../api/authentication.md).

## Uploading Your First Document

### Document Preparation

Before uploading a document, ensure it meets the following requirements:

- File format: PDF only
- Maximum file size: 10MB
- Content: The document should contain extractable text (not just scanned images)

For optimal results, choose well-structured documents with clear text content. This will ensure better text extraction and more accurate search results.

### Upload Process

To upload your first document:

1. Ensure you have a valid authentication token
2. Prepare your PDF document for upload
3. Make a POST request to the document upload endpoint:

```
POST /api/v1/documents/
Content-Type: multipart/form-data
Authorization: Bearer {your_access_token}

[file: your_document.pdf]
```

4. The system will respond with document metadata, including a unique document ID and initial status (typically 'processing'):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "your_document.pdf",
  "filename": "your_document.pdf",
  "size_bytes": 125000,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "processing",
  "file_path": "/storage/documents/123e4567-e89b-12d3-a456-426614174000.pdf",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
}
```

5. The system will process the document asynchronously, extracting text and generating vector embeddings. This typically takes a few seconds to a minute, depending on the document size and complexity.

### Checking Document Status

After uploading, you can check the document's processing status:

1. Make a GET request to the document endpoint with the document ID:

```
GET /api/v1/documents/{document_id}
Authorization: Bearer {your_access_token}
```

2. The system will respond with the current document status:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "your_document.pdf",
  "filename": "your_document.pdf",
  "size_bytes": 125000,
  "upload_date": "2023-06-15T10:30:00Z",
  "status": "available",
  "file_path": "/storage/documents/123e4567-e89b-12d3-a456-426614174000.pdf",
  "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
}
```

When the status changes to "available", the document has been successfully processed and is ready for searching.

### Troubleshooting Upload Issues

If you encounter issues during document upload:

- **413 Payload Too Large**: Your document exceeds the 10MB size limit. Try compressing the PDF or splitting it into smaller documents.

- **415 Unsupported Media Type**: The system only accepts PDF files. Verify your file format.

- **422 Unprocessable Entity**: The system couldn't process your document. This could be due to password protection, corrupted file, or other issues with the PDF.

- **Error Status After Processing**: If your document ends up in the 'error' state, there was an issue during processing. Common causes include text extraction problems or invalid document content.

For more detailed information on document management, see the [Document Management Guide](./document-management.md).

## Performing Your First Search

### Understanding Vector Search

The Document Management and AI Chatbot System uses vector search to find semantically relevant information in your documents. Unlike traditional keyword search, vector search understands the meaning behind your query, not just the exact words.

When you submit a query, the system:

1. Converts your query text into a vector embedding
2. Searches the vector database for document chunks with similar embeddings
3. Retrieves the most relevant document chunks based on similarity scores
4. Uses these relevant chunks as context for generating an AI response

This approach allows the system to find information that is conceptually similar to your query, even if it doesn't contain the exact keywords you used.

### Formulating Effective Queries

For the best results, follow these guidelines when formulating queries:

- **Be specific**: Clearly state what you're looking for
- **Use natural language**: Full questions often work better than keywords
- **Include context**: Provide relevant background information
- **Focus on one topic**: Avoid multi-part questions in a single query

Examples of effective queries:

✅ "What are the main advantages of vector databases over traditional databases?"
✅ "How does the document chunking process work in the system?"
✅ "Explain the concept of similarity scores in vector search"

Less effective queries:

❌ "vector databases" (too vague)
❌ "What are vector databases and how do they work and what are their limitations?" (too many questions at once)
❌ "Tell me everything about searching" (too broad)

### Submitting a Query

To submit your first search query:

1. Ensure you have a valid authentication token
2. Formulate a clear, specific query related to your uploaded document(s)
3. Make a POST request to the query endpoint:

```
POST /api/v1/query/
Content-Type: application/json
Authorization: Bearer {your_access_token}

{
  "query_text": "What are the key benefits of vector databases?",
  "max_results": 5,
  "similarity_threshold": 0.7
}
```

4. The system will respond with an AI-generated answer and relevant document chunks:

```json
{
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "query_text": "What are the key benefits of vector databases?",
  "response_text": "Vector databases offer several key benefits including: 1) Efficient similarity search for high-dimensional data, 2) Better semantic understanding compared to keyword search, 3) Ability to find related content even when exact keywords aren't present, 4) Scalability for large document collections, and 5) Optimized performance for AI and machine learning applications.",
  "relevant_documents": [
    {
      "id": "abc12345-e89b-12d3-a456-426614174000",
      "document_id": "def67890-e89b-12d3-a456-426614174000",
      "chunk_index": 3,
      "content": "Vector databases provide efficient similarity search capabilities for high-dimensional data. Unlike traditional databases, they can quickly find the most similar items based on semantic meaning rather than exact keyword matches.",
      "token_count": 142,
      "similarity_score": 0.92
    },
    {
      "id": "ghi12345-e89b-12d3-a456-426614174000",
      "document_id": "jkl67890-e89b-12d3-a456-426614174000",
      "chunk_index": 7,
      "content": "The scalability of vector databases makes them ideal for large document collections. They can handle millions of vectors while maintaining fast query performance.",
      "token_count": 98,
      "similarity_score": 0.85
    }
  ]
}
```

### Understanding Search Results

The search response contains several key components:

1. **AI-Generated Response**: A natural language answer to your query, synthesized from the relevant document chunks. This response aims to directly answer your question based on the information found in your documents.

2. **Relevant Documents**: A list of document chunks that the system found relevant to your query, sorted by similarity score (most relevant first). Each document chunk includes:
   - Document ID and chunk ID for reference
   - Chunk index within the document
   - The actual text content of the chunk
   - Token count (a measure of text length)
   - Similarity score indicating relevance to your query

3. **Query ID**: A unique identifier for your query that you can use to retrieve the same results later or provide feedback.

The quality of the response depends on the relevance and quality of the documents in your collection. If you don't get satisfactory results, try refining your query or uploading more relevant documents.

For more detailed information on searching, see the [Searching Guide](./searching.md).

## Providing Feedback

### Why Feedback Matters

Your feedback plays a vital role in improving the Document Management and AI Chatbot System:

1. **Quality Improvement**: Feedback helps identify strengths and weaknesses in AI-generated responses
2. **Personalization**: The system learns from your preferences to provide more relevant answers
3. **Reinforcement Learning**: Accumulated feedback trains the system to generate better responses over time
4. **Content Gaps**: Your feedback helps identify areas where document coverage could be improved

Every piece of feedback contributes to a continuous improvement cycle that benefits all users of the system.

### Submitting Feedback

To provide feedback on an AI-generated response:

1. Ensure you have a valid authentication token
2. Make a POST request to the feedback endpoint:

```
POST /api/v1/feedback/
Content-Type: application/json
Authorization: Bearer {your_access_token}

{
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "rating": 4,
  "comments": "Good response, but could include more specific examples."
}
```

3. The system will respond with the saved feedback:

```json
{
  "id": "abc12345-e89b-12d3-a456-426614174000",
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "789e4567-e89b-12d3-a456-426614174000",
  "rating": 4,
  "comments": "Good response, but could include more specific examples.",
  "feedback_time": "2023-06-15T14:30:00Z"
}
```

The rating scale is:

- 1: Poor - Response was not helpful or relevant
- 2: Fair - Response had some relevant information but was mostly unhelpful
- 3: Average - Response was moderately helpful
- 4: Good - Response was helpful and mostly relevant
- 5: Excellent - Response was very helpful and highly relevant

The `comments` field is optional but provides valuable qualitative feedback.

### Feedback Best Practices

For the most effective feedback:

- **Be specific**: Mention exactly what was helpful or unhelpful
- **Provide context**: Explain why the response did or didn't meet your needs
- **Suggest improvements**: Offer constructive suggestions for better responses
- **Highlight strengths**: Note particularly useful aspects of good responses

Consistent, thoughtful feedback contributes significantly to system improvement over time.

For more detailed information on the feedback system, see the [Feedback Guide](./feedback.md).

## Managing Documents

### Listing Your Documents

To retrieve a list of all your documents:

1. Make a GET request to the documents endpoint:

```
GET /api/v1/documents/
Authorization: Bearer {your_access_token}
```

2. The system will respond with a list of your documents:

```json
{
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "document1.pdf",
      "filename": "document1.pdf",
      "size_bytes": 125000,
      "upload_date": "2023-06-15T10:30:00Z",
      "status": "available",
      "file_path": "/storage/documents/123e4567-e89b-12d3-a456-426614174000.pdf",
      "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
    },
    {
      "id": "456e4567-e89b-12d3-a456-426614174000",
      "title": "document2.pdf",
      "filename": "document2.pdf",
      "size_bytes": 250000,
      "upload_date": "2023-06-16T14:45:00Z",
      "status": "processing",
      "file_path": "/storage/documents/456e4567-e89b-12d3-a456-426614174000.pdf",
      "uploader_id": "789e4567-e89b-12d3-a456-426614174000"
    }
  ],
  "total": 42
}
```

You can use query parameters for filtering and pagination:

- `status`: Filter by document status (e.g., 'processing', 'available')
- `title_contains`: Filter by title substring
- `skip`: Number of items to skip (for pagination)
- `limit`: Maximum number of items to return (for pagination)

### Retrieving Document Content

To retrieve the original PDF content of a document:

1. Make a GET request to the document content endpoint:

```
GET /api/v1/documents/{document_id}/content
Authorization: Bearer {your_access_token}
```

2. The system will respond with the binary PDF content with Content-Type: application/pdf.

This endpoint is useful for downloading the original document for viewing or saving locally.

### Deleting Documents

To delete a document from the system:

1. Make a DELETE request to the document endpoint:

```
DELETE /api/v1/documents/{document_id}
Authorization: Bearer {your_access_token}
```

2. The system will respond with a confirmation message:

```json
{
  "message": "Document successfully deleted",
  "document_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Important**: Document deletion is permanent and cannot be undone. Make sure you have a backup if needed before deleting.

## Next Steps

### Exploring Advanced Features

Now that you've learned the basics, consider exploring these advanced features:

- **Document Organization**: Develop naming conventions and organization strategies for your documents
- **Advanced Searching**: Learn about adjusting search parameters and formulating complex queries
- **Feedback Analysis**: Review your feedback history and track system improvements
- **API Integration**: Integrate the system with your own applications or workflows

The detailed guides for each feature area provide comprehensive information on these advanced capabilities.

### Detailed Documentation

For more in-depth information on specific features, refer to these detailed guides:

- [Document Management Guide](./document-management.md) - Comprehensive guide to document operations
- [Searching Guide](./searching.md) - Detailed information on vector search and query optimization
- [Feedback Guide](./feedback.md) - Complete guide to the feedback system and reinforcement learning
- [API Integration Guide](./api-integration.md) - Technical guide for developers integrating with the API

### Best Practices

To get the most out of the system:

- **Upload high-quality documents**: Well-structured documents with clear text yield better search results
- **Use specific queries**: Clear, focused questions get more relevant answers
- **Provide consistent feedback**: Regular, thoughtful feedback helps improve the system
- **Organize your documents**: Develop a consistent naming and organization scheme
- **Explore iteratively**: Use search results to refine subsequent queries

Regular use and experimentation will help you develop effective strategies for your specific needs.

### Getting Help

If you encounter issues or have questions:

- Consult the detailed documentation for specific feature areas
- Check the troubleshooting sections in each guide
- Contact your system administrator for organization-specific guidance
- For developers, refer to the API documentation for technical details

## Conclusion

### Summary

In this getting started guide, you've learned how to:

- Set up your account and authenticate with the system
- Upload your first document and check its processing status
- Perform your first search query and understand the results
- Provide feedback to help improve the system
- Manage your documents with basic operations

These fundamental skills provide the foundation for effectively using the Document Management and AI Chatbot System. As you continue to use the system, you'll discover more advanced features and develop strategies tailored to your specific needs.

### Key Takeaways

Remember these key points as you begin using the system:

- The system combines document management with vector search and AI-powered responses
- Document quality directly impacts search quality and AI responses
- Natural language queries typically work better than keyword searches
- Your feedback helps improve the system for everyone
- Detailed documentation is available for each feature area

With practice and exploration, you'll soon be leveraging the full power of the Document Management and AI Chatbot System to efficiently manage and extract insights from your document collection.