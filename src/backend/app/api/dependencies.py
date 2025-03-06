"""
FastAPI dependency functions for the Document Management and AI Chatbot System.

This module provides reusable dependencies for authentication, database access, and permission
checking that can be injected into API route handlers. These dependencies implement JWT-based
authentication, role-based access control, and provide database sessions for API endpoints.
"""

from typing import Optional, Annotated  # standard library
from uuid import UUID  # standard library

from fastapi import Depends, HTTPException, status, Header  # version 0.95.0+
from fastapi.security import Security, HTTPBearer, HTTPAuthorizationCredentials  # version 0.95.0+
from sqlalchemy.orm import Session  # SQLAlchemy 2.0.0+
from sqlalchemy.ext.asyncio import AsyncSession  # SQLAlchemy 2.0.0+

from ..core.security import verify_token
from ..schemas.token import TokenData
from ..db.session import get_db_dependency, get_async_db_dependency
from ..crud import user
from ..models.user import User
from ..core.config import security_settings

# JWT security scheme for authorization
oauth2_scheme = HTTPBearer(auto_error=False)

def get_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(oauth2_scheme)) -> str:
    """
    Extracts JWT token from the Authorization header.
    
    Args:
        credentials: Authorization credentials from the request header
        
    Returns:
        str: JWT token string
        
    Raises:
        HTTPException: If no valid authorization token is provided
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db_dependency)) -> User:
    """
    Validates JWT token and returns the authenticated user.
    
    Args:
        token: JWT token from the Authorization header
        db: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token validation fails or user is not found
    """
    try:
        # Verify the token and get token data
        token_data = verify_token(token)
        
        # Get the user from the database
        user_obj = user.get(db=db, id=token_data.user_id)
        if user_obj is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Returns the current authenticated user if active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User: Active authenticated user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Returns the current authenticated user if they have admin role.
    
    Args:
        current_user: Active user from get_current_active_user dependency
        
    Returns:
        User: Admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough permissions",
        )
    return current_user

async def get_current_user_async(
    token: str = Depends(get_token), db: AsyncSession = Depends(get_async_db_dependency)
) -> User:
    """
    Validates JWT token and returns the authenticated user asynchronously.
    
    Args:
        token: JWT token from the Authorization header
        db: Async database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token validation fails or user is not found
    """
    try:
        # Verify the token and get token data
        token_data = verify_token(token)
        
        # Get the user from the database asynchronously
        user_obj = await user.get_async(db=db, id=token_data.user_id)
        if user_obj is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user_async(current_user: User = Depends(get_current_user_async)) -> User:
    """
    Returns the current authenticated user if active (async version).
    
    Args:
        current_user: User from get_current_user_async dependency
        
    Returns:
        User: Active authenticated user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user

async def get_current_admin_user_async(current_user: User = Depends(get_current_active_user_async)) -> User:
    """
    Returns the current authenticated user if they have admin role (async version).
    
    Args:
        current_user: Active user from get_current_active_user_async dependency
        
    Returns:
        User: Admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough permissions",
        )
    return current_user

def get_optional_current_user(
    token: Optional[str] = None, db: Session = Depends(get_db_dependency)
) -> Optional[User]:
    """
    Attempts to get the current user but returns None if authentication fails.
    
    Args:
        token: Optional JWT token from the Authorization header
        db: Database session
        
    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    if not token:
        return None
    
    try:
        # Verify the token and get token data
        token_data = verify_token(token)
        
        # Get the user from the database
        user_obj = user.get(db=db, id=token_data.user_id)
        if user_obj is None or not user.is_active(user_obj):
            return None
        
        return user_obj
    except Exception:
        return None

async def get_optional_current_user_async(
    token: Optional[str] = None, db: AsyncSession = Depends(get_async_db_dependency)
) -> Optional[User]:
    """
    Attempts to get the current user asynchronously but returns None if authentication fails.
    
    Args:
        token: Optional JWT token from the Authorization header
        db: Async database session
        
    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    if not token:
        return None
    
    try:
        # Verify the token and get token data
        token_data = verify_token(token)
        
        # Get the user from the database asynchronously
        user_obj = await user.get_async(db=db, id=token_data.user_id)
        if user_obj is None or not user.is_active(user_obj):
            return None
        
        return user_obj
    except Exception:
        return None

def require_role(allowed_roles: list[str]):
    """
    Creates a dependency that requires the user to have a specific role.
    
    Args:
        allowed_roles: List of role names that are allowed to access the endpoint
        
    Returns:
        callable: Dependency function that checks user role
    """
    def role_dependency(current_user: User = Depends(get_current_active_user)):
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of these roles: {', '.join(allowed_roles)}",
            )
        return current_user
    
    return role_dependency