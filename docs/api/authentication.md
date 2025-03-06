# Authentication API

## Authentication Overview

The Document Management and AI Chatbot System uses JWT (JSON Web Token) based authentication to secure API access. This stateless authentication mechanism provides secure, scalable access control with support for role-based permissions.

### Authentication Flow

1. Client submits credentials to obtain access and refresh tokens
2. Client includes access token in subsequent API requests
3. When access token expires, client uses refresh token to obtain new tokens
4. Client can explicitly logout by revoking refresh tokens

### Token Types

- **Access Token**: Short-lived token (60 minutes) used to authenticate API requests
- **Refresh Token**: Longer-lived token (7 days) used to obtain new access tokens without re-authentication

### Security Considerations

- Access tokens should be included in the Authorization header using the Bearer scheme
- Refresh tokens should be stored securely and transmitted only when needed
- All authentication endpoints use HTTPS to protect credentials and tokens

## Authentication Endpoints

The following endpoints are available for authentication operations:

### Login

**POST /auth/token**

Authenticate a user and obtain access and refresh tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "refresh_token": "string"
}
```

**Status Codes:**
- 200 OK: Authentication successful
- 401 Unauthorized: Invalid credentials
- 422 Unprocessable Entity: Invalid request format

#### Example Request

```bash
curl -X POST "https://api.example.com/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "securepassword"}'
```

#### Example Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Token Refresh

**POST /auth/refresh**

Refresh an expired access token using a valid refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "refresh_token": "string"
}
```

**Status Codes:**
- 200 OK: Token refresh successful
- 401 Unauthorized: Invalid or expired refresh token
- 422 Unprocessable Entity: Invalid request format

#### Example Request

```bash
curl -X POST "https://api.example.com/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

#### Example Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Logout

**POST /auth/logout**

Revoke a refresh token, effectively logging the user out.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Status Codes:**
- 200 OK: Logout successful (or token already revoked)
- 422 Unprocessable Entity: Invalid request format

#### Example Request

```bash
curl -X POST "https://api.example.com/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

#### Example Response

```json
{
  "message": "Successfully logged out"
}
```

### User Registration

**POST /auth/register**

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string"
}
```

**Status Codes:**
- 201 Created: User registration successful
- 400 Bad Request: Username or email already exists
- 422 Unprocessable Entity: Invalid request format or password requirements not met

#### Example Request

```bash
curl -X POST "https://api.example.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "newuser@example.com", "password": "SecureP@ssw0rd"}'
```

#### Example Response

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "username": "newuser",
  "email": "newuser@example.com"
}
```

## Using Authentication Tokens

After obtaining an access token, include it in the Authorization header of subsequent API requests:

### Authorization Header Format

```
Authorization: Bearer <access_token>
```

Where `<access_token>` is the JWT token received from the login or refresh endpoints.

### Example Authenticated Request

```bash
curl -X GET "https://api.example.com/documents/list" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expiration Handling

When an access token expires, the API will return a 401 Unauthorized response. The client should then use the refresh token to obtain a new access token via the /auth/refresh endpoint.

## Role-Based Authorization

The system implements role-based access control with the following roles:

### Available Roles

- **admin**: Full system access including user management
- **regular**: Standard user with access to own documents and queries
- **guest**: Limited access for unauthenticated or minimally authenticated users

### Role Claims

The JWT access token includes a `role` claim that specifies the user's role. API endpoints use this claim to enforce access control.

### Permission Matrix

| Endpoint | Admin | Regular User | Guest |
| --- | --- | --- | --- |
| POST /documents/upload | ✓ | ✓ | ✗ |
| GET /documents/list | ✓ | ✓ | ✗ |
| GET /documents/{id} | ✓ | ✓ (own docs) | ✗ |
| DELETE /documents/{id} | ✓ | ✓ (own docs) | ✗ |
| POST /query | ✓ | ✓ | ✓ (limited) |
| GET /query/{id} | ✓ | ✓ (own queries) | ✗ |
| POST /feedback | ✓ | ✓ | ✗ |
| GET /feedback/{id} | ✓ | ✓ (own feedback) | ✗ |
| POST /reinforce | ✓ | ✗ | ✗ |
| User management | ✓ | ✗ | ✗ |

## Password Requirements

User passwords must meet the following requirements:

### Password Criteria

- Minimum length: 10 characters
- Must include at least one uppercase letter
- Must include at least one lowercase letter
- Must include at least one number
- Must include at least one special character

### Password Policies

- Passwords expire after 90 days
- Cannot reuse the last 5 passwords
- Account lockout after 5 failed login attempts

## Error Handling

Authentication endpoints return standard HTTP status codes and error responses:

### Common Error Codes

- **401 Unauthorized**: Invalid credentials or token
- **403 Forbidden**: Insufficient permissions for the requested operation
- **422 Unprocessable Entity**: Invalid request format

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### Example Error Response

```json
{
  "detail": "Invalid username or password"
}
```

## Security Best Practices

When implementing client authentication, follow these security best practices:

### Token Storage

- Store access tokens in memory for web applications
- Use secure HTTP-only cookies for refresh tokens
- For mobile applications, use secure storage mechanisms provided by the platform

### Token Refresh Strategy

- Implement automatic token refresh when access tokens expire
- Include error handling for failed refresh attempts
- Redirect to login when refresh token is invalid or expired

### Logout Handling

- Always revoke refresh tokens on logout
- Clear stored tokens from client storage
- Consider implementing a server-side session invalidation mechanism for sensitive applications

## Async API Support

The system provides async versions of all authentication endpoints for high-performance clients:

### Async Endpoints

- POST /auth/token/async
- POST /auth/refresh/async
- POST /auth/logout/async
- POST /auth/register/async

### Usage Notes

Async endpoints have identical request and response formats as their synchronous counterparts but are optimized for high-concurrency scenarios.