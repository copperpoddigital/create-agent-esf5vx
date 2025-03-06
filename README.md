# Document Management and AI Chatbot System

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

## Technology Stack
### Core Technologies

- **Backend**: Python 3.10+, FastAPI 0.95.0+
- **Database**: PostgreSQL 14+, SQLAlchemy 2.0.0+
- **Vector Storage**: FAISS 1.7.4+
- **Document Processing**: PyMuPDF 1.21.0+
- **Embeddings**: Sentence Transformers 2.2.2+
- **LLM Integration**: OpenAI API
- **Authentication**: JWT with PyJWT 2.6.0+

### Development Tools

- **Dependency Management**: Poetry
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest, Coverage
- **Code Quality**: Black, Flake8, isort, mypy
- **CI/CD**: GitHub Actions

## Getting Started
### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Docker and Docker Compose (for containerized deployment)
- OpenAI API key (for LLM integration)

### Installation

#### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/example/document-management-ai-chatbot.git
cd document-management-ai-chatbot

# Install dependencies with Poetry
cd src/backend
poetry install

# Activate the virtual environment
poetry shell
```

#### Using Docker

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
   cp src/backend/.env.example src/backend/.env
   ```

2. Edit the `.env` file with your configuration:
   - Database connection details
   - OpenAI API key
   - JWT secret key
   - Other application settings

See the [Configuration Documentation](docs/development/setup.md) for detailed configuration options.

## Running the Application
### Development Mode

```bash
# Using Poetry
cd src/backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the shortcut command
poetry run dev
```

### Production Mode

```bash
# Using Docker
cd src/backend
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

For detailed API documentation, see the [API Documentation](docs/api/README.md).

## Project Structure
```
├── src/
│   ├── backend/             # Backend application code
│   │   ├── app/             # Application modules
│   │   ├── migrations/      # Database migrations
│   │   ├── scripts/         # Utility scripts
│   │   ├── tests/           # Test suite
│   │   ├── main.py          # Application entry point
│   │   └── ...              # Configuration files
├── infrastructure/          # Infrastructure as code
│   ├── terraform/           # Terraform configurations
│   ├── docker/              # Docker configurations
│   └── ...                  # Other infrastructure components
├── docs/                    # Documentation
│   ├── api/                 # API documentation
│   ├── architecture/        # Architecture documentation
│   ├── development/         # Development guides
│   └── ...                  # Other documentation
├── scripts/                 # Project-level scripts
├── .github/                 # GitHub workflows and templates
└── ...                      # Project root files
```

## Documentation
Comprehensive documentation is available in the [docs](docs/) directory:

- [System Architecture](docs/architecture/system-overview.md)
- [API Documentation](docs/api/README.md)
- [Development Guide](docs/development/setup.md)
- [Operations Guide](docs/operations/deployment.md)
- [User Guide](docs/user-guide/getting-started.md)

## Contributing
Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.