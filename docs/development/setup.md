# Development Setup Guide

## Introduction

This document provides instructions for setting up the development environment for the Document Management and AI Chatbot System. The system is built using Python with FastAPI for the backend, PostgreSQL for relational data storage, and FAISS for vector storage. Follow these instructions to get your development environment up and running quickly.

## Prerequisites

Before you begin, ensure you have the following tools installed on your system:

- Python 3.10 or higher
- Poetry 1.5.1 or higher (for dependency management)
- Docker and Docker Compose (for containerized development)
- Git (for version control)
- An OpenAI API key (for LLM integration)

## Getting the Source Code

Clone the repository from GitHub:

```bash
git clone https://github.com/example/document-management-ai-chatbot.git
cd document-management-ai-chatbot
```

## Development Setup Options

You can set up the development environment in two ways: using Docker (recommended) or directly on your local machine.

## Option 1: Docker-based Setup (Recommended)

### Environment Configuration

Create a .env file in the src/backend directory by copying the example file:

```bash
cd src/backend
cp .env.example .env
```

### Customize Environment Variables

Edit the .env file to configure your environment. At minimum, you should update the following variables:

- `LLM_OPENAI_API_KEY`: Your OpenAI API key
- `SECURITY_JWT_SECRET`: A secure random string for JWT token signing

### Build and Start Containers

Use Docker Compose to build and start the application containers:

```bash
docker-compose up --build
```

This will:
- Build the Docker image for the application
- Start the PostgreSQL database container
- Start the application container with the FastAPI backend
- Mount the appropriate volumes for document storage and code changes

### Verify Setup

Once the containers are running, you can access the API documentation at http://localhost:8000/docs

### Running Tests in Docker

To run tests inside the Docker container:

```bash
docker-compose exec app poetry run pytest
```

## Option 2: Local Machine Setup

### Install Dependencies

Use Poetry to install the project dependencies:

```bash
cd src/backend
poetry install
```

### Database Setup

Install and configure PostgreSQL:

- Install PostgreSQL 14 or higher
- Create a database named 'document_management'
- Create a user with appropriate permissions

```bash
# Example PostgreSQL setup commands
createdb document_management
createuser -P postgres  # Set password when prompted
```

### Environment Configuration

Create and configure the .env file:

```bash
cp .env.example .env
# Edit .env with your database credentials and OpenAI API key
```

### Create Required Directories

Create directories for document storage and vector indices:

```bash
mkdir -p data/documents data/vector_indices
```

### Initialize Database

Run database migrations to set up the schema:

```bash
poetry run python -m scripts.generate_migrations
poetry run alembic upgrade head
```

### Run the Application

Start the FastAPI application:

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests Locally

Run the test suite:

```bash
poetry run pytest
```

## Development Workflow

### Code Structure

The project follows a modular structure:

- app/core: Core application settings and utilities
- app/api: API endpoints and routers
- app/models: SQLAlchemy ORM models
- app/schemas: Pydantic schemas for validation
- app/crud: Database CRUD operations
- app/services: Business logic services
- app/utils: Utility functions
- app/vector_store: Vector database implementation
- tests: Test suite

### Making Changes

When making changes to the codebase:

- Create a new branch for your feature or bugfix
- Write tests for your changes
- Ensure all tests pass before submitting a pull request
- Follow the coding standards defined in docs/development/coding-standards.md

### Database Migrations

If you make changes to the database models, generate new migrations:

```bash
poetry run python -m scripts.generate_migrations
poetry run alembic upgrade head
```

## Common Development Tasks

### Adding Dependencies

To add new dependencies to the project:

```bash
poetry add package-name  # For production dependencies
poetry add --dev package-name  # For development dependencies
```

### Running Linters and Formatters

Ensure code quality by running linters and formatters:

```bash
poetry run black app tests  # Format code
poetry run flake8 app tests  # Lint code
poetry run isort app tests  # Sort imports
poetry run mypy app  # Type checking
```

### Creating an Admin User

Create an admin user for testing:

```bash
poetry run python -m scripts.create_admin
```

### Rebuilding Vector Index

If you need to rebuild the vector index:

```bash
poetry run python -m scripts.rebuild_index
```

## Troubleshooting

Common issues and their solutions:

- Database connection errors: Check your PostgreSQL service is running and credentials are correct in .env
- FAISS index errors: Ensure the vector_indices directory exists and has write permissions
- OpenAI API errors: Verify your API key is valid and properly set in .env
- Docker permission issues: You may need to run Docker commands with sudo on Linux

## Next Steps

After setting up your development environment, you may want to:

- Review the API documentation at http://localhost:8000/docs
- Explore the codebase to understand the system architecture
- Check out docs/development/coding-standards.md for coding guidelines
- Read docs/development/testing.md for information on the testing strategy