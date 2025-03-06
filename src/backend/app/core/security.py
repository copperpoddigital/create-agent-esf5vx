"""
Core security module that implements JWT authentication, password hashing, and token management.

This module provides functions for creating and verifying JWT tokens, hashing and verifying
passwords, and generating secure random tokens for the Document Management and AI Chatbot System.
"""
from datetime import datetime, timedelta
import uuid
import re
from typing import Optional, Tuple, Dict, Any

from fastapi import HTTPException, status  # version 0.95.0+
from jose import jwt, JWTError  # version 3.3.0+
from passlib.context import CryptContext  # version 1.7.4+
import secrets

from .config import security_settings
from ..schemas.token import TokenPayload, TokenData

# Configure the password context with Argon2id (memory-hard algorithm)
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto", 
    argon2__memory_cost=65536,  # 64MB
    argon2__time_cost=3,         # 3 iterations
    argon2__parallelism=4        # 4 parallel threads
)

# JWT algorithm and token expiration from settings
ALGORITHM = security_settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = security_settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to check against

    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates a secure hash of the password using Argon2id.

    Args:
        password: The plain text password to hash

    Returns:
        str: The hashed password string
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates password strength against configured requirements.

    Args:
        password: The password to validate

    Returns:
        Tuple[bool, str]: A tuple containing (is_valid, error_message)
    """
    # Check minimum length
    if len(password) < security_settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {security_settings.PASSWORD_MIN_LENGTH} characters long"

    # Check uppercase requirement
    if security_settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    # Check lowercase requirement
    if security_settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    # Check digit requirement
    if security_settings.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    # Check special character requirement
    if security_settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token with the specified data and expiration.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta, defaults to settings value

    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration and issued at claims
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        security_settings.JWT_SECRET.get_secret_value(), 
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """
    Creates a JWT refresh token with longer expiration.

    Args:
        data: The data to encode in the token

    Returns:
        str: The encoded refresh token
    """
    to_encode = data.copy()
    
    # Set longer expiration time for refresh token
    expire = datetime.utcnow() + timedelta(days=security_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add expiration, issued at, and token type claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        security_settings.JWT_SECRET.get_secret_value(), 
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verifies and decodes a JWT token, returning the token data.

    Args:
        token: The JWT token to verify

    Returns:
        TokenData: The decoded token data with user_id and role

    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            security_settings.JWT_SECRET.get_secret_value(),
            algorithms=[ALGORITHM]
        )
        
        # Extract data from payload
        token_payload = TokenPayload(**payload)
        
        # Ensure we have a subject (user_id)
        if token_payload.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token data with user_id and role
        token_data = TokenData(user_id=uuid.UUID(token_payload.sub), role=token_payload.role)
        return token_data
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_secure_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure random token.

    Args:
        length: The length of the token in bytes

    Returns:
        str: The generated secure token string
    """
    return secrets.token_urlsafe(length)


def generate_uuid() -> str:
    """
    Generates a random UUID for use as a unique identifier.

    Returns:
        str: The generated UUID string
    """
    return str(uuid.uuid4())