# API Integration Guide

## Introduction

This guide provides comprehensive information for developers who want to integrate with the Document Management and AI Chatbot System API. The system offers a RESTful API that enables programmatic access to document management, vector search, and AI-powered response generation capabilities.

The API is designed to be easy to use, well-documented, and follows standard REST conventions. All endpoints return JSON responses (except for binary file downloads) and use standard HTTP status codes to indicate success or failure.

### API Overview

The Document Management and AI Chatbot System API is organized into the following main areas:

- **Authentication**: Endpoints for user authentication, token management, and registration
- **Document Management**: Endpoints for uploading, retrieving, listing, and deleting documents
- **Query Processing**: Endpoints for submitting search queries and retrieving AI-generated responses
- **Feedback Collection**: Endpoints for submitting feedback on responses and triggering reinforcement learning
- **Health Checks**: Endpoints for monitoring system health and status

All API endpoints are prefixed with `/api/v1/` to indicate the API version. This versioning approach allows for future API enhancements while maintaining backward compatibility.

### API Base URL

The base URL for all API requests depends on your deployment environment. For example:

- Development: `http://localhost:8000/api/v1`
- Production: `https://your-domain.com/api/v1`

All examples in this guide use relative paths that should be appended to the appropriate base URL for your environment.

## Authentication

### Authentication Overview

The API uses JWT (JSON Web Token) based authentication to secure access. To use most API endpoints, you'll need to:

1. Obtain an access token by authenticating with username and password
2. Include the access token in the Authorization header of subsequent requests
3. Refresh the access token when it expires using a refresh token

For detailed information about the authentication system, see the [Authentication API documentation](../api/authentication.md).

### Obtaining Access Tokens

To obtain an access token, make a POST request to the `/auth/token` endpoint with your credentials:

```javascript
async function login(username, password) {
  try {
    const response = await axios.post('/auth/token', {
      username: username,
      password: password
    });
    
    return response.data; // Contains access_token, token_type, and refresh_token
  } catch (error) {
    console.error('Authentication failed:', error.response?.data || error.message);
    throw error;
  }
}
```

The response will include:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Store these tokens securely in your application. The access token is short-lived (60 minutes) while the refresh token has a longer lifetime (7 days).

### Using Access Tokens

Include the access token in the Authorization header of all API requests that require authentication:

```javascript
async function makeAuthenticatedRequest(endpoint, method = 'GET', data = null) {
  try {
    const response = await axios({
      url: endpoint,
      method: method,
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      data: data
    });
    
    return response.data;
  } catch (error) {
    // Handle authentication errors
    if (error.response?.status === 401) {
      // Token expired or invalid, try to refresh
      await refreshAccessToken();
      // Retry the request with the new token
      return makeAuthenticatedRequest(endpoint, method, data);
    }
    
    console.error('Request failed:', error.response?.data || error.message);
    throw error;
  }
}
```

### Refreshing Access Tokens

When an access token expires, you'll receive a 401 Unauthorized response. Use the refresh token to obtain a new access token:

```javascript
async function refreshAccessToken() {
  try {
    const response = await axios.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    
    // Update stored tokens
    accessToken = response.data.access_token;
    refreshToken = response.data.refresh_token;
    
    return response.data;
  } catch (error) {
    console.error('Token refresh failed:', error.response?.data || error.message);
    // If refresh fails, redirect to login
    redirectToLogin();
    throw error;
  }
}
```

Implement token refresh logic to handle expired tokens gracefully without disrupting the user experience.

### Token Management

Implement these best practices for token management:

1. **Store tokens securely**:
   - For web applications: Use HTTP-only cookies for refresh tokens and memory/session storage for access tokens
   - For mobile applications: Use secure storage mechanisms provided by the platform

2. **Handle token expiration**:
   - Implement automatic token refresh when access tokens expire
   - Include error handling for failed refresh attempts

3. **Implement logout**:
   - Revoke refresh tokens on logout by calling the `/auth/logout` endpoint
   - Clear stored tokens from client storage

```javascript
async function logout() {
  try {
    await axios.post('/auth/logout', {
      refresh_token: refreshToken
    });
    
    // Clear stored tokens
    accessToken = null;
    refreshToken = null;
    
    // Redirect to login page
    redirectToLogin();
  } catch (error) {
    console.error('Logout failed:', error.response?.data || error.message);
    // Clear tokens anyway
    accessToken = null;
    refreshToken = null;
    redirectToLogin();
  }
}
```

## Document Management

### Document Management Overview

The Document Management API allows you to upload PDF documents, retrieve document metadata, download original documents, and manage the document lifecycle. For detailed information, see the [Document API documentation](../api/documents.md).

### Uploading Documents

To upload a document, make a POST request to the `/documents/` endpoint with the file as multipart/form-data:

```javascript
async function uploadDocument(file, title = null) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }
    
    const response = await axios.post('/documents/', formData, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Document upload failed:', error.response?.data || error.message);
    throw error;
  }
}
```

The response will include the document metadata with a status of 'processing'. The system will process the document asynchronously, extracting text and generating vector embeddings.

### Checking Document Status

After uploading a document, you can check its processing status by retrieving the document metadata:

```javascript
async function getDocument(documentId) {
  try {
    const response = await axios.get(`/documents/${documentId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get document:', error.response?.data || error.message);
    throw error;
  }
}
```

The document status will be one of:
- 'processing': Document is being processed
- 'available': Document has been successfully processed and is available for search
- 'error': An error occurred during processing
- 'deleted': Document has been deleted

### Listing Documents

To retrieve a list of documents with optional filtering and pagination:

```javascript
async function listDocuments(filters = {}, skip = 0, limit = 100) {
  try {
    const queryParams = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
      ...filters
    });
    
    const response = await axios.get(`/documents/?${queryParams}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to list documents:', error.response?.data || error.message);
    throw error;
  }
}
```

Available filter parameters include:
- `title`: Filter by document title (substring match)
- `status`: Filter by document status
- `upload_date_from`: Filter by upload date (from)
- `upload_date_to`: Filter by upload date (to)

### Downloading Documents

To download the original document file:

```javascript
async function downloadDocument(documentId) {
  try {
    const response = await axios.get(`/documents/${documentId}/download`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      responseType: 'blob'
    });
    
    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', response.headers['content-disposition']?.split('filename=')[1]?.replace(/\"/g, '') || 'document.pdf');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return true;
  } catch (error) {
    console.error('Document download failed:', error.response?.data || error.message);
    throw error;
  }
}
```

### Deleting Documents

To delete a document (soft delete):

```javascript
async function deleteDocument(documentId) {
  try {
    const response = await axios.delete(`/documents/${documentId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Document deletion failed:', error.response?.data || error.message);
    throw error;
  }
}
```

This performs a soft delete, which means the document will be marked as deleted but remains in the database. It will no longer appear in search results or document listings (unless specifically filtered for deleted documents).

### Retrieving Document Chunks

To retrieve a document with its text chunks:

```javascript
async function getDocumentWithChunks(documentId) {
  try {
    const response = await axios.get(`/documents/${documentId}/chunks`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get document chunks:', error.response?.data || error.message);
    throw error;
  }
}
```

This is useful for understanding how the document has been processed and split into chunks for vector search.

## Query Processing

### Query Processing Overview

The Query API allows you to submit natural language queries and receive AI-generated responses based on the content of documents stored in the system. For detailed information, see the [Query API documentation](../api/query.md).

### Submitting Queries

To submit a search query and receive an AI-generated response:

```javascript
async function submitQuery(queryText, maxResults = 5, similarityThreshold = 0.7) {
  try {
    const response = await axios.post('/query/', {
      query_text: queryText,
      max_results: maxResults,
      similarity_threshold: similarityThreshold
    }, {
      headers: {
        'Authorization': `Bearer ${accessToken}` // Optional for this endpoint
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Query submission failed:', error.response?.data || error.message);
    throw error;
  }
}
```

The response will include:
- The query ID and text
- An AI-generated response based on relevant documents
- A list of relevant document chunks with similarity scores

Note that authentication is optional for the query endpoint, allowing anonymous users to submit queries. However, authenticated queries are stored in the user's history and can be retrieved later.

### Retrieving Query History

To retrieve a list of previous queries for the authenticated user:

```javascript
async function getUserQueries(skip = 0, limit = 100) {
  try {
    const response = await axios.get(`/query/me?skip=${skip}&limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get user queries:', error.response?.data || error.message);
    throw error;
  }
}
```

This endpoint returns a list of the user's previous queries with their responses.

### Retrieving a Specific Query

To retrieve a specific query by ID:

```javascript
async function getQuery(queryId) {
  try {
    const response = await axios.get(`/query/${queryId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get query:', error.response?.data || error.message);
    throw error;
  }
}
```

This is useful for retrieving the details of a previously submitted query.

### Retrieving Query with Feedback

To retrieve a query along with its associated feedback:

```javascript
async function getQueryWithFeedback(queryId) {
  try {
    const response = await axios.get(`/query/${queryId}/feedback`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get query with feedback:', error.response?.data || error.message);
    throw error;
  }
}
```

This endpoint returns the query details along with any feedback that has been submitted for it.

### Optimizing Query Results

To get the best results from the query API:

1. **Formulate clear, specific queries**: The system works best with well-formed natural language questions rather than keywords.

2. **Adjust max_results**: Increase this parameter to get more context from documents, or decrease it to focus on the most relevant content.

3. **Tune similarity_threshold**: Lower this value (e.g., 0.5) to include more diverse results, or increase it (e.g., 0.8) to focus on highly relevant matches only.

4. **Provide feedback**: Submit feedback on responses to help improve the system over time.

## Feedback Collection

### Feedback Collection Overview

The Feedback API allows users to provide ratings and comments on AI-generated responses. This feedback is used to improve response quality through reinforcement learning. For detailed information, see the [Feedback API documentation](../api/feedback.md).

### Submitting Feedback

To submit feedback for a query response:

```javascript
async function submitFeedback(queryId, rating, comments = '') {
  try {
    const response = await axios.post('/feedback/', {
      query_id: queryId,
      rating: rating, // Integer from 1 to 5
      comments: comments // Optional
    }, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Feedback submission failed:', error.response?.data || error.message);
    throw error;
  }
}
```

The rating should be an integer from 1 to 5, where:
- 1: Poor - Response was not helpful or relevant
- 2: Fair - Response had some relevant information but was mostly unhelpful
- 3: Average - Response was moderately helpful
- 4: Good - Response was helpful and mostly relevant
- 5: Excellent - Response was very helpful and highly relevant

The comments field is optional but provides valuable qualitative feedback.

### Retrieving User Feedback

To retrieve all feedback submitted by the current user:

```javascript
async function getUserFeedback(skip = 0, limit = 100) {
  try {
    const response = await axios.get(`/feedback/user/me?skip=${skip}&limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get user feedback:', error.response?.data || error.message);
    throw error;
  }
}
```

This endpoint returns a list of feedback submitted by the current user.

### Retrieving Feedback for a Query

To retrieve all feedback for a specific query:

```javascript
async function getFeedbackByQuery(queryId) {
  try {
    const response = await axios.get(`/feedback/query/${queryId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get feedback for query:', error.response?.data || error.message);
    throw error;
  }
}
```

This is useful for retrieving all feedback submitted for a particular query.

### Feedback Statistics

For administrators, the API provides endpoints to retrieve feedback statistics:

```javascript
async function getFeedbackStatistics(filters = {}) {
  try {
    const response = await axios.post('/feedback/statistics', filters, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to get feedback statistics:', error.response?.data || error.message);
    throw error;
  }
}
```

This endpoint returns statistics such as average rating, rating distribution, and percentages of positive, neutral, and negative feedback.

### Triggering Reinforcement Learning

Administrators can trigger the reinforcement learning process manually:

```javascript
async function triggerReinforcementLearning() {
  try {
    const response = await axios.post('/feedback/reinforce', {}, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to trigger reinforcement learning:', error.response?.data || error.message);
    throw error;
  }
}
```

This process analyzes accumulated feedback and updates the response generation parameters to improve future responses. The system also runs this process automatically on a scheduled basis.

## Error Handling

### Error Response Format

The API returns errors in a consistent format:

```json
{
  "detail": "Error message describing the issue"
}
```

All error responses include appropriate HTTP status codes to indicate the type of error.

### Common Error Codes

| Status Code | Description | Common Causes |
| --- | --- | --- |
| 400 Bad Request | Invalid request parameters or body | Malformed JSON, invalid parameters |
| 401 Unauthorized | Missing or invalid authentication | Expired token, missing token |
| 403 Forbidden | Insufficient permissions | Attempting to access unauthorized resources |
| 404 Not Found | Resource not found | Invalid ID, deleted resource |
| 413 Payload Too Large | Request body too large | Document exceeds size limit |
| 415 Unsupported Media Type | Unsupported content type | Non-PDF document upload |
| 422 Unprocessable Entity | Request validation error | Invalid data format, business rule violation |
| 429 Too Many Requests | Rate limit exceeded | Too many requests in a short period |
| 500 Internal Server Error | Server-side error | Unexpected server issues |

### Handling Authentication Errors

For 401 Unauthorized errors, implement token refresh logic:

```javascript
async function handleAuthError(error, retryFunction, ...args) {
  if (error.response?.status === 401) {
    try {
      // Try to refresh the token
      await refreshAccessToken();
      // Retry the original request with the new token
      return await retryFunction(...args);
    } catch (refreshError) {
      // If refresh fails, redirect to login
      redirectToLogin();
      throw refreshError;
    }
  }
  
  // For other errors, just throw them
  throw error;
}
```

Use this function to wrap API calls that might return authentication errors.

### Validation Errors

For 400 Bad Request and 422 Unprocessable Entity errors, extract and display the validation details:

```javascript
function handleValidationError(error) {
  if (error.response?.status === 400 || error.response?.status === 422) {
    const errorDetail = error.response.data.detail;
    
    // Display validation errors to the user
    displayValidationErrors(errorDetail);
  } else {
    // Handle other errors
    handleGenericError(error);
  }
}
```

### Rate Limiting

The API implements rate limiting to prevent abuse. When you exceed the rate limit, you'll receive a 429 Too Many Requests response with a Retry-After header indicating when you can retry the request.

```javascript
async function handleRateLimitError(error, retryFunction, ...args) {
  if (error.response?.status === 429) {
    const retryAfter = error.response.headers['retry-after'] || 60;
    
    // Notify the user
    notifyUser(`Rate limit exceeded. Retrying in ${retryAfter} seconds.`);
    
    // Wait for the specified time
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    
    // Retry the request
    return await retryFunction(...args);
  }
  
  // For other errors, just throw them
  throw error;
}
```

## Best Practices

### API Client Implementation

Implement a reusable API client that handles common concerns:

```javascript
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.accessToken = null;
    this.refreshToken = null;
    
    // Create axios instance with defaults
    this.axios = axios.create({
      baseURL: baseUrl,
      timeout: 30000 // 30 seconds
    });
    
    // Add response interceptor for token handling
    this.axios.interceptors.response.use(
      response => response,
      async error => {
        const originalRequest = error.config;
        
        // If the error is due to an expired token and we haven't tried to refresh yet
        if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
          originalRequest._retry = true;
          
          try {
            // Try to refresh the token
            await this.refreshAccessToken();
            
            // Update the authorization header
            originalRequest.headers['Authorization'] = `Bearer ${this.accessToken}`;
            
            // Retry the original request
            return this.axios(originalRequest);
          } catch (refreshError) {
            // If refresh fails, clear tokens and reject
            this.clearTokens();
            return Promise.reject(refreshError);
          }
        }
        
        // For other errors, just reject
        return Promise.reject(error);
      }
    );
  }
  
  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }
  
  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
  }
  
  async login(username, password) {
    const response = await this.axios.post('/auth/token', {
      username,
      password
    });
    
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }
  
  async refreshAccessToken() {
    const response = await this.axios.post('/auth/refresh', {
      refresh_token: this.refreshToken
    });
    
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  }
  
  async logout() {
    if (!this.refreshToken) return;
    
    try {
      await this.axios.post('/auth/logout', {
        refresh_token: this.refreshToken
      });
    } finally {
      this.clearTokens();
    }
  }
  
  async request(method, endpoint, data = null, config = {}) {
    const requestConfig = {
      ...config,
      method,
      url: endpoint
    };
    
    if (data) {
      requestConfig.data = data;
    }
    
    if (this.accessToken) {
      requestConfig.headers = {
        ...requestConfig.headers,
        'Authorization': `Bearer ${this.accessToken}`
      };
    }
    
    return this.axios(requestConfig);
  }
  
  // Convenience methods
  async get(endpoint, config = {}) {
    return this.request('GET', endpoint, null, config);
  }
  
  async post(endpoint, data, config = {}) {
    return this.request('POST', endpoint, data, config);
  }
  
  async put(endpoint, data, config = {}) {
    return this.request('PUT', endpoint, data, config);
  }
  
  async delete(endpoint, config = {}) {
    return this.request('DELETE', endpoint, null, config);
  }
}
```

This client handles token management, request/response processing, and error handling in a reusable way.

### Caching Strategies

Implement caching for appropriate endpoints to improve performance and reduce API calls:

1. **Document Metadata**: Cache document metadata to avoid repeated requests
2. **Query Results**: Cache query results for frequently asked questions
3. **User Information**: Cache user profile and permissions

```javascript
class CacheManager {
  constructor(ttl = 300000) { // Default TTL: 5 minutes
    this.cache = {};
    this.defaultTtl = ttl;
  }
  
  set(key, value, ttl = this.defaultTtl) {
    const item = {
      value,
      expiry: Date.now() + ttl
    };
    
    this.cache[key] = item;
    return value;
  }
  
  get(key) {
    const item = this.cache[key];
    
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
      delete this.cache[key];
      return null;
    }
    
    return item.value;
  }
  
  invalidate(key) {
    delete this.cache[key];
  }
  
  clear() {
    this.cache = {};
  }
}

// Usage example
const cache = new CacheManager();

async function getDocumentWithCache(documentId) {
  const cacheKey = `document:${documentId}`;
  const cachedDocument = cache.get(cacheKey);
  
  if (cachedDocument) {
    return cachedDocument;
  }
  
  const document = await apiClient.get(`/documents/${documentId}`);
  cache.set(cacheKey, document.data);
  
  return document.data;
}
```

Invalidate cache entries when the underlying data changes (e.g., after document updates or deletions).

### Rate Limit Handling

Implement rate limit handling to avoid disruptions:

1. **Respect Rate Limits**: Monitor the rate limit headers in API responses
2. **Implement Backoff**: Use exponential backoff for retries
3. **Queue Requests**: In high-volume scenarios, queue requests to stay within limits

```javascript
class RateLimitHandler {
  constructor(maxRetries = 3) {
    this.maxRetries = maxRetries;
  }
  
  async executeWithRetry(requestFn, ...args) {
    let retries = 0;
    
    while (retries <= this.maxRetries) {
      try {
        return await requestFn(...args);
      } catch (error) {
        if (error.response?.status === 429 && retries < this.maxRetries) {
          retries++;
          
          // Get retry-after header or use exponential backoff
          const retryAfter = parseInt(error.response.headers['retry-after']) || Math.pow(2, retries) * 1000;
          
          console.log(`Rate limited. Retrying in ${retryAfter/1000} seconds (attempt ${retries}/${this.maxRetries})`);
          
          // Wait for the specified time
          await new Promise(resolve => setTimeout(resolve, retryAfter));
        } else {
          // If it's not a rate limit error or we've exceeded max retries
          throw error;
        }
      }
    }
  }
}

// Usage example
const rateLimitHandler = new RateLimitHandler();

async function submitQueryWithRetry(queryText) {
  return rateLimitHandler.executeWithRetry(
    apiClient.post.bind(apiClient),
    '/query/',
    { query_text: queryText }
  );
}
```

### Error Handling and Logging

Implement comprehensive error handling and logging:

1. **Centralized Error Handling**: Process all API errors consistently
2. **Detailed Logging**: Log request/response details for troubleshooting
3. **User-Friendly Messages**: Translate technical errors into user-friendly messages

```javascript
class ErrorHandler {
  constructor(logger) {
    this.logger = logger;
  }
  
  handleError(error, context = {}) {
    // Extract error details
    const errorDetails = {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      context
    };
    
    // Log the error
    this.logger.error('API Error', errorDetails);
    
    // Generate user-friendly message
    const userMessage = this.getUserFriendlyMessage(error);
    
    return {
      userMessage,
      technicalDetails: errorDetails
    };
  }
  
  getUserFriendlyMessage(error) {
    const status = error.response?.status;
    
    switch (status) {
      case 400:
        return 'The request contains invalid parameters. Please check your input and try again.';
      case 401:
        return 'Your session has expired. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 413:
        return 'The file you are trying to upload is too large.';
      case 415:
        return 'The file format is not supported. Please upload a PDF file.';
      case 422:
        return 'The request could not be processed. Please check your input and try again.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'A server error occurred. Please try again later or contact support if the problem persists.';
      default:
        return 'An unexpected error occurred. Please try again or contact support.';
    }
  }
}
```

### Batch Operations

For operations involving multiple documents or queries, implement batch processing to reduce API calls:

```javascript
async function batchUploadDocuments(files, progressCallback) {
  const results = {
    successful: [],
    failed: []
  };
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    
    try {
      // Update progress
      if (progressCallback) {
        progressCallback(i, files.length, file.name);
      }
      
      // Upload document
      const response = await apiClient.post('/documents/', {
        file
      }, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      results.successful.push({
        file: file.name,
        document: response.data
      });
    } catch (error) {
      results.failed.push({
        file: file.name,
        error: error.response?.data || error.message
      });
    }
  }
  
  return results;
}
```

This approach provides better error handling and progress tracking for batch operations.

## API Reference

### API Documentation

For detailed API documentation, refer to the following resources:

- [Authentication API](../api/authentication.md): User authentication and token management
- [Document API](../api/documents.md): Document upload, retrieval, and management
- [Query API](../api/query.md): Search queries and AI-powered responses
- [Feedback API](../api/feedback.md): Feedback submission and reinforcement learning
- [OpenAPI Specification](../api/openapi.json): Complete API specification in OpenAPI format

### OpenAPI Specification

The API is documented using the OpenAPI Specification (formerly Swagger). You can use this specification to generate client libraries, explore the API, and understand the available endpoints.

The OpenAPI specification is available at `/api/v1/docs/openapi.json` and can be viewed using Swagger UI at `/api/v1/docs`.

### API Versioning

The API uses URI-based versioning with the format `/api/v{version_number}/`. The current version is v1.

When new versions are released, older versions will be maintained for a transition period to allow clients to migrate. Deprecation notices will be provided in the API documentation and response headers.

### Rate Limits

The API implements the following rate limits:

| Client Type | Rate Limit | Timeframe |
| --- | --- | --- |
| Anonymous | 10 requests | Per minute |
| Authenticated | 60 requests | Per minute |
| Admin | 120 requests | Per minute |

Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: Maximum number of requests allowed per minute
- `X-RateLimit-Remaining`: Number of requests remaining in the current window
- `X-RateLimit-Reset`: Time in seconds until the rate limit resets

## Sample Applications

### Basic Integration Example

Here's a simple example of integrating with the API using JavaScript:

```javascript
// Initialize API client
const apiClient = new ApiClient('https://api.example.com/api/v1');

// Login and store tokens
async function login(username, password) {
  try {
    const tokenData = await apiClient.login(username, password);
    localStorage.setItem('refreshToken', tokenData.refresh_token);
    return true;
  } catch (error) {
    console.error('Login failed:', error);
    return false;
  }
}

// Initialize from stored refresh token
async function initializeFromStoredToken() {
  const refreshToken = localStorage.getItem('refreshToken');
  
  if (!refreshToken) return false;
  
  try {
    apiClient.setTokens(null, refreshToken);
    await apiClient.refreshAccessToken();
    return true;
  } catch (error) {
    console.error('Token refresh failed:', error);
    localStorage.removeItem('refreshToken');
    return false;
  }
}

// Document search and query
async function searchDocuments(query) {
  try {
    const response = await apiClient.post('/query/', {
      query_text: query
    });
    
    return response.data;
  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
}

// Document upload
async function uploadDocument(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
}

// Submit feedback
async function submitFeedback(queryId, rating, comments = '') {
  try {
    const response = await apiClient.post('/feedback/', {
      query_id: queryId,
      rating: rating,
      comments: comments
    });
    
    return response.data;
  } catch (error) {
    console.error('Feedback submission failed:', error);
    throw error;
  }
}

// Logout
async function logout() {
  try {
    await apiClient.logout();
    localStorage.removeItem('refreshToken');
    return true;
  } catch (error) {
    console.error('Logout failed:', error);
    localStorage.removeItem('refreshToken');
    return false;
  }
}
```

### Complete Integration Example

For a complete integration example, refer to the sample applications in the repository:

- [JavaScript Client](https://github.com/example/document-ai-js-client): Web-based client using React
- [Python Client](https://github.com/example/document-ai-python-client): Command-line client using Python
- [Mobile Client](https://github.com/example/document-ai-mobile-client): Mobile application using React Native

These sample applications demonstrate best practices for API integration, error handling, and user experience.

## Troubleshooting

### Authentication Issues

**Issue**: Unable to obtain access token
**Solution**: Verify your credentials and ensure you're using the correct endpoint. Check for typos in username or password.

**Issue**: Token refresh fails
**Solution**: The refresh token may have expired or been revoked. Redirect the user to the login page to obtain a new token pair.

**Issue**: Unauthorized errors despite valid token
**Solution**: Check that the token is being correctly included in the Authorization header with the 'Bearer' prefix. Verify that the token hasn't expired.

### Document Upload Issues

**Issue**: Document upload fails with 413 Payload Too Large
**Solution**: Ensure the document is under the 10MB size limit. Consider compressing the PDF or splitting it into smaller documents.

**Issue**: Document upload fails with 415 Unsupported Media Type
**Solution**: Verify that you're uploading a valid PDF file. Check the file extension and content type.

**Issue**: Document status remains 'processing' for a long time
**Solution**: Large or complex documents may take longer to process. If the status doesn't change after several minutes, the document may be stuck in processing. Contact support with the document ID.

### Query Issues

**Issue**: Query returns no relevant documents
**Solution**: Try reformulating the query or lowering the similarity threshold. Ensure that relevant documents have been uploaded and processed successfully.

**Issue**: AI-generated responses are not relevant
**Solution**: Provide feedback on the response to help improve future responses. Ensure your query is clear and specific.

**Issue**: Query processing is slow
**Solution**: Complex queries or large document collections may take longer to process. Consider optimizing your query or filtering the document set.

### Rate Limiting

**Issue**: Receiving 429 Too Many Requests errors
**Solution**: Implement rate limit handling with exponential backoff. Reduce the frequency of requests or distribute them more evenly over time.

**Issue**: Rate limits are too restrictive for your use case
**Solution**: Contact support to discuss custom rate limits for your application.

### Common Error Codes

**400 Bad Request**: The request contains invalid parameters or malformed JSON. Check the request body and parameters.

**401 Unauthorized**: Authentication is required or the provided token is invalid. Obtain a new token or refresh the existing one.

**403 Forbidden**: The authenticated user doesn't have permission to access the requested resource. Check user roles and permissions.

**404 Not Found**: The requested resource doesn't exist. Verify the ID or path.

**422 Unprocessable Entity**: The request is well-formed but contains semantic errors. Check the validation rules for the endpoint.

**500 Internal Server Error**: An unexpected error occurred on the server. Retry the request or contact support if the issue persists.

## Support and Resources

### Documentation

- [API Reference](../api/): Detailed documentation for all API endpoints
- [User Guide](../user-guide/): Comprehensive guide for using the system
- [Developer Guide](../development/): Guide for developers working with the system
- [FAQ](../faq.md): Frequently asked questions about the system

### Support Channels

- **Email Support**: support@example.com
- **Issue Tracker**: https://github.com/example/document-ai-system/issues
- **Community Forum**: https://community.example.com
- **Office Hours**: Weekly developer office hours (Thursdays, 2-4 PM UTC)

### SDKs and Client Libraries

- [JavaScript SDK](https://github.com/example/document-ai-js-sdk): Official JavaScript client library
- [Python SDK](https://github.com/example/document-ai-python-sdk): Official Python client library
- [Java SDK](https://github.com/example/document-ai-java-sdk): Official Java client library
- [Community Libraries](https://github.com/example/document-ai-community): Community-maintained client libraries

### Stay Updated

- **Release Notes**: https://github.com/example/document-ai-system/releases
- **Developer Newsletter**: Subscribe at https://example.com/newsletter
- **API Status**: https://status.example.com
- **Roadmap**: https://github.com/example/document-ai-system/projects/1