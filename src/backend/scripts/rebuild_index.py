#!/usr/bin/env python3
"""
Script to rebuild the FAISS vector index for the Document Management and AI Chatbot System.

This script is used for maintenance operations to recreate the vector index from document chunks
stored in the database. This can be necessary after data corruption, index optimization needs,
or when migrating to a new server.

Usage:
    python rebuild_index.py [--force] [--batch-size BATCH_SIZE] [--verbose]

Options:
    --force         Force rebuild even if index exists
    --batch-size    Number of document chunks to process in a batch (default: 100)
    --verbose       Enable verbose output
"""

import os
import sys
import argparse  # standard library
import logging  # standard library
from typing import List

import tqdm  # tqdm 4.64.0+
from sqlalchemy import select  # sqlalchemy 2.0.0+

# Import internal modules
from ..app.db.session import get_db
from ..app.models.document import Document
from ..app.models.document_chunk import DocumentChunk
from ..app.vector_store.faiss_store import FAISSStore
from ..app.services.embedding_service import generate_embedding
from ..app.utils.vector_utils import generate_embedding_id
from ..app.core.config import vector_settings

# Set up module logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the script with appropriate format and level.
    
    Args:
        verbose: If True, sets log level to DEBUG, otherwise INFO
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Add handler to the logger if it doesn't already have one
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    logger.setLevel(log_level)
    logger.info("Logging configured with level: %s", "DEBUG" if verbose else "INFO")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the script.
    
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Rebuild the FAISS vector index for all document chunks in the database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if index already exists"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of document chunks to process in a batch"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def rebuild_index(force: bool, batch_size: int) -> bool:
    """
    Rebuilds the FAISS vector index from document chunks in the database.
    
    Args:
        force: If True, force rebuild even if index exists
        batch_size: Number of document chunks to process in each batch
    
    Returns:
        True if rebuild was successful, False otherwise
    """
    try:
        # Initialize FAISS vector store
        index_path = vector_settings.VECTOR_INDEX_PATH
        logger.info(f"Using vector index path: {index_path}")
        vector_store = FAISSStore(index_path=index_path)
        
        # Check if index exists and force flag is not set
        if os.path.exists(f"{index_path}.faiss") and not force:
            logger.warning(f"Index already exists at {index_path}.faiss. Use --force to rebuild.")
            return False
        
        # Clear existing index
        logger.info("Clearing existing index")
        vector_store.clear()
        
        # Get database session
        with get_db() as db:
            # Get all available documents
            logger.info("Querying available documents from database")
            documents_query = select(Document).where(Document.is_available() == True)
            documents = db.execute(documents_query).scalars().all()
            
            if not documents:
                logger.warning("No available documents found in database")
                return False
            
            # Get document IDs
            document_ids = [doc.id for doc in documents]
            logger.info(f"Found {len(document_ids)} available documents")
            
            # Get all document chunks for available documents
            chunks_query = select(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids))
            chunks = db.execute(chunks_query).scalars().all()
            
            if not chunks:
                logger.warning("No document chunks found for available documents")
                return False
            
            logger.info(f"Found {len(chunks)} document chunks to process")
            
            # Process chunks in batches
            total_chunks = len(chunks)
            processed_chunks = 0
            successful_chunks = 0
            
            # Process chunks in batches
            for i in tqdm.tqdm(range(0, total_chunks, batch_size), desc="Processing batches"):
                batch = chunks[i:i+batch_size]
                batch_embeddings = []
                batch_embedding_ids = []
                
                # Generate embeddings for each chunk in batch
                for chunk in batch:
                    try:
                        # Generate embedding from chunk content
                        embedding = generate_embedding(chunk.content)
                        
                        # Generate a unique embedding ID
                        embedding_id = generate_embedding_id()
                        
                        batch_embeddings.append(embedding)
                        batch_embedding_ids.append(embedding_id)
                        
                        # Update chunk with new embedding ID
                        chunk.update_embedding_id(embedding_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk.id}: {str(e)}")
                        continue
                
                # Add batch of embeddings to vector store
                if batch_embeddings:
                    success = vector_store.add_vectors(batch_embeddings, batch_embedding_ids)
                    if success:
                        successful_chunks += len(batch_embeddings)
                    else:
                        logger.error(f"Failed to add batch of {len(batch_embeddings)} vectors to FAISS")
                
                # Commit changes to database
                db.commit()
                
                # Update progress counter
                processed_chunks += len(batch)
                logger.debug(f"Processed {processed_chunks}/{total_chunks} chunks")
            
            # Save the updated vector store to disk
            logger.info("Saving FAISS index to disk")
            vector_store.save()
            
            logger.info(f"Successfully rebuilt FAISS index with {successful_chunks} vectors from {processed_chunks} chunks")
            return True
    
    except Exception as e:
        logger.exception(f"Error rebuilding index: {str(e)}")
        return False


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.verbose)
    
    logger.info("Starting FAISS index rebuild")
    logger.info(f"Force rebuild: {args.force}")
    logger.info(f"Batch size: {args.batch_size}")
    
    # Rebuild the index
    success = rebuild_index(force=args.force, batch_size=args.batch_size)
    
    if success:
        logger.info("FAISS index rebuild completed successfully")
        return 0
    else:
        logger.error("FAISS index rebuild failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())