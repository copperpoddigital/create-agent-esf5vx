from typing import Optional  # standard library
from pydantic import BaseModel, Field, UUID4  # 2.0.0+

class Token(BaseModel):
    """
    Schema for token response containing access token and optional refresh token.
    
    Used for returning authentication tokens to clients after successful login
    or token refresh operations.
    """
    access_token: str
    token_type: str = 'bearer'
    refresh_token: Optional[str] = None

class TokenPayload(BaseModel):
    """
    Schema for JWT token payload containing claims.
    
    These claims are encoded in the JWT token and used for validation
    and authorization purposes.
    """
    sub: str  # subject identifier (user ID)
    role: Optional[str] = None  # user role for authorization
    exp: Optional[int] = None  # expiration time (Unix timestamp)
    iat: Optional[int] = None  # issued at time (Unix timestamp)
    type: Optional[str] = None  # token type (access or refresh)

class TokenData(BaseModel):
    """
    Schema for decoded token data used in authentication dependencies.
    
    This model is used after token verification to represent the authenticated user.
    """
    user_id: UUID4  # UUID of the authenticated user
    role: Optional[str] = None  # user role for authorization

class TokenRequest(BaseModel):
    """
    Schema for login request to obtain access token.
    
    Used to validate user credentials during the authentication process.
    """
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request to obtain new access token.
    
    Used when the client wants to refresh an expired access token
    without requiring the user to re-authenticate.
    """
    refresh_token: str