# Query API

The Query API provides endpoints for submitting search queries, retrieving AI-generated responses, and managing query history. These endpoints enable the core vector search and AI chatbot functionality of the Document Management and AI Chatbot System.

## Overview

The Query API allows users to submit natural language queries and receive AI-generated responses based on the content of documents stored in the system. The system uses vector similarity search to find relevant document chunks and then generates contextual responses using a language model.

## Authentication

Most query endpoints require authentication using JWT tokens. See the [Authentication API](./authentication.md) documentation for details on obtaining and using authentication tokens. The main query endpoint supports optional authentication, allowing both authenticated and anonymous users to submit queries.

## Performance Expectations

- Query response time: < 3 seconds for standard queries
- Maximum query length: 1000 characters
- Minimum query length: 3 characters

## API Endpoints

The following endpoints are available for query operations:

### Submit Query

**POST /api/v1/query/**

Submit a search query and receive an AI-generated response with relevant documents.

**Request:**
- Content-Type: application/json
- Authorization: Bearer {access_token} (optional)

**Request Body:**
```json
{
  "query_text": "How does vector similarity search work?",
  "max_results": 5,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "query_text": "How does vector similarity search work?",
  "response_text": "Vector similarity search works by converting text into numerical vector representations (embeddings) that capture semantic meaning. These vectors are stored in a specialized database like FAISS. When a query is submitted, it's also converted to a vector, and the system finds documents with vectors most similar to the query vector using distance metrics like cosine similarity. This approach enables semantic search beyond simple keyword matching, finding documents that are conceptually related even if they don't share exact terms.",
  "relevant_documents": [
    {
      "document_id": "abc12345-e89b-12d3-a456-426614174000",
      "content": "Vector similarity search is a technique used to find documents or text chunks that are semantically similar to a query. It works by converting text into high-dimensional vector embeddings using models like Sentence Transformers, then using efficient algorithms to find vectors that are close to each other in the vector space.",
      "similarity_score": 0.92
    },
    {
      "document_id": "def67890-e89b-12d3-a456-426614174000",
      "content": "FAISS (Facebook AI Similarity Search) is a library that enables efficient similarity search and clustering of dense vectors. It contains algorithms that search in sets of vectors of any size, up to ones that possibly do not fit in RAM.",
      "similarity_score": 0.85
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Query processed successfully
- `400 Bad Request`: Invalid query parameters
- `422 Unprocessable Entity`: Query validation failed

**Notes:**
- `max_results` is optional (default: 5) and specifies the maximum number of relevant documents to return
- `similarity_threshold` is optional (default: 0.7) and specifies the minimum similarity score for included documents
- If authenticated, the query and response will be stored in the user's history
- Anonymous queries are still processed but not stored for future reference

#### Example Request

```bash
curl -X POST "https://api.example.com/api/v1/query/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{"query_text": "How does vector similarity search work?", "max_results": 5}'
```

#### Example Response

```json
{
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "query_text": "How does vector similarity search work?",
  "response_text": "Vector similarity search works by converting text into numerical vector representations (embeddings) that capture semantic meaning. These vectors are stored in a specialized database like FAISS. When a query is submitted, it's also converted to a vector, and the system finds documents with vectors most similar to the query vector using distance metrics like cosine similarity. This approach enables semantic search beyond simple keyword matching, finding documents that are conceptually related even if they don't share exact terms.",
  "relevant_documents": [
    {
      "document_id": "abc12345-e89b-12d3-a456-426614174000",
      "content": "Vector similarity search is a technique used to find documents or text chunks that are semantically similar to a query. It works by converting text into high-dimensional vector embeddings using models like Sentence Transformers, then using efficient algorithms to find vectors that are close to each other in the vector space.",
      "similarity_score": 0.92
    },
    {
      "document_id": "def67890-e89b-12d3-a456-426614174000",
      "content": "FAISS (Facebook AI Similarity Search) is a library that enables efficient similarity search and clustering of dense vectors. It contains algorithms that search in sets of vectors of any size, up to ones that possibly do not fit in RAM.",
      "similarity_score": 0.85
    }
  ]
}
```

### Get Query by ID

**GET /api/v1/query/{query_id}**

Retrieve a specific query and its response by ID.

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `query_id`: UUID of the query

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "789e4567-e89b-12d3-a456-426614174000",
  "query_text": "How does vector similarity search work?",
  "query_time": "2023-06-15T14:30:00Z",
  "response_text": "Vector similarity search works by converting text into numerical vector representations (embeddings) that capture semantic meaning. These vectors are stored in a specialized database like FAISS. When a query is submitted, it's also converted to a vector, and the system finds documents with vectors most similar to the query vector using distance metrics like cosine similarity. This approach enables semantic search beyond simple keyword matching, finding documents that are conceptually related even if they don't share exact terms."
}
```

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have access to this query
- `404 Not Found`: Query not found

#### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/query/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Get Query with Feedback

**GET /api/v1/query/{query_id}/feedback**

Retrieve a specific query along with its associated feedback.

**Request:**
- Authorization: Bearer {access_token}

**Path Parameters:**
- `query_id`: UUID of the query

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "789e4567-e89b-12d3-a456-426614174000",
  "query_text": "How does vector similarity search work?",
  "query_time": "2023-06-15T14:30:00Z",
  "response_text": "Vector similarity search works by converting text into numerical vector representations (embeddings) that capture semantic meaning. These vectors are stored in a specialized database like FAISS. When a query is submitted, it's also converted to a vector, and the system finds documents with vectors most similar to the query vector using distance metrics like cosine similarity. This approach enables semantic search beyond simple keyword matching, finding documents that are conceptually related even if they don't share exact terms.",
  "feedback": [
    {
      "rating": 4,
      "comments": "Good response, but could include more specific examples."
    },
    {
      "rating": 5,
      "comments": "Excellent explanation!"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User does not have access to this query
- `404 Not Found`: Query not found

#### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/query/123e4567-e89b-12d3-a456-426614174000/feedback" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### List Queries

**GET /api/v1/query/**

List queries with pagination and optional filtering.

**Request:**
- Authorization: Bearer {access_token}

**Query Parameters:**
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100)
- `search_term`: Optional search term to filter queries

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "789e4567-e89b-12d3-a456-426614174000",
    "query_text": "How does vector similarity search work?",
    "query_time": "2023-06-15T14:30:00Z",
    "response_text": "Vector similarity search works by converting text into numerical vector representations..."
  },
  {
    "id": "456e4567-e89b-12d3-a456-426614174000",
    "user_id": "789e4567-e89b-12d3-a456-426614174000",
    "query_text": "What is the difference between FAISS and Elasticsearch?",
    "query_time": "2023-06-16T09:15:00Z",
    "response_text": "FAISS and Elasticsearch are both search systems but serve different purposes..."
  }
]
```

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication

**Notes:**
- Admin users can see all queries
- Regular users can only see their own queries
- The `search_term` parameter searches within query text

#### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/query/?limit=10&search_term=vector" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### List User Queries

**GET /api/v1/query/me**

List queries for the current authenticated user with pagination.

**Request:**
- Authorization: Bearer {access_token}

**Query Parameters:**
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100)

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "789e4567-e89b-12d3-a456-426614174000",
    "query_text": "How does vector similarity search work?",
    "query_time": "2023-06-15T14:30:00Z",
    "response_text": "Vector similarity search works by converting text into numerical vector representations..."
  },
  {
    "id": "456e4567-e89b-12d3-a456-426614174000",
    "user_id": "789e4567-e89b-12d3-a456-426614174000",
    "query_text": "What is the difference between FAISS and Elasticsearch?",
    "query_time": "2023-06-16T09:15:00Z",
    "response_text": "FAISS and Elasticsearch are both search systems but serve different purposes..."
  }
]
```

**Status Codes:**
- `200 OK`: Request successful
- `401 Unauthorized`: Missing or invalid authentication

#### Example Request

```bash
curl -X GET "https://api.example.com/api/v1/query/me?limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Query Data Models

The following data models are used in the Query API:

### QueryCreate

```json
{
  "query_text": "string",
  "max_results": "integer (optional, default: 5)",
  "similarity_threshold": "float (optional, default: 0.7)"
}
```

### QueryResponse

```json
{
  "query_id": "UUID",
  "query_text": "string",
  "response_text": "string",
  "relevant_documents": [
    {
      "document_id": "UUID",
      "content": "string",
      "similarity_score": "float"
    }
  ]
}
```

### Query

```json
{
  "id": "UUID",
  "user_id": "UUID",
  "query_text": "string",
  "query_time": "datetime",
  "response_text": "string"
}
```

### QueryWithFeedback

```json
{
  "id": "UUID",
  "user_id": "UUID",
  "query_text": "string",
  "query_time": "datetime",
  "response_text": "string",
  "feedback": [
    {
      "rating": "integer (1-5)",
      "comments": "string (optional)"
    }
  ]
}
```

### QueryFilter

```json
{
  "user_id": "UUID (optional)",
  "start_date": "datetime (optional)",
  "end_date": "datetime (optional)",
  "search_term": "string (optional)"
}
```

## Error Handling

The Query API uses standard HTTP status codes and returns error details in a consistent format:

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters or body
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Authenticated user does not have permission for the requested operation
- `404 Not Found`: Requested resource does not exist
- `422 Unprocessable Entity`: Request validation error
- `500 Internal Server Error`: Server-side error

### Validation Errors

- Query text must be between 3 and 1000 characters
- Max results must be a positive integer
- Similarity threshold must be between 0 and 1

## Implementation Examples

Code examples for common query operations:

### Submit Query Example (JavaScript)

```javascript
async function submitQuery(queryText, maxResults = 5, accessToken = null) {
  const headers = {
    'Content-Type': 'application/json'
  };
  
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }
  
  const response = await fetch('/api/v1/query/', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      query_text: queryText,
      max_results: maxResults
    })
  });

  if (!response.ok) {
    throw new Error(`Query submission failed: ${response.status}`);
  }

  return await response.json();
}
```

### Get User Queries Example (JavaScript)

```javascript
async function getUserQueries(accessToken, skip = 0, limit = 100) {
  const response = await fetch(`/api/v1/query/me?skip=${skip}&limit=${limit}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to get user queries: ${response.status}`);
  }

  return await response.json();
}
```

### Get Query with Feedback Example (JavaScript)

```javascript
async function getQueryWithFeedback(queryId, accessToken) {
  const response = await fetch(`/api/v1/query/${queryId}/feedback`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to get query with feedback: ${response.status}`);
  }

  return await response.json();
}
```

## Vector Search Process

The query processing workflow involves several steps to generate relevant responses:

### Query Processing Workflow

1. **Query Submission**: User submits a natural language query
2. **Vector Embedding**: The query is converted to a vector embedding
3. **Similarity Search**: The system searches for document chunks with similar vector embeddings
4. **Context Preparation**: Relevant document chunks are combined to create context
5. **Response Generation**: The LLM generates a response based on the query and context
6. **Result Storage**: The query and response are stored for authenticated users

### Vector Similarity Search

The system uses FAISS (Facebook AI Similarity Search) to efficiently find document chunks that are semantically similar to the query. The similarity is measured using cosine similarity between vector embeddings, with higher scores indicating greater relevance.

The `similarity_threshold` parameter (default: 0.7) determines the minimum similarity score for a document chunk to be included in the results. The `max_results` parameter (default: 5) limits the number of document chunks returned.

### Response Generation

The system uses a language model to generate a coherent response based on the query and the content of the most relevant document chunks. The response is designed to directly answer the user's question using information from the documents.

The system is instructed to:
- Only use information from the provided document context
- Indicate when it doesn't have enough information to answer
- Provide specific references to the documents used

## Providing Feedback

Users can provide feedback on query responses to help improve the system:

### Feedback Process

1. Submit a query and receive a response
2. Evaluate the quality and relevance of the response
3. Submit feedback with a rating and optional comments
4. The system uses this feedback for reinforcement learning

You can submit feedback on query responses through the dedicated feedback endpoints in the API.

### Feedback Integration Example

```javascript
async function queryAndProvideFeedback(queryText, accessToken) {
  // Submit query
  const queryResponse = await submitQuery(queryText, 5, accessToken);
  
  // Display response to user
  displayResponse(queryResponse);
  
  // Collect user feedback
  const rating = await getUserRating();
  const comments = await getUserComments();
  
  // Submit feedback
  await submitFeedback(queryResponse.query_id, rating, comments, accessToken);
}
```

## Rate Limiting

The Query API implements rate limiting to prevent abuse and ensure fair resource allocation:

### Rate Limits

- Anonymous users: 10 queries per minute
- Authenticated users: 60 queries per minute
- Admin users: 120 queries per minute

### Rate Limit Headers

The API includes rate limit information in response headers:

- `X-RateLimit-Limit`: Maximum number of requests allowed per minute
- `X-RateLimit-Remaining`: Number of requests remaining in the current window
- `X-RateLimit-Reset`: Time in seconds until the rate limit resets

### Rate Limit Exceeded

When a rate limit is exceeded, the API returns a 429 Too Many Requests response with a Retry-After header indicating when the client can retry the request.

## Related Documentation

Additional resources for working with the Query API:

### References

- [Authentication API](./authentication.md) - Authentication and authorization for API access
- Feedback API - For providing feedback on query responses
- [OpenAPI Specification](./openapi.json) - Complete API specification including query endpoints