from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict, UUID4

from ..models.user import UserRole
from ..core.security import validate_password_strength


class UserBase(BaseModel):
    """Base Pydantic model for user data with common fields."""
    username: str
    email: EmailStr
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserCreate(UserBase):
    """Pydantic model for user creation with password validation."""
    password: str
    
    @validator('password')
    def validate_password(cls, password: str) -> str:
        """
        Validates password strength using security module function.
        
        Raises:
            ValueError: If the password does not meet strength requirements
        """
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_message)
        return password


class UserUpdate(BaseModel):
    """Pydantic model for user updates with all fields optional."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    
    @validator('password')
    def validate_password(cls, password: Optional[str]) -> Optional[str]:
        """
        Validates password strength if provided.
        
        Raises:
            ValueError: If the provided password does not meet strength requirements
        """
        if password is None:
            return None
        
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_message)
        return password


class UserInDBBase(UserBase):
    """Base Pydantic model for user data from database with ID and timestamps."""
    id: UUID4
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserInDBBase):
    """Pydantic model for user data from database including password hash."""
    password_hash: str


class User(UserInDBBase):
    """Pydantic model for user data returned in API responses (without password hash)."""
    pass