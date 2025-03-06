"""
Utility module that provides helper functions for JWT token handling, validation, and management.

This module abstracts common token operations used across the application for the
Document Management and AI Chatbot System, including token generation, validation,
and extraction from request headers.
"""
from datetime import datetime, timedelta  # standard library
from typing import Optional, Dict, Any  # standard library
import logging  # standard library
from uuid import UUID  # standard library

from jose import jwt, JWTError  # python-jose 3.3.0+
from fastapi import HTTPException, status  # fastapi 0.95.0+

from ..core.config import security_settings
from ..schemas.token import TokenPayload, TokenData

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants from settings
ALGORITHM = security_settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = security_settings.ACCESS_TOKEN_EXPIRE_MINUTES


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes a JWT token and returns the payload.
    
    Args:
        token: The JWT token string to decode
        
    Returns:
        Dict[str, Any]: Decoded token payload as a dictionary
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode the JWT token using the secret key and algorithm
        payload = jwt.decode(
            token,
            security_settings.JWT_SECRET.get_secret_value(),
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Failed to decode token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_token_data(payload: Dict[str, Any]) -> TokenData:
    """
    Extracts user data from a decoded token payload.
    
    Args:
        payload: The decoded token payload dictionary
        
    Returns:
        TokenData: Token data with user_id and role
        
    Raises:
        HTTPException: If required data is missing from the token
    """
    try:
        # Extract the subject (user_id) from the payload
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Subject claim missing from token")
        
        # Convert string user_id to UUID
        user_id = UUID(user_id_str)
        
        # Extract the role from the payload if present
        role = payload.get("role")
        
        # Create and return a TokenData object
        return TokenData(user_id=user_id, role=role)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid token data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token data",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_token_payload(
    subject: str,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    token_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a token payload with the specified data and claims.
    
    Args:
        subject: The subject claim (user ID)
        role: Optional role claim for authorization
        expires_delta: Optional custom expiration time
        token_type: Optional token type (e.g., 'access', 'refresh')
        
    Returns:
        Dict[str, Any]: Token payload dictionary
    """
    # Create a payload dictionary with the subject claim
    payload = {"sub": subject}
    
    # Add role claim if provided
    if role:
        payload["role"] = role
    
    # Calculate expiration time
    expire = calculate_token_expiry(expires_delta)
    payload["exp"] = expire
    
    # Add issued at claim with current timestamp
    payload["iat"] = int(datetime.utcnow().timestamp())
    
    # Add token type claim if provided
    if token_type:
        payload["type"] = token_type
    
    return payload


def encode_token(payload: Dict[str, Any]) -> str:
    """
    Encodes a payload into a JWT token.
    
    Args:
        payload: The token payload to encode
        
    Returns:
        str: Encoded JWT token
    """
    # Encode the payload using JWT with the secret key and algorithm
    token = jwt.encode(
        payload,
        security_settings.JWT_SECRET.get_secret_value(),
        algorithm=ALGORITHM
    )
    
    # Log token creation (without sensitive data)
    logger.debug(f"Created token for user: {payload.get('sub')} with role: {payload.get('role')}")
    
    return token


def get_token_from_header(authorization: str) -> str:
    """
    Extracts JWT token from the Authorization header.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        str: Extracted token
        
    Raises:
        HTTPException: If header is missing or invalid
    """
    # Check if authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Split header into scheme and token
    auth_parts = authorization.split()
    
    # Verify the authorization scheme is 'Bearer'
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract the token part from the header
    token = auth_parts[1]
    
    return token


def is_token_expired(payload: Dict[str, Any]) -> bool:
    """
    Checks if a token is expired based on its payload.
    
    Args:
        payload: The decoded token payload
        
    Returns:
        bool: True if token is expired, False otherwise
    """
    # Extract expiration timestamp from payload
    exp = payload.get("exp")
    
    # If no expiration claim, consider it not expired
    if not exp:
        return False
    
    # Compare with current timestamp
    now = int(datetime.utcnow().timestamp())
    
    # Return True if current time is past expiration
    return now > exp


def calculate_token_expiry(expires_delta: Optional[timedelta] = None) -> int:
    """
    Calculates token expiration timestamp.
    
    Args:
        expires_delta: Optional custom expiration time
        
    Returns:
        int: Expiration timestamp
    """
    # Use provided expires_delta or default from settings
    if expires_delta:
        expiration_time = datetime.utcnow() + expires_delta
    else:
        expiration_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Convert to timestamp and return
    return int(expiration_time.timestamp())