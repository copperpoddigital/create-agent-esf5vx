# Feedback API

This document provides detailed information about the Feedback API endpoints in the Document Management and AI Chatbot System. These endpoints allow users to submit feedback on AI-generated responses, retrieve feedback data, and trigger reinforcement learning to improve response quality over time.

## Authentication

All feedback API endpoints require authentication using JWT tokens. See the [Authentication API](authentication.md) documentation for details on obtaining and using tokens.

## Base URL

All feedback endpoints are prefixed with `/api/v1/feedback`.

## Endpoints

### Submit Feedback

Submit feedback for a specific query response.

**POST /**

**Alternative Endpoint:** POST /submit

**Request Body:** FeedbackCreate schema
```json
{
  "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "rating": 4,
  "comments": "Very helpful response with relevant information"
}
```

**Response:** Feedback schema with HTTP 201 Created status
```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "rating": 4,
  "comments": "Very helpful response with relevant information",
  "feedback_time": "2023-06-15T14:30:00Z"
}
```

**Authorization:** Requires authentication

### Get Feedback by ID

Retrieve a specific feedback record by its ID.

**GET /{feedback_id}**

**Path Parameters:**
- `feedback_id` (UUID, required): ID of the feedback to retrieve

**Response:** Feedback schema
```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "rating": 4,
  "comments": "Very helpful response with relevant information",
  "feedback_time": "2023-06-15T14:30:00Z"
}
```

**Authorization:** Requires authentication (own feedback or admin role)

### Get Feedback by Query

Retrieve all feedback for a specific query.

**GET /query/{query_id}**

**Path Parameters:**
- `query_id` (UUID, required): ID of the query to retrieve feedback for

**Response:** Array of Feedback schema objects
```json
[
  {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rating": 4,
    "comments": "Very helpful response with relevant information",
    "feedback_time": "2023-06-15T14:30:00Z"
  },
  {
    "id": "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "user_id": "4fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rating": 3,
    "comments": "Somewhat helpful but missing some details",
    "feedback_time": "2023-06-15T15:45:00Z"
  }
]
```

**Authorization:** Requires authentication (admin or query owner)

### Get Current User's Feedback

Retrieve all feedback submitted by the current authenticated user.

**GET /user/me**

**Query Parameters:**
- `skip` (integer, optional, default: 0): Number of records to skip for pagination
- `limit` (integer, optional, default: 100): Maximum number of records to return

**Response:** Array of Feedback schema objects
```json
[
  {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rating": 4,
    "comments": "Very helpful response with relevant information",
    "feedback_time": "2023-06-15T14:30:00Z"
  },
  {
    "id": "8ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_id": "5fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rating": 5,
    "comments": "Excellent response, exactly what I needed",
    "feedback_time": "2023-06-16T10:15:00Z"
  }
]
```

**Authorization:** Requires authentication

### Filter Feedback

Retrieve feedback based on filter criteria.

**POST /filter**

**Request Body:** FeedbackFilter schema
```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "min_rating": 4,
  "start_date": "2023-06-01T00:00:00Z",
  "end_date": "2023-06-30T23:59:59Z"
}
```

**Query Parameters:**
- `skip` (integer, optional, default: 0): Number of records to skip for pagination
- `limit` (integer, optional, default: 100): Maximum number of records to return

**Response:** Array of Feedback schema objects
```json
[
  {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rating": 4,
    "comments": "Very helpful response with relevant information",
    "feedback_time": "2023-06-15T14:30:00Z"
  },
  {
    "id": "8ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query_id": "5fa85f64-5717-4562-b3fc-2c963f66afa6",
    "rating": 5,
    "comments": "Excellent response, exactly what I needed",
    "feedback_time": "2023-06-16T10:15:00Z"
  }
]
```

**Authorization:** Requires authentication (admin for all feedback, regular users for own feedback only)

### Get Feedback Statistics

Retrieve statistics for feedback based on filter criteria.

**POST /statistics**

**Request Body:** FeedbackFilter schema (optional)
```json
{
  "start_date": "2023-06-01T00:00:00Z",
  "end_date": "2023-06-30T23:59:59Z"
}
```

**Response:** FeedbackStats schema
```json
{
  "average_rating": 4.2,
  "total_feedback": 150,
  "rating_distribution": {
    "1": 5,
    "2": 10,
    "3": 25,
    "4": 60,
    "5": 50
  },
  "positive_percentage": 73.33,
  "negative_percentage": 10.0,
  "neutral_percentage": 16.67
}
```

**Authorization:** Requires authentication (admin for all statistics, regular users for own feedback statistics only)

### Trigger Reinforcement Learning

Trigger the reinforcement learning process based on accumulated feedback.

**POST /reinforce**

**Alternative Endpoint:** POST /reinforcement-learning

**Response:** Status object
```json
{
  "status": "success",
  "message": "Reinforcement learning process completed successfully",
  "processed_feedback": 150,
  "model_improvement": "Prompt templates updated based on feedback patterns"
}
```

**Authorization:** Requires authentication with admin role

## Data Models

### FeedbackCreate

Schema for submitting new feedback.

| Name | Type | Required | Description | Constraints |
| ---- | ---- | -------- | ----------- | ---------- |
| query_id | UUID | Yes | ID of the query being rated | |
| rating | integer | Yes | Rating value from 1 to 5 (1=poor, 5=excellent) | Value must be between 1 and 5 |
| comments | string | No | Optional comments about the response quality | |

### Feedback

Schema for feedback data returned by the API.

| Name | Type | Description |
| ---- | ---- | ----------- |
| id | UUID | Unique identifier for the feedback |
| user_id | UUID | ID of the user who submitted the feedback |
| query_id | UUID | ID of the query being rated |
| rating | integer | Rating value from 1 to 5 (1=poor, 5=excellent) |
| comments | string | Optional comments about the response quality |
| feedback_time | datetime | Timestamp when the feedback was submitted |

### FeedbackFilter

Schema for filtering feedback data.

| Name | Type | Required | Description | Constraints |
| ---- | ---- | -------- | ----------- | ---------- |
| user_id | UUID | No | Filter by user who submitted the feedback | |
| query_id | UUID | No | Filter by query ID | |
| start_date | datetime | No | Filter feedback submitted on or after this date | |
| end_date | datetime | No | Filter feedback submitted on or before this date | |
| min_rating | integer | No | Filter by minimum rating value | Value must be between 1 and 5 |
| max_rating | integer | No | Filter by maximum rating value | Value must be between 1 and 5 |

### FeedbackStats

Schema for feedback statistics.

| Name | Type | Description |
| ---- | ---- | ----------- |
| average_rating | float | Average rating value across all feedback |
| total_feedback | integer | Total number of feedback records |
| rating_distribution | object | Distribution of ratings (count for each rating value) |
| positive_percentage | float | Percentage of positive feedback (ratings 4-5) |
| negative_percentage | float | Percentage of negative feedback (ratings 1-2) |
| neutral_percentage | float | Percentage of neutral feedback (rating 3) |

## Error Responses

The API may return the following error responses:

### 401 Unauthorized

Returned when authentication is required but not provided or invalid.

### 403 Forbidden

Returned when the authenticated user does not have permission to access the requested resource.

### 404 Not Found

Returned when the requested feedback or query does not exist.

### 422 Unprocessable Entity

Returned when the request data fails validation (e.g., invalid rating value).

### 500 Internal Server Error

Returned when an unexpected error occurs on the server.

## Reinforcement Learning

The feedback system includes a reinforcement learning component that improves response quality over time based on user feedback. Administrators can trigger this process manually using the `/reinforce` endpoint, or it can run automatically on a scheduled basis.

### Learning Process

The reinforcement learning process analyzes feedback patterns, identifies successful and unsuccessful response strategies, and updates the response generation parameters accordingly. This helps the system generate better responses over time based on user preferences.

### Feedback Quality

To maximize the effectiveness of the reinforcement learning process, users are encouraged to provide detailed comments along with their ratings, especially for negative feedback. This helps the system understand what aspects of the responses need improvement.

## Rate Limiting

To prevent abuse, the feedback API endpoints are subject to rate limiting. Authenticated users can submit up to 60 requests per minute, while administrators have a higher limit of 120 requests per minute.

## See Also

- [Authentication API](authentication.md) - Details on obtaining and using JWT tokens
- [Query API](query.md) - Information about the query endpoints that generate responses which can be rated