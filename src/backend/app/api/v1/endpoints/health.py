"""
API endpoints for health checks in the Document Management and AI Chatbot System.
This module provides endpoints to verify the health and status of various system components
including the API itself, database connections, vector store, and LLM service.
"""

from fastapi import APIRouter, Depends, HTTPException, status  # version 0.95.0+
from sqlalchemy.orm import Session  # version 2.0.0+
from sqlalchemy.ext.asyncio import AsyncSession  # version 2.0.0+
import openai  # version 1.0.0+

from ..../../db.session import get_db_dependency, get_async_db_dependency
from ..../../vector_store.faiss_store import FAISSStore
from ..../../services.llm_service import get_openai_client
from ..../../core.logging import get_logger
from ..../../core.settings import vector_settings

# Create router and get logger
router = APIRouter()
logger = get_logger(__name__)

# Global FAISS store instance
faiss_store = None

def get_faiss_store() -> FAISSStore:
    """
    Returns the FAISS vector store instance, initializing it if necessary
    
    Returns:
        FAISSStore: Initialized FAISS store instance
    """
    global faiss_store
    if faiss_store is None:
        logger.info("Initializing FAISS store for health check")
        try:
            faiss_store = FAISSStore(vector_settings.VECTOR_INDEX_PATH)
            logger.info(f"FAISS store initialized with {faiss_store.count()} vectors")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS store: {str(e)}")
            # Return an uninitialized store for status check
            faiss_store = FAISSStore(vector_settings.VECTOR_INDEX_PATH)
    
    return faiss_store

@router.get("/live", status_code=status.HTTP_200_OK, tags=["health"])
def check_liveness():
    """
    Simple health check to verify the API is running
    
    Returns:
        dict: Status response indicating API is alive
    """
    logger.debug("Liveness check requested")
    return {"status": "ok", "service": "Document Management and AI Chatbot API"}

@router.get("/ready", status_code=status.HTTP_200_OK, tags=["health"])
def check_readiness(db: Session = Depends(get_db_dependency)):
    """
    Health check to verify the API is ready to accept requests
    
    Parameters:
        db: Database session from dependency injection
    
    Returns:
        dict: Status response indicating API readiness
    """
    logger.debug("Readiness check requested")
    try:
        # Check database connection by executing a simple query
        db.execute("SELECT 1")
        return {"status": "ok", "message": "API is ready to accept requests"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready to accept requests"
        )

@router.get("/dependencies", status_code=status.HTTP_200_OK, tags=["health"])
def check_dependencies(db: Session = Depends(get_db_dependency)):
    """
    Comprehensive health check to verify all system dependencies
    
    Parameters:
        db: Database session from dependency injection
    
    Returns:
        dict: Detailed status response for all system components
    """
    logger.debug("Dependencies check requested")
    
    # Initialize status dictionary with unknown status for all components
    components_status = {
        "database": {"status": "unknown", "details": None},
        "vector_store": {"status": "unknown", "details": None},
        "llm_service": {"status": "unknown", "details": None}
    }
    
    # Check database connection
    try:
        db.execute("SELECT 1")
        components_status["database"]["status"] = "healthy"
        components_status["database"]["details"] = "Connection successful"
    except Exception as e:
        components_status["database"]["status"] = "unhealthy"
        components_status["database"]["details"] = f"Connection failed: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check FAISS vector store
    try:
        store = get_faiss_store()
        vector_count = store.count()
        components_status["vector_store"]["status"] = "healthy"
        components_status["vector_store"]["details"] = f"Vector count: {vector_count}"
    except Exception as e:
        components_status["vector_store"]["status"] = "unhealthy"
        components_status["vector_store"]["details"] = f"FAISS store error: {str(e)}"
        logger.error(f"FAISS store health check failed: {str(e)}")
    
    # Check LLM service (OpenAI)
    try:
        client = get_openai_client()
        # Just check if we can access the client, no need to make an actual API call
        if client is not None:
            components_status["llm_service"]["status"] = "healthy"
            components_status["llm_service"]["details"] = "OpenAI client initialized"
        else:
            components_status["llm_service"]["status"] = "unhealthy"
            components_status["llm_service"]["details"] = "OpenAI client not initialized"
    except Exception as e:
        components_status["llm_service"]["status"] = "unhealthy"
        components_status["llm_service"]["details"] = f"OpenAI client error: {str(e)}"
        logger.error(f"LLM service health check failed: {str(e)}")
    
    # Calculate overall status
    overall_status = "healthy"
    for component, status_info in components_status.items():
        if status_info["status"] == "unhealthy":
            overall_status = "degraded"
            logger.warning(f"System health degraded: {component} is unhealthy")
    
    return {
        "status": overall_status,
        "timestamp": str(import datetime; datetime.datetime.now().isoformat()),
        "components": components_status
    }

@router.get("/async/ready", status_code=status.HTTP_200_OK, tags=["health"])
async def check_async_readiness(db: AsyncSession = Depends(get_async_db_dependency)):
    """
    Async health check to verify the API is ready to accept requests
    
    Parameters:
        db: Async database session from dependency injection
    
    Returns:
        dict: Status response indicating API readiness
    """
    logger.debug("Async readiness check requested")
    try:
        # Check database connection by executing a simple async query
        await db.execute("SELECT 1")
        return {"status": "ok", "message": "API is ready to accept requests"}
    except Exception as e:
        logger.error(f"Async readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready to accept requests"
        )

@router.get("/async/dependencies", status_code=status.HTTP_200_OK, tags=["health"])
async def check_async_dependencies(db: AsyncSession = Depends(get_async_db_dependency)):
    """
    Async comprehensive health check to verify all system dependencies
    
    Parameters:
        db: Async database session from dependency injection
    
    Returns:
        dict: Detailed status response for all system components
    """
    logger.debug("Async dependencies check requested")
    
    # Initialize status dictionary with unknown status for all components
    components_status = {
        "database": {"status": "unknown", "details": None},
        "vector_store": {"status": "unknown", "details": None},
        "llm_service": {"status": "unknown", "details": None}
    }
    
    # Check database connection
    try:
        await db.execute("SELECT 1")
        components_status["database"]["status"] = "healthy"
        components_status["database"]["details"] = "Connection successful"
    except Exception as e:
        components_status["database"]["status"] = "unhealthy"
        components_status["database"]["details"] = f"Connection failed: {str(e)}"
        logger.error(f"Async database health check failed: {str(e)}")
    
    # Check FAISS vector store
    try:
        store = get_faiss_store()
        vector_count = store.count()
        components_status["vector_store"]["status"] = "healthy"
        components_status["vector_store"]["details"] = f"Vector count: {vector_count}"
    except Exception as e:
        components_status["vector_store"]["status"] = "unhealthy"
        components_status["vector_store"]["details"] = f"FAISS store error: {str(e)}"
        logger.error(f"FAISS store health check failed: {str(e)}")
    
    # Check LLM service (OpenAI)
    try:
        client = get_openai_client()
        # Just check if we can access the client, no need to make an actual API call
        if client is not None:
            components_status["llm_service"]["status"] = "healthy"
            components_status["llm_service"]["details"] = "OpenAI client initialized"
        else:
            components_status["llm_service"]["status"] = "unhealthy"
            components_status["llm_service"]["details"] = "OpenAI client not initialized"
    except Exception as e:
        components_status["llm_service"]["status"] = "unhealthy"
        components_status["llm_service"]["details"] = f"OpenAI client error: {str(e)}"
        logger.error(f"LLM service health check failed: {str(e)}")
    
    # Calculate overall status
    overall_status = "healthy"
    for component, status_info in components_status.items():
        if status_info["status"] == "unhealthy":
            overall_status = "degraded"
            logger.warning(f"System health degraded: {component} is unhealthy")
    
    return {
        "status": overall_status,
        "timestamp": str(import datetime; datetime.datetime.now().isoformat()),
        "components": components_status
    }