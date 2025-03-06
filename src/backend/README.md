# Document Management and AI Chatbot System Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI: 0.95.0+](https://img.shields.io/badge/FastAPI-0.95.0%2B-green.svg)](https://fastapi.tiangolo.com/)

A comprehensive backend solution for document management with AI-powered search capabilities. This system provides intelligent document search and retrieval through vector embeddings and AI-powered chatbot responses.

## Features

- **Document Management**: Upload, list, retrieve, and delete PDF documents
- **Vector Search**: Semantic search using FAISS vector database
- **AI Chatbot**: Generate contextual responses based on document content using LLM integration
- **Reinforcement Learning**: Improve responses over time based on user feedback
- **Authentication**: Secure JWT-based authentication and role-based access control

## System Architecture

The system follows a modular architecture with clear component boundaries:

- **API Layer**: FastAPI-based REST API endpoints
- **Document Processor**: Extracts text from PDFs and generates vector embeddings
- **Vector Engine**: Manages FAISS index for similarity search
- **LLM Connector**: Interfaces with OpenAI API for response generation
- **Feedback Manager**: Collects and processes user feedback
- **Data Store**: PostgreSQL database for metadata and SQLAlchemy ORM

The system is designed as a monolithic application initially but with clear boundaries for potential microservice extraction in the future.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Docker and Docker Compose (for containerized deployment)
- OpenAI API key (for LLM integration)

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/example/document-management-ai-chatbot.git
cd document-management-ai-chatbot/src/backend

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Using Docker

```bash
# Clone the repository
git clone https://github.com/example/document-management-ai-chatbot.git
cd document-management-ai-chatbot/src/backend

# Build and start the containers
docker-compose up -d
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
   - Database connection details
   - OpenAI API key
   - JWT secret key
   - Other application settings

3. Key configuration sections:
   - **Application Settings**: General application configuration
   - **Database Settings**: PostgreSQL connection parameters
   - **Security Settings**: JWT and password policies
   - **Vector Search Settings**: FAISS configuration
   - **LLM Settings**: OpenAI API configuration
   - **Document Settings**: Document processing parameters
   - **Feedback Settings**: Reinforcement learning configuration

## Database Setup

Initialize the database with the following commands:

```bash
# Using Poetry
poetry run alembic upgrade head

# Create an admin user
poetry run python scripts/create_admin.py
```

When using Docker, the database migrations are applied automatically on startup.

## Running the Application

### Development Mode

```bash
# Using Poetry
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the shortcut command
poetry run dev
```

### Production Mode

```bash
# Using Poetry
poetry run uvicorn main:app --host 0.0.0.0 --port 8000

# Or use the shortcut command
poetry run start
```

### Using Docker

```bash
docker-compose up -d
```

The application will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The API is organized into the following main endpoints:

- `/api/v1/auth`: Authentication endpoints
- `/api/v1/documents`: Document management endpoints
- `/api/v1/query`: Vector search and chatbot endpoints
- `/api/v1/feedback`: Feedback and reinforcement learning endpoints
- `/api/v1/health`: Health check endpoint

## Key API Endpoints

### Authentication

- `POST /api/v1/auth/token`: Obtain JWT token
- `POST /api/v1/auth/refresh`: Refresh JWT token

### Document Management

- `POST /api/v1/documents`: Upload a document
- `GET /api/v1/documents`: List documents
- `GET /api/v1/documents/{document_id}`: Get document details
- `GET /api/v1/documents/{document_id}/download`: Download original document
- `DELETE /api/v1/documents/{document_id}`: Delete a document

### Vector Search and Chatbot

- `POST /api/v1/query`: Submit a search query
- `GET /api/v1/query/{query_id}`: Get query results
- `GET /api/v1/query`: List query history

### Feedback and Reinforcement Learning

- `POST /api/v1/feedback`: Submit feedback on a response
- `GET /api/v1/feedback/query/{query_id}`: Get feedback for a query
- `POST /api/v1/feedback/reinforce`: Trigger reinforcement learning (admin only)

## Development

### Project Structure

```
src/backend/
├── app/                    # Application code
│   ├── api/                # API endpoints
│   │   ├── v1/             # API version 1
│   │   │   └── endpoints/  # API route handlers
│   │   └── dependencies.py # API dependencies
│   ├── core/               # Core application components
│   ├── crud/               # Database CRUD operations
│   ├── db/                 # Database configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   └── vector_store/       # Vector database integration
├── data/                   # Data storage
│   ├── documents/          # Document storage
│   └── vector_indices/     # FAISS indices
├── migrations/             # Alembic migrations
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── .env.example            # Example environment variables
├── alembic.ini             # Alembic configuration
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker build configuration
├── main.py                 # Application entry point
├── pyproject.toml          # Poetry configuration
└── README.md               # This file
```

### Testing

Run the test suite with:

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=app --cov-report=term-missing

# Or use the shortcut command
poetry run test-cov
```

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Linting with flake8
poetry run flake8 app tests

# Formatting with black
poetry run black app tests

# Import sorting with isort
poetry run isort app tests

# Type checking with mypy
poetry run mypy app

# Security checks with bandit
poetry run bandit -r app
```

You can use the shortcut commands defined in pyproject.toml:

```bash
poetry run lint      # Run flake8
poetry run format    # Run black
poetry run sort-imports  # Run isort
poetry run type-check    # Run mypy
poetry run security-check  # Run bandit
```

## Deployment

The application is designed to be deployed as a containerized application using Docker. The provided Dockerfile and docker-compose.yml files can be used for both development and production deployments.

For production deployment, consider the following:

1. Use a proper secret management solution for sensitive values in the .env file
2. Configure a reverse proxy (like Nginx) in front of the application
3. Set up proper monitoring and logging
4. Use a managed PostgreSQL service or properly configured PostgreSQL instance
5. Configure backups for both the database and document storage

## Environment Variables

The application is configured using environment variables. See `.env.example` for a complete list of available configuration options with descriptions and default values.

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check PostgreSQL is running and accessible
   - Verify database credentials in .env file
   - Ensure database exists and migrations are applied

2. **Vector search not working**:
   - Check FAISS index path is correctly configured
   - Verify documents have been properly processed
   - Check logs for any errors during document processing

3. **LLM integration issues**:
   - Verify OpenAI API key is valid
   - Check network connectivity to OpenAI API
   - Review request/response logs for API errors

4. **Container issues**:
   - Check Docker logs: `docker-compose logs -f`
   - Verify container health: `docker-compose ps`
   - Rebuild containers if needed: `docker-compose build --no-cache`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

Please ensure your code passes all tests and follows the project's coding standards.

## License

This project is licensed under the MIT License - see the LICENSE file for details.