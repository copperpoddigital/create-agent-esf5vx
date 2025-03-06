from typing import Any, Dict, Type
from sqlalchemy.orm import as_declarative, declared_attr  # SQLAlchemy 2.0.0+


@as_declarative()
class Base:
    """
    SQLAlchemy declarative base class that all ORM models inherit from.
    
    Provides common functionality and configuration for all database models
    in the Document Management and AI Chatbot System. This base class enables
    consistent table naming, standardized ID access, and serialization for API
    responses.
    """
    
    # Type annotations for IDE support
    __annotations__: Dict[str, Any]
    
    @declared_attr
    @classmethod
    def __tablename__(cls) -> str:
        """
        Automatically generates table name from class name.
        
        This eliminates the need to manually define __tablename__ in each model
        class and ensures consistent naming conventions across the application.
        
        Returns:
            str: Lowercase table name derived from class name
        """
        return cls.__name__.lower()
    
    def get_id(self) -> str:
        """
        Returns the primary key column name for the model.
        
        This provides a standard way to access the ID field across all models.
        
        Returns:
            str: Name of the primary key column (standardized as 'id')
        """
        return "id"
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Converts model instance to dictionary representation.
        
        This method is useful for serializing model instances to JSON for API
        responses or other data transfer needs.
        
        Returns:
            Dict[str, Any]: Dictionary of model attributes where keys are column
                           names and values are the corresponding attribute values
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }