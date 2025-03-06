"""
Authentication service that implements user authentication, token management, and session handling
for the Document Management and AI Chatbot System. This service provides high-level functions for
user login, token creation, validation, refresh, and revocation.
"""
import logging
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any, Union

from fastapi import HTTPException, status  # version 0.95.0+
from sqlalchemy.orm import Session  # version 2.0.0+
from sqlalchemy.ext.asyncio import AsyncSession  # version 2.0.0+

from ..core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_secure_token
)
from ..crud.crud_user import user
from ..schemas.token import Token, TokenData
from ..utils.token_utils import decode_token, extract_token_data, create_token_payload
from ..core.config import security_settings

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants from settings
REFRESH_TOKEN_EXPIRE_DAYS = security_settings.REFRESH_TOKEN_EXPIRE_DAYS


class RefreshToken:
    """
    SQLAlchemy ORM model for refresh tokens stored in the database.
    """
    id: uuid.UUID
    token: str
    user_id: str
    is_revoked: bool
    created_at: datetime
    expires_at: datetime
    
    def __init__(self, token: str, user_id: str, expires_at: Optional[datetime] = None):
        """
        Initializes a RefreshToken instance
        
        Args:
            token: The refresh token string
            user_id: The ID of the user the token belongs to
            expires_at: Optional expiration timestamp
        """
        self.token = token
        self.user_id = user_id
        self.is_revoked = False
        self.created_at = datetime.utcnow()
        
        # Set expiration date based on settings if not provided
        if expires_at is None:
            self.expires_at = self.created_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            self.expires_at = expires_at
    
    def is_expired(self) -> bool:
        """
        Checks if the token is expired
        
        Returns:
            bool: True if token is expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """
        Checks if the token is valid (not revoked and not expired)
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        return not self.is_revoked and not self.is_expired()
    
    def revoke(self) -> None:
        """
        Revokes the token
        """
        self.is_revoked = True


def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticates a user with username and password
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        Optional[User]: Authenticated user if successful, None otherwise
    """
    logger.info(f"Authentication attempt for user: {username}")
    
    # Use the user CRUD object to authenticate
    authenticated_user = user.authenticate(db, username, password)
    
    if authenticated_user:
        logger.info(f"User authenticated successfully: {username}")
    else:
        logger.warning(f"Authentication failed for user: {username}")
    
    return authenticated_user


async def authenticate_user_async(db: AsyncSession, username: str, password: str):
    """
    Authenticates a user with username and password asynchronously
    
    Args:
        db: Async database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        Optional[User]: Authenticated user if successful, None otherwise
    """
    logger.info(f"Asynchronous authentication attempt for user: {username}")
    
    # Use the user CRUD object to authenticate asynchronously
    authenticated_user = await user.authenticate_async(db, username, password)
    
    if authenticated_user:
        logger.info(f"User authenticated successfully (async): {username}")
    else:
        logger.warning(f"Authentication failed (async) for user: {username}")
    
    return authenticated_user


def create_user_tokens(db: Session, user_obj) -> Token:
    """
    Creates access and refresh tokens for a user
    
    Args:
        db: Database session
        user_obj: User object to create tokens for
        
    Returns:
        Token: Token object containing access and refresh tokens
    """
    # Create token data with user ID as subject and user role
    token_data = {"sub": str(user_obj.id), "role": user_obj.role.name if hasattr(user_obj.role, "name") else user_obj.role}
    
    # Create access token
    access_token = create_access_token(data=token_data)
    
    # Create refresh token
    refresh_token = create_refresh_token(data=token_data)
    
    # Store refresh token in database
    store_refresh_token(db, refresh_token, str(user_obj.id))
    
    logger.info(f"Created tokens for user: {user_obj.username}")
    
    # Return token object
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token
    )


async def create_user_tokens_async(db: AsyncSession, user_obj) -> Token:
    """
    Creates access and refresh tokens for a user asynchronously
    
    Args:
        db: Async database session
        user_obj: User object to create tokens for
        
    Returns:
        Token: Token object containing access and refresh tokens
    """
    # Create token data with user ID as subject and user role
    token_data = {"sub": str(user_obj.id), "role": user_obj.role.name if hasattr(user_obj.role, "name") else user_obj.role}
    
    # Create access token
    access_token = create_access_token(data=token_data)
    
    # Create refresh token
    refresh_token = create_refresh_token(data=token_data)
    
    # Store refresh token in database asynchronously
    await store_refresh_token_async(db, refresh_token, str(user_obj.id))
    
    logger.info(f"Created tokens for user (async): {user_obj.username}")
    
    # Return token object
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token
    )


def refresh_access_token(db: Session, refresh_token: str) -> Token:
    """
    Refreshes an access token using a refresh token
    
    Args:
        db: Database session
        refresh_token: Refresh token to use for getting a new access token
        
    Returns:
        Token: Token object containing new access_token and refresh_token
        
    Raises:
        HTTPException: If the refresh token is invalid, expired, or revoked
    """
    try:
        # Decode the refresh token
        payload = decode_token(refresh_token)
        
        # Verify token type is 'refresh'
        if payload.get("type") != "refresh":
            logger.warning("Attempted to use non-refresh token for refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user ID from token
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Refresh token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify refresh token exists in database and is not revoked
        db_token = get_refresh_token(db, refresh_token)
        if not db_token or not db_token.is_valid():
            logger.warning(f"Invalid or revoked refresh token for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_obj = user.get(db, user_id)
        if not user_obj or not user.is_active(user_obj):
            logger.warning(f"User not found or inactive: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Revoke the used refresh token
        revoke_token(db, refresh_token)
        
        # Create new access and refresh tokens
        return create_user_tokens(db, user_obj)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def refresh_access_token_async(db: AsyncSession, refresh_token: str) -> Token:
    """
    Refreshes an access token using a refresh token asynchronously
    
    Args:
        db: Async database session
        refresh_token: Refresh token to use for getting a new access token
        
    Returns:
        Token: Token object containing new access_token and refresh_token
        
    Raises:
        HTTPException: If the refresh token is invalid, expired, or revoked
    """
    try:
        # Decode the refresh token
        payload = decode_token(refresh_token)
        
        # Verify token type is 'refresh'
        if payload.get("type") != "refresh":
            logger.warning("Attempted to use non-refresh token for refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user ID from token
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Refresh token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify refresh token exists in database and is not revoked
        db_token = await get_refresh_token_async(db, refresh_token)
        if not db_token or not db_token.is_valid():
            logger.warning(f"Invalid or revoked refresh token for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database asynchronously
        user_obj = await user.get_async(db, user_id)
        if not user_obj or not user.is_active(user_obj):
            logger.warning(f"User not found or inactive: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Revoke the used refresh token asynchronously
        await revoke_token_async(db, refresh_token)
        
        # Create new access and refresh tokens asynchronously
        return await create_user_tokens_async(db, user_obj)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error refreshing token asynchronously: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def revoke_token(db: Session, refresh_token: str) -> bool:
    """
    Revokes a refresh token
    
    Args:
        db: Database session
        refresh_token: Token to revoke
        
    Returns:
        bool: True if token was found and revoked, False otherwise
    """
    try:
        # Try to decode the token to ensure it's valid
        decode_token(refresh_token)
        
        # Find the token in the database
        db_token = get_refresh_token(db, refresh_token)
        if not db_token:
            logger.warning(f"Token not found in database during revocation")
            return False
        
        # Mark the token as revoked
        db_token.revoke()
        db.add(db_token)
        db.commit()
        
        logger.info(f"Token revoked for user: {db_token.user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        return False


async def revoke_token_async(db: AsyncSession, refresh_token: str) -> bool:
    """
    Revokes a refresh token asynchronously
    
    Args:
        db: Async database session
        refresh_token: Token to revoke
        
    Returns:
        bool: True if token was found and revoked, False otherwise
    """
    try:
        # Try to decode the token to ensure it's valid
        decode_token(refresh_token)
        
        # Find the token in the database asynchronously
        db_token = await get_refresh_token_async(db, refresh_token)
        if not db_token:
            logger.warning(f"Token not found in database during async revocation")
            return False
        
        # Mark the token as revoked
        db_token.revoke()
        db.add(db_token)
        await db.commit()
        
        logger.info(f"Token revoked asynchronously for user: {db_token.user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error revoking token asynchronously: {str(e)}")
        return False


def revoke_all_user_tokens(db: Session, user_id: Union[str, uuid.UUID]) -> int:
    """
    Revokes all refresh tokens for a user
    
    Args:
        db: Database session
        user_id: ID of the user whose tokens should be revoked
        
    Returns:
        int: Number of tokens revoked
    """
    # Convert user_id to string if it's a UUID
    if isinstance(user_id, uuid.UUID):
        user_id = str(user_id)
    
    try:
        # Find all active refresh tokens for the user
        tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        
        # Mark all found tokens as revoked
        token_count = 0
        for token in tokens:
            token.revoke()
            db.add(token)
            token_count += 1
        
        # Commit the changes to the database
        db.commit()
        
        logger.info(f"Revoked {token_count} tokens for user: {user_id}")
        return token_count
    
    except Exception as e:
        logger.error(f"Error revoking all tokens for user {user_id}: {str(e)}")
        db.rollback()
        return 0


async def revoke_all_user_tokens_async(db: AsyncSession, user_id: Union[str, uuid.UUID]) -> int:
    """
    Revokes all refresh tokens for a user asynchronously
    
    Args:
        db: Async database session
        user_id: ID of the user whose tokens should be revoked
        
    Returns:
        int: Number of tokens revoked
    """
    # Convert user_id to string if it's a UUID
    if isinstance(user_id, uuid.UUID):
        user_id = str(user_id)
    
    try:
        # Find all active refresh tokens for the user asynchronously
        from sqlalchemy import select  # SQLAlchemy 2.0.0+
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
        result = await db.execute(stmt)
        tokens = result.scalars().all()
        
        # Mark all found tokens as revoked
        token_count = 0
        for token in tokens:
            token.revoke()
            db.add(token)
            token_count += 1
        
        # Commit the changes to the database asynchronously
        await db.commit()
        
        logger.info(f"Revoked {token_count} tokens asynchronously for user: {user_id}")
        return token_count
    
    except Exception as e:
        logger.error(f"Error revoking all tokens asynchronously for user {user_id}: {str(e)}")
        await db.rollback()
        return 0


def get_user_from_token(db: Session, token: str):
    """
    Gets a user from a token
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        Optional[User]: User if token is valid and user exists, None otherwise
    """
    try:
        # Try to decode the token
        payload = decode_token(token)
        
        # Extract user ID from token data
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing subject claim")
            return None
        
        # Get user from database
        return user.get(db, user_id)
    
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return None


async def get_user_from_token_async(db: AsyncSession, token: str):
    """
    Gets a user from a token asynchronously
    
    Args:
        db: Async database session
        token: JWT token
        
    Returns:
        Optional[User]: User if token is valid and user exists, None otherwise
    """
    try:
        # Try to decode the token
        payload = decode_token(token)
        
        # Extract user ID from token data
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing subject claim")
            return None
        
        # Get user from database asynchronously
        return await user.get_async(db, user_id)
    
    except Exception as e:
        logger.error(f"Error getting user from token asynchronously: {str(e)}")
        return None


def store_refresh_token(
    db: Session, 
    token: str, 
    user_id: str, 
    expires_at: Optional[datetime] = None
) -> RefreshToken:
    """
    Stores a refresh token in the database
    
    Args:
        db: Database session
        token: Refresh token string
        user_id: ID of the user the token belongs to
        expires_at: Optional expiration timestamp
        
    Returns:
        RefreshToken: Created refresh token record
    """
    # Create a new RefreshToken instance
    token_obj = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    
    # Add the token to the database session
    db.add(token_obj)
    
    # Commit the session to persist the token
    db.commit()
    
    logger.debug(f"Stored refresh token for user: {user_id}")
    return token_obj


async def store_refresh_token_async(
    db: AsyncSession, 
    token: str, 
    user_id: str, 
    expires_at: Optional[datetime] = None
) -> RefreshToken:
    """
    Stores a refresh token in the database asynchronously
    
    Args:
        db: Async database session
        token: Refresh token string
        user_id: ID of the user the token belongs to
        expires_at: Optional expiration timestamp
        
    Returns:
        RefreshToken: Created refresh token record
    """
    # Create a new RefreshToken instance
    token_obj = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
    
    # Add the token to the database session
    db.add(token_obj)
    
    # Commit the session asynchronously to persist the token
    await db.commit()
    
    logger.debug(f"Stored refresh token asynchronously for user: {user_id}")
    return token_obj


def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """
    Gets a refresh token from the database
    
    Args:
        db: Database session
        token: Refresh token string
        
    Returns:
        RefreshToken: RefreshToken if found, None otherwise
    """
    try:
        # Query the database for the refresh token
        result = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving refresh token: {str(e)}")
        return None


async def get_refresh_token_async(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """
    Gets a refresh token from the database asynchronously
    
    Args:
        db: Async database session
        token: Refresh token string
        
    Returns:
        RefreshToken: RefreshToken if found, None otherwise
    """
    try:
        # Query the database for the refresh token asynchronously
        from sqlalchemy import select  # SQLAlchemy 2.0.0+
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    except Exception as e:
        logger.error(f"Error retrieving refresh token asynchronously: {str(e)}")
        return None