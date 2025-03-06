"""
Authentication endpoints for the Document Management and AI Chatbot System.

This module provides API routes for user login, token refresh, token revocation, 
and user registration, implementing JWT-based authentication.
"""

import logging  # standard library
from fastapi import APIRouter, Depends, HTTPException, status  # version 0.95.0+
from sqlalchemy.orm import Session  # SQLAlchemy 2.0.0+
from sqlalchemy.ext.asyncio import AsyncSession  # SQLAlchemy 2.0.0+

from ....api.dependencies import get_db_dependency, get_async_db_dependency
from ....schemas.token import Token, TokenRequest, RefreshTokenRequest
from ....schemas.user import UserCreate, User
from ....services.auth_service import (
    authenticate_user, authenticate_user_async,
    create_user_tokens, create_user_tokens_async,
    refresh_access_token, refresh_access_token_async,
    revoke_token, revoke_token_async
)
from ....crud.crud_user import user

# Set up module logger
logger = logging.getLogger(__name__)

# Create API router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
def login(form_data: TokenRequest, db: Session = Depends(get_db_dependency)) -> Token:
    """
    Authenticates a user and returns access and refresh tokens.
    
    Args:
        form_data: Login credentials with username and password
        db: Database session
        
    Returns:
        Token object containing access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Log login attempt (without logging the password)
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Authenticate user with provided credentials
    authenticated_user = authenticate_user(db, form_data.username, form_data.password)
    
    # If authentication fails, raise an exception
    if not authenticated_user:
        logger.warning(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access and refresh tokens for the authenticated user
    tokens = create_user_tokens(db, authenticated_user)
    
    # Return the tokens
    return tokens


@router.post("/token/async", response_model=Token)
async def login_async(form_data: TokenRequest, db: AsyncSession = Depends(get_async_db_dependency)) -> Token:
    """
    Authenticates a user asynchronously and returns access and refresh tokens.
    
    Args:
        form_data: Login credentials with username and password
        db: Async database session
        
    Returns:
        Token object containing access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Log login attempt (without logging the password)
    logger.info(f"Async login attempt for user: {form_data.username}")
    
    # Authenticate user with provided credentials asynchronously
    authenticated_user = await authenticate_user_async(db, form_data.username, form_data.password)
    
    # If authentication fails, raise an exception
    if not authenticated_user:
        logger.warning(f"Async authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access and refresh tokens for the authenticated user asynchronously
    tokens = await create_user_tokens_async(db, authenticated_user)
    
    # Return the tokens
    return tokens


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db_dependency)) -> Token:
    """
    Refreshes an access token using a refresh token.
    
    Args:
        refresh_request: Request containing the refresh token
        db: Database session
        
    Returns:
        Token object containing new access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Log token refresh attempt
    logger.info("Token refresh attempt")
    
    try:
        # Call service function to refresh the token
        new_tokens = refresh_access_token(db, refresh_request.refresh_token)
        return new_tokens
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh/async", response_model=Token)
async def refresh_token_async(refresh_request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db_dependency)) -> Token:
    """
    Refreshes an access token asynchronously using a refresh token.
    
    Args:
        refresh_request: Request containing the refresh token
        db: Async database session
        
    Returns:
        Token object containing new access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Log token refresh attempt
    logger.info("Async token refresh attempt")
    
    try:
        # Call async service function to refresh the token
        new_tokens = await refresh_access_token_async(db, refresh_request.refresh_token)
        return new_tokens
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.error(f"Error refreshing token asynchronously: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
def logout(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db_dependency)) -> dict:
    """
    Revokes a refresh token, effectively logging the user out.
    
    Args:
        refresh_request: Request containing the refresh token to revoke
        db: Database session
        
    Returns:
        Dictionary with success message
    """
    # Log logout attempt
    logger.info("Logout attempt")
    
    # Revoke the refresh token
    revoke_token(db, refresh_request.refresh_token)
    
    # Return success message (even if token wasn't found or already revoked)
    # This maintains idempotency of the logout operation
    return {"message": "Successfully logged out"}


@router.post("/logout/async")
async def logout_async(refresh_request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db_dependency)) -> dict:
    """
    Revokes a refresh token asynchronously, effectively logging the user out.
    
    Args:
        refresh_request: Request containing the refresh token to revoke
        db: Async database session
        
    Returns:
        Dictionary with success message
    """
    # Log logout attempt
    logger.info("Async logout attempt")
    
    # Revoke the refresh token asynchronously
    await revoke_token_async(db, refresh_request.refresh_token)
    
    # Return success message (even if token wasn't found or already revoked)
    # This maintains idempotency of the logout operation
    return {"message": "Successfully logged out"}


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db_dependency)) -> User:
    """
    Registers a new user and returns their information.
    
    Args:
        user_data: User creation data with username, email, and password
        db: Database session
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Log registration attempt
    logger.info(f"Registration attempt for username: {user_data.username}, email: {user_data.email}")
    
    # Check if username already exists
    if user.get_by_username(db, user_data.username):
        logger.warning(f"Registration failed: username {user_data.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists
    if user.get_by_email(db, user_data.email):
        logger.warning(f"Registration failed: email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    created_user = user.create(db, user_data)
    logger.info(f"User registered successfully: {created_user.username}")
    
    # Return created user
    return created_user


@router.post("/register/async", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_async(user_data: UserCreate, db: AsyncSession = Depends(get_async_db_dependency)) -> User:
    """
    Registers a new user asynchronously and returns their information.
    
    Args:
        user_data: User creation data with username, email, and password
        db: Async database session
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Log registration attempt
    logger.info(f"Async registration attempt for username: {user_data.username}, email: {user_data.email}")
    
    # Check if username already exists asynchronously
    existing_username = await user.get_by_username_async(db, user_data.username)
    if existing_username:
        logger.warning(f"Async registration failed: username {user_data.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists asynchronously
    existing_email = await user.get_by_email_async(db, user_data.email)
    if existing_email:
        logger.warning(f"Async registration failed: email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user asynchronously
    created_user = await user.create_async(db, user_data)
    logger.info(f"User registered successfully (async): {created_user.username}")
    
    # Return created user
    return created_user