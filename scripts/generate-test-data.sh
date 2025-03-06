#!/bin/bash
# generate-test-data.sh
# This script generates test data for the Document Management and AI Chatbot System.
# It creates sample users, documents, document chunks, queries, and feedback entries in the database for testing and development purposes.

set -e

# Default values
DB_URL=${DATABASE_URL:-"postgresql://postgres:postgres@localhost:5432/docmanagement"}
NUM_USERS=${NUM_USERS:-5}
NUM_DOCUMENTS=${NUM_DOCUMENTS:-10}
NUM_QUERIES=${NUM_QUERIES:-20}
NUM_FEEDBACK=${NUM_FEEDBACK:-15}
SAMPLE_PDF_PATH=${SAMPLE_PDF_PATH:-"../src/backend/tests/fixtures/documents/sample.pdf"}

# Function to check dependencies
check_dependencies() {
  echo "Checking dependencies..."
  
  # Check if Python is installed
  if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    return 1
  fi
  
  # Check if PostgreSQL client is installed
  if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL client (psql) is not installed."
    return 1
  fi
  
  # Check if required Python packages are installed
  REQUIRED_PACKAGES=("sqlalchemy" "pymupdf" "sentence_transformers" "faiss")
  MISSING_PACKAGES=()
  
  for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" &> /dev/null; then
      MISSING_PACKAGES+=("$package")
    fi
  done
  
  if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "Error: The following Python packages are missing:"
    for package in "${MISSING_PACKAGES[@]}"; do
      echo "  - $package"
    done
    echo "Please install them using: pip install ${MISSING_PACKAGES[*]}"
    return 1
  fi
  
  echo "All dependencies are installed."
  return 0
}

# Function to run Python scripts
run_python_script() {
  PYTHON_CODE="$1"
  python3 -c "$PYTHON_CODE"
  return $?
}

# Function to create test users
create_test_users() {
  local count=$1
  echo "Creating $count test users..."
  
  # Create an admin user first using the existing script
  echo "Creating admin user..."
  python3 ../src/backend/scripts/create_admin.py --username admin --email admin@example.com --password Admin123!
  
  # Create regular users
  PYTHON_CODE=$(cat <<EOL
import sys
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import the necessary models and functions
sys.path.append('../src/backend')
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Connect to the database
engine = create_engine('${DB_URL}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Create regular users
    user_ids = []
    for i in range(2, ${count} + 1):  # Start from 2 since we already created admin
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=get_password_hash(f"Password{i}!"),
            role=UserRole.regular,
            is_active=True,
            created_at=datetime.now()
        )
        db.add(user)
        user_ids.append(str(user_id))
    
    db.commit()
    print(",".join(user_ids))
except Exception as e:
    db.rollback()
    print(f"Error creating users: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    db.close()
EOL
)

  USER_IDS=$(run_python_script "$PYTHON_CODE")
  if [ $? -ne 0 ]; then
    echo "Error creating test users."
    return 1
  fi
  
  echo "Created test users with IDs: $USER_IDS"
  echo $USER_IDS
}

# Function to create test documents
create_test_documents() {
  local count=$1
  local user_ids=$2
  echo "Creating $count test documents..."
  
  # Check if sample PDF exists
  if [ ! -f "$SAMPLE_PDF_PATH" ]; then
    echo "Error: Sample PDF file not found at $SAMPLE_PDF_PATH"
    return 1
  fi
  
  # Create temporary directory for sample documents
  TEMP_DIR=$(mktemp -d)
  cp "$SAMPLE_PDF_PATH" "$TEMP_DIR/sample.pdf"
  
  PYTHON_CODE=$(cat <<EOL
import sys
import os
import uuid
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import fitz  # PyMuPDF
import numpy as np

# Try to import vector-related packages, with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    has_sentence_transformers = True
except ImportError:
    has_sentence_transformers = False
    print("Warning: sentence_transformers not available, using random vectors instead", file=sys.stderr)

try:
    import faiss
    has_faiss = True
except ImportError:
    has_faiss = False
    print("Warning: faiss not available, using random vector IDs instead", file=sys.stderr)

# Import the necessary models
sys.path.append('../src/backend')
try:
    from app.models.document import Document, DocumentChunk, DocumentStatus
except ImportError:
    # If models aren't found, define simple versions here
    from enum import Enum
    
    class DocumentStatus(Enum):
        processing = "processing"
        available = "available"
        error = "error"
        deleted = "deleted"
    
    class Document:
        def __init__(self, id, title, filename, size_bytes, upload_date, status, file_path, uploader_id):
            self.id = id
            self.title = title
            self.filename = filename
            self.size_bytes = size_bytes
            self.upload_date = upload_date
            self.status = status
            self.file_path = file_path
            self.uploader_id = uploader_id
    
    class DocumentChunk:
        def __init__(self, id, document_id, chunk_index, content, token_count, embedding_id):
            self.id = id
            self.document_id = document_id
            self.chunk_index = chunk_index
            self.content = content
            self.token_count = token_count
            self.embedding_id = embedding_id

# Connect to the database
engine = create_engine('${DB_URL}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# User IDs array
user_ids = "${user_ids}".split(',')

# Sample document text for chunks
sample_texts = [
    "This is a sample document about artificial intelligence and machine learning.",
    "Vector databases are essential for semantic search applications.",
    "Document management systems help organize and retrieve information efficiently.",
    "Natural language processing enables computers to understand human language.",
    "Embeddings capture the semantic meaning of text in high-dimensional space.",
    "AI chatbots can provide intelligent responses based on document content.",
    "Information retrieval systems find relevant documents based on user queries.",
    "Knowledge management is crucial for organizational success.",
    "FastAPI provides a modern framework for building APIs with Python.",
    "FAISS is a library for efficient similarity search of dense vectors."
]

# Initialize sentence transformer if available
if has_sentence_transformers:
    try:
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    except Exception as e:
        print(f"Warning: Error initializing SentenceTransformer: {e}", file=sys.stderr)
        has_sentence_transformers = False

# Generate an embedding for text
def generate_embedding(text):
    if has_sentence_transformers:
        try:
            return model.encode(text)
        except:
            pass
    # Fallback to random vector
    return np.random.rand(768).astype(np.float32)  # Use 768 dimensions as default

try:
    # Get sample PDF content
    doc = fitz.open("${TEMP_DIR}/sample.pdf")
    sample_pdf_text = ""
    for page in doc:
        sample_pdf_text += page.get_text()
    doc.close()
    
    # Create documents
    document_ids = []
    for i in range(1, ${count} + 1):
        # Select random user as uploader
        uploader_id = uuid.UUID(random.choice(user_ids))
        
        # Create document
        document_id = uuid.uuid4()
        document = Document(
            id=document_id,
            title=f"Test Document {i}",
            filename=f"test_document_{i}.pdf",
            size_bytes=len(sample_pdf_text) * 2,  # Approximate size
            upload_date=datetime.now(),
            status=DocumentStatus.processing,
            file_path=f"${TEMP_DIR}/sample.pdf",
            uploader_id=uploader_id
        )
        db.add(document)
        
        # Create document chunks
        num_chunks = random.randint(3, 7)
        for j in range(num_chunks):
            chunk_id = uuid.uuid4()
            # Select random text or use part of PDF text
            if j == 0:
                content = sample_texts[random.randint(0, len(sample_texts) - 1)]
            else:
                start = random.randint(0, max(0, len(sample_pdf_text) - 500))
                content = sample_pdf_text[start:start + min(500, len(sample_pdf_text) - start)]
            
            # Generate embedding and ID
            embedding = generate_embedding(content)
            embedding_id = f"embedding_{chunk_id}"
            
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=j,
                content=content,
                token_count=len(content.split()),
                embedding_id=embedding_id
            )
            db.add(chunk)
        
        # Update document status to available
        document.status = DocumentStatus.available
        document_ids.append(str(document_id))
    
    db.commit()
    print(",".join(document_ids))
except Exception as e:
    db.rollback()
    print(f"Error creating documents: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    db.close()
EOL
)

  DOCUMENT_IDS=$(run_python_script "$PYTHON_CODE")
  if [ $? -ne 0 ]; then
    echo "Error creating test documents."
    return 1
  fi
  
  # Clean up temporary directory
  rm -rf "$TEMP_DIR"
  
  echo "Created test documents with IDs: $DOCUMENT_IDS"
  echo $DOCUMENT_IDS
}

# Function to create test queries
create_test_queries() {
  local count=$1
  local user_ids=$2
  local document_ids=$3
  echo "Creating $count test queries..."
  
  PYTHON_CODE=$(cat <<EOL
import sys
import uuid
import random
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import the necessary models
sys.path.append('../src/backend')
try:
    from app.models.query import Query
except ImportError:
    # If model isn't found, define a simple version here
    class Query:
        def __init__(self, id, user_id, query_text, query_time, response_text, context_documents, embedding_id):
            self.id = id
            self.user_id = user_id
            self.query_text = query_text
            self.query_time = query_time
            self.response_text = response_text
            self.context_documents = context_documents
            self.embedding_id = embedding_id

# Connect to the database
engine = create_engine('${DB_URL}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# User IDs and Document IDs arrays
user_ids = "${user_ids}".split(',')
document_ids = "${document_ids}".split(',')

# Sample query templates
query_templates = [
    "What is artificial intelligence?",
    "How do vector databases work?",
    "Explain document management systems.",
    "What are the benefits of natural language processing?",
    "How are embeddings used in semantic search?",
    "What are the capabilities of AI chatbots?",
    "How does information retrieval work?",
    "Why is knowledge management important?",
    "What are the features of FastAPI?",
    "How does FAISS implement efficient similarity search?"
]

# Sample AI responses
ai_responses = [
    "Artificial intelligence refers to systems designed to perform tasks that typically require human intelligence.",
    "Vector databases store and retrieve high-dimensional vectors for similarity search, enabling semantic search applications.",
    "Document management systems help organizations store, manage, and track electronic documents and images of paper-based information.",
    "Natural language processing enables more natural human-computer interaction and can extract insights from unstructured text data.",
    "Embeddings represent text in high-dimensional vector space where semantic similarity corresponds to vector proximity.",
    "AI chatbots can understand and respond to user queries, learn from interactions, and provide personalized assistance.",
    "Information retrieval systems identify and retrieve relevant documents based on user queries using techniques like vector search.",
    "Knowledge management enhances decision-making, innovation, and organizational efficiency by effectively utilizing information assets.",
    "FastAPI is a high-performance Python framework for building APIs with automatic documentation and validation.",
    "FAISS uses specialized data structures and algorithms to efficiently search for similar vectors in high-dimensional space."
]

try:
    # Create queries
    query_ids = []
    for i in range(1, ${count} + 1):
        # Select random user
        user_id = uuid.UUID(random.choice(user_ids))
        
        # Select random query template and response
        template_index = random.randint(0, len(query_templates) - 1)
        query_text = query_templates[template_index]
        response_text = ai_responses[template_index]
        
        # Select random documents as context
        num_context_docs = min(random.randint(1, 3), len(document_ids))
        context_doc_ids = random.sample(document_ids, num_context_docs)
        
        # Create context JSON
        context_documents = []
        for doc_id in context_doc_ids:
            # Try to get a random chunk from this document
            try:
                stmt = f"SELECT id, content FROM document_chunk WHERE document_id = '{doc_id}' LIMIT 1"
                chunk = db.execute(stmt).fetchone()
                if chunk:
                    context_documents.append({
                        "document_id": doc_id,
                        "chunk_id": str(chunk[0]),
                        "content": chunk[1],
                        "similarity_score": round(random.uniform(0.7, 0.95), 2)
                    })
            except:
                # If table doesn't exist or query fails, create dummy context
                context_documents.append({
                    "document_id": doc_id,
                    "chunk_id": str(uuid.uuid4()),
                    "content": "Sample content for document chunk",
                    "similarity_score": round(random.uniform(0.7, 0.95), 2)
                })
        
        # Create query
        query_id = uuid.uuid4()
        query = Query(
            id=query_id,
            user_id=user_id,
            query_text=query_text,
            query_time=datetime.now(),
            response_text=response_text,
            context_documents=json.dumps(context_documents),
            embedding_id=f"embedding_{query_id}"  # In a real system, this would be a vector ID
        )
        db.add(query)
        query_ids.append(str(query_id))
    
    db.commit()
    print(",".join(query_ids))
except Exception as e:
    db.rollback()
    print(f"Error creating queries: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    db.close()
EOL
)

  QUERY_IDS=$(run_python_script "$PYTHON_CODE")
  if [ $? -ne 0 ]; then
    echo "Error creating test queries."
    return 1
  fi
  
  echo "Created test queries with IDs: $QUERY_IDS"
  echo $QUERY_IDS
}

# Function to create test feedback
create_test_feedback() {
  local count=$1
  local user_ids=$2
  local query_ids=$3
  echo "Creating $count test feedback entries..."
  
  PYTHON_CODE=$(cat <<EOL
import sys
import uuid
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import the necessary models
sys.path.append('../src/backend')
try:
    from app.models.feedback import Feedback
except ImportError:
    # If model isn't found, define a simple version here
    class Feedback:
        def __init__(self, id, query_id, user_id, rating, comments, feedback_time):
            self.id = id
            self.query_id = query_id
            self.user_id = user_id
            self.rating = rating
            self.comments = comments
            self.feedback_time = feedback_time

# Connect to the database
engine = create_engine('${DB_URL}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# User IDs and Query IDs arrays
user_ids = "${user_ids}".split(',')
query_ids = "${query_ids}".split(',')

# Sample feedback comments
positive_comments = [
    "Great response! Very helpful.",
    "Exactly what I was looking for.",
    "Clear and concise explanation.",
    "Answered my question perfectly.",
    "Very informative, thank you!"
]

neutral_comments = [
    "Somewhat helpful, but could be more detailed.",
    "The answer was okay.",
    "Partially addressed my question.",
    "Good but missing some information."
]

negative_comments = [
    "Not very helpful.",
    "Did not answer my question.",
    "Confusing explanation.",
    "Missing important details.",
    "Completely irrelevant to what I asked."
]

try:
    # Create feedback entries
    feedback_ids = []
    for i in range(1, ${count} + 1):
        # Select random user and query
        user_id = uuid.UUID(random.choice(user_ids))
        query_id = uuid.UUID(random.choice(query_ids))
        
        # Generate random rating (1-5)
        rating = random.randint(1, 5)
        
        # Select appropriate comment based on rating
        if rating >= 4:
            comments = random.choice(positive_comments)
        elif rating == 3:
            comments = random.choice(neutral_comments)
        else:
            comments = random.choice(negative_comments)
        
        # Create feedback
        feedback_id = uuid.uuid4()
        feedback = Feedback(
            id=feedback_id,
            query_id=query_id,
            user_id=user_id,
            rating=rating,
            comments=comments,
            feedback_time=datetime.now()
        )
        db.add(feedback)
        feedback_ids.append(str(feedback_id))
    
    db.commit()
    print(",".join(feedback_ids))
except Exception as e:
    db.rollback()
    print(f"Error creating feedback: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    db.close()
EOL
)

  FEEDBACK_IDS=$(run_python_script "$PYTHON_CODE")
  if [ $? -ne 0 ]; then
    echo "Error creating test feedback."
    return 1
  fi
  
  echo "Created test feedback entries with IDs: $FEEDBACK_IDS"
  echo $FEEDBACK_IDS
}

# Main function
main() {
  echo "Generating test data for Document Management and AI Chatbot System..."
  echo "Using database: $DB_URL"
  
  # Check dependencies
  check_dependencies
  if [ $? -ne 0 ]; then
    echo "Missing dependencies. Please install required packages."
    return 1
  fi
  
  # Create test users
  USER_IDS=$(create_test_users $NUM_USERS)
  if [ $? -ne 0 ]; then
    echo "Failed to create test users."
    return 2
  fi
  
  # Create test documents
  DOCUMENT_IDS=$(create_test_documents $NUM_DOCUMENTS "$USER_IDS")
  if [ $? -ne 0 ]; then
    echo "Failed to create test documents."
    return 3
  fi
  
  # Create test queries
  QUERY_IDS=$(create_test_queries $NUM_QUERIES "$USER_IDS" "$DOCUMENT_IDS")
  if [ $? -ne 0 ]; then
    echo "Failed to create test queries."
    return 4
  fi
  
  # Create test feedback
  FEEDBACK_IDS=$(create_test_feedback $NUM_FEEDBACK "$USER_IDS" "$QUERY_IDS")
  if [ $? -ne 0 ]; then
    echo "Failed to create test feedback."
    return 5
  fi
  
  # Print summary
  echo "=============================================="
  echo "Test data generation complete!"
  echo "=============================================="
  echo "Created:"
  echo "  - $NUM_USERS users"
  echo "  - $NUM_DOCUMENTS documents"
  echo "  - $NUM_QUERIES queries"
  echo "  - $NUM_FEEDBACK feedback entries"
  echo "=============================================="
  
  return 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --users)
      NUM_USERS="$2"
      shift 2
      ;;
    --documents)
      NUM_DOCUMENTS="$2"
      shift 2
      ;;
    --queries)
      NUM_QUERIES="$2"
      shift 2
      ;;
    --feedback)
      NUM_FEEDBACK="$2"
      shift 2
      ;;
    --db-url)
      DB_URL="$2"
      shift 2
      ;;
    --sample-pdf)
      SAMPLE_PDF_PATH="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --users NUMBER        Number of test users to create (default: 5)"
      echo "  --documents NUMBER    Number of test documents to create (default: 10)"
      echo "  --queries NUMBER      Number of test queries to create (default: 20)"
      echo "  --feedback NUMBER     Number of test feedback entries to create (default: 15)"
      echo "  --db-url URL          Database connection URL (default: from DATABASE_URL environment variable)"
      echo "  --sample-pdf PATH     Path to sample PDF file (default: ../src/backend/tests/fixtures/documents/sample.pdf)"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information."
      exit 1
      ;;
  esac
done

# Run the main function
main
exit $?