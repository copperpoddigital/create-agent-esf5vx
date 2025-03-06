from typing import Optional, Any, Dict, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CRUDBase
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    CRUD operations for User model, extending the generic CRUDBase class with user-specific
    functionality like authentication and user retrieval by username/email.
    """

    def __init__(self):
        """Initialize the CRUDUser class with the User model"""
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get a user by username
        
        Args:
            db: Database session
            username: Username to search for
            
        Returns:
            The user if found, None otherwise
        """
        stmt = select(self.model).where(self.model.username == username)
        result = db.execute(stmt)
        return result.scalars().first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get a user by email
        
        Args:
            db: Database session
            email: Email to search for
            
        Returns:
            The user if found, None otherwise
        """
        stmt = select(self.model).where(self.model.email == email)
        result = db.execute(stmt)
        return result.scalars().first()

    async def get_by_username_async(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Get a user by username asynchronously
        
        Args:
            db: Async database session
            username: Username to search for
            
        Returns:
            The user if found, None otherwise
        """
        stmt = select(self.model).where(self.model.username == username)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_email_async(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email asynchronously
        
        Args:
            db: Async database session
            email: Email to search for
            
        Returns:
            The user if found, None otherwise
        """
        stmt = select(self.model).where(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    def create(self, db: Session, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password
        
        Args:
            db: Database session
            obj_in: User creation schema with user data
            
        Returns:
            The created user
        """
        hashed_password = get_password_hash(obj_in.password)
        
        # Create user data dictionary excluding the plain password
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.__dict__
        obj_in_data.pop("password")
        
        # Add the hashed password
        db_obj = User(**obj_in_data, password_hash=hashed_password)
        
        # Add to database and commit
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj

    async def create_async(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password asynchronously
        
        Args:
            db: Async database session
            obj_in: User creation schema with user data
            
        Returns:
            The created user
        """
        hashed_password = get_password_hash(obj_in.password)
        
        # Create user data dictionary excluding the plain password
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.__dict__
        obj_in_data.pop("password")
        
        # Add the hashed password
        db_obj = User(**obj_in_data, password_hash=hashed_password)
        
        # Add to database and commit
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    def update(
        self, db: Session, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user, handling password hashing if password is provided
        
        Args:
            db: Database session
            db_obj: Existing user object
            obj_in: User update schema or dictionary with fields to update
            
        Returns:
            The updated user
        """
        # Convert to dict if it's a Pydantic model
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.__dict__
        
        # If password is provided, hash it
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            update_data["password_hash"] = hashed_password
            del update_data["password"]
        
        # Use the parent class's update method
        return super().update(db, db_obj, update_data)

    async def update_async(
        self, db: AsyncSession, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user asynchronously, handling password hashing if password is provided
        
        Args:
            db: Async database session
            db_obj: Existing user object
            obj_in: User update schema or dictionary with fields to update
            
        Returns:
            The updated user
        """
        # Convert to dict if it's a Pydantic model
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.__dict__
        
        # If password is provided, hash it
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            update_data["password_hash"] = hashed_password
            del update_data["password"]
        
        # Use the parent class's update method
        return await super().update_async(db, db_obj, update_data)

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            The authenticated user if successful, None otherwise
        """
        user = self.get_by_username(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login timestamp
        user.update_last_login()
        db.commit()
        
        return user

    async def authenticate_async(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password asynchronously
        
        Args:
            db: Async database session
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            The authenticated user if successful, None otherwise
        """
        user = await self.get_by_username_async(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login timestamp
        user.update_last_login()
        await db.commit()
        
        return user

    def is_active(self, user: User) -> bool:
        """
        Check if a user is active
        
        Args:
            user: User to check
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active

    def is_admin(self, user: User) -> bool:
        """
        Check if a user has admin role
        
        Args:
            user: User to check
            
        Returns:
            True if user has admin role, False otherwise
        """
        return user.is_admin()


# Create a singleton instance of CRUDUser for application-wide use
user = CRUDUser()