from typing import Generic, Type, TypeVar, Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import select, update, delete  # SQLAlchemy 2.0.0+
from sqlalchemy.orm import Session  # SQLAlchemy 2.0.0+
from sqlalchemy.ext.asyncio import AsyncSession  # SQLAlchemy 2.0.0+

from ..db.base_class import Base
from ..db.session import get_db, get_async_db

# Define TypeVars for generic typing
ModelType = TypeVar('ModelType', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for CRUD operations on database models.
    Provides standard methods for creating, reading, updating, and deleting database records
    with both synchronous and asynchronous support.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the CRUD base with a specific SQLAlchemy model
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Union[UUID, str, int]) -> Optional[ModelType]:
        """
        Get a single record by ID
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            The found record or None if not found
        """
        stmt = select(self.model).where(self.model.id == id)
        result = db.execute(stmt)
        return result.scalars().first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple records with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record
        
        Args:
            db: Database session
            obj_in: Create schema with data for the new record
            
        Returns:
            The created record
        """
        # Convert input to dictionary if it's not already
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            # Try Pydantic v2 model_dump method first
            if hasattr(obj_in, "model_dump"):
                obj_in_data = obj_in.model_dump()
            # Fallback to __dict__ for non-Pydantic objects
            else:
                obj_in_data = obj_in.__dict__
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record
        
        Args:
            db: Database session
            db_obj: Existing database record
            obj_in: Update schema with data to update
            
        Returns:
            The updated record
        """
        obj_data = db_obj.__dict__
        
        # Convert input to dictionary if it's not already
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Try Pydantic v2 model_dump method first
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            # Fallback to __dict__ for non-Pydantic objects
            else:
                update_data = obj_in.__dict__
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: Union[UUID, str, int]) -> Optional[ModelType]:
        """
        Delete a record
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            The deleted record or None if not found
        """
        obj = self.get(db=db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    async def get_async(self, db: AsyncSession, id: Union[UUID, str, int]) -> Optional[ModelType]:
        """
        Get a single record by ID asynchronously
        
        Args:
            db: Async database session
            id: Record ID
            
        Returns:
            The found record or None if not found
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi_async(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination asynchronously
        
        Args:
            db: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_async(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record asynchronously
        
        Args:
            db: Async database session
            obj_in: Create schema with data for the new record
            
        Returns:
            The created record
        """
        # Convert input to dictionary if it's not already
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            # Try Pydantic v2 model_dump method first
            if hasattr(obj_in, "model_dump"):
                obj_in_data = obj_in.model_dump()
            # Fallback to __dict__ for non-Pydantic objects
            else:
                obj_in_data = obj_in.__dict__
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_async(
        self, db: AsyncSession, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record asynchronously
        
        Args:
            db: Async database session
            db_obj: Existing database record
            obj_in: Update schema with data to update
            
        Returns:
            The updated record
        """
        obj_data = db_obj.__dict__
        
        # Convert input to dictionary if it's not already
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Try Pydantic v2 model_dump method first
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            # Fallback to __dict__ for non-Pydantic objects
            else:
                update_data = obj_in.__dict__
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove_async(self, db: AsyncSession, id: Union[UUID, str, int]) -> Optional[ModelType]:
        """
        Delete a record asynchronously
        
        Args:
            db: Async database session
            id: Record ID
            
        Returns:
            The deleted record or None if not found
        """
        obj = await self.get_async(db=db, id=id)
        if obj:
            db.delete(obj)
            await db.commit()
        return obj