# Contributing to Document Management and AI Chatbot System

Thank you for your interest in contributing to the Document Management and AI Chatbot System. This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We are committed to fostering an open and welcoming environment for all contributors. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) in all your interactions with the project.

## Getting Started

### Prerequisites

Before you begin contributing, ensure you have the following installed:

- Python 3.10 or higher
- Poetry 1.5.1 or higher
- Docker and Docker Compose (for containerized development)
- Git

### Setting Up the Development Environment

Follow the detailed instructions in our [Development Setup Guide](docs/development/setup.md) to set up your local development environment.

In summary:

1. Fork the repository on GitHub
2. Clone your fork locally
   ```bash
   git clone https://github.com/your-username/document-management-ai-chatbot.git
   cd document-management-ai-chatbot
   ```
3. Set up the development environment
   ```bash
   cd src/backend
   cp .env.example .env  # Configure with your settings
   poetry install
   ```
4. Run the application
   ```bash
   poetry run uvicorn main:app --reload
   ```

## Development Workflow

We follow a Git Flow-inspired branching strategy:

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Workflow Steps

1. Create a new branch from `develop` for your work
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following our [Coding Standards](docs/development/coding-standards.md)

3. Write tests for your changes following our [Testing Guidelines](docs/development/testing.md)

4. Run tests locally to ensure they pass
   ```bash
   cd src/backend
   poetry run pytest
   ```

5. Run linters and formatters
   ```bash
   poetry run black app tests
   poetry run flake8 app tests
   poetry run isort app tests
   poetry run mypy app
   ```

6. Commit your changes with clear, descriptive commit messages
   ```bash
   git add .
   git commit -m "feat: Add vector search caching for improved performance"
   ```

7. Push your branch to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

8. Create a pull request to the `develop` branch of the main repository

### Commit Message Guidelines

We follow conventional commits for clear, structured commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding or modifying tests
- `chore:` for maintenance tasks

Example: `feat: Implement vector search caching`

## Pull Request Process

1. **Create a Pull Request (PR)** from your feature branch to the `develop` branch of the main repository

2. **Fill out the PR template** with all required information, including:
   - Description of the changes
   - Related issue(s)
   - Type of change (feature, bugfix, etc.)
   - Checklist of completed items

3. **Wait for CI checks** to complete. All checks must pass before a PR can be merged:
   - Code quality checks
   - Unit and integration tests
   - Security scans
   - Build verification

4. **Address review feedback** from maintainers and make necessary changes

5. **Update your branch** if needed:
   ```bash
   git checkout feature/your-feature-name
   git fetch origin develop
   git rebase origin/develop
   git push --force-with-lease origin feature/your-feature-name
   ```

6. Once approved and all checks pass, a maintainer will merge your PR

### PR Review Criteria

Pull requests are reviewed based on the following criteria:

- Code quality and adherence to project standards
- Test coverage and quality
- Documentation completeness
- Performance considerations
- Security implications
- Overall design and architecture fit

For more details on our CI/CD process, see the [CI/CD documentation](docs/development/ci-cd.md).

## Coding Standards

We maintain strict coding standards to ensure code quality and consistency. Please refer to our detailed [Coding Standards](docs/development/coding-standards.md) document for comprehensive guidelines.

Key highlights include:

### Python Style

- Follow PEP 8 with some project-specific modifications
- Use Black for code formatting with a line length of 88 characters
- Use isort for import sorting
- Use type hints for all function parameters and return values
- Write comprehensive docstrings in Google style

### Project Structure

- Follow the established project structure
- Place new modules in the appropriate directories
- Maintain separation of concerns between components

### Error Handling

- Use custom exception classes for domain-specific errors
- Catch specific exceptions, not `Exception` (unless absolutely necessary)
- Include meaningful error messages
- Log exceptions with appropriate context

### Asynchronous Programming

- Use `async`/`await` consistently throughout an execution path
- Don't mix synchronous and asynchronous code without careful consideration
- Use `asyncio` primitives for coordination

All code must pass our automated quality checks before it can be merged.

## Testing Requirements

All contributions must include appropriate tests. Please refer to our [Testing Guidelines](docs/development/testing.md) for detailed information.

### Testing Expectations

- **Unit Tests**: Required for all new functions and classes
- **Integration Tests**: Required for API endpoints and service interactions
- **Code Coverage**: Minimum 80% overall, 90% for core business logic

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=app --cov-report=term-missing

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
```

### Test Quality

Tests should be:

- Focused on a single behavior
- Independent of each other
- Fast and reliable
- Easy to understand and maintain

The CI pipeline will automatically run tests on your pull request, but you should always run tests locally before submitting.

## Documentation

Good documentation is essential for the project. Please follow these guidelines for documentation:

### Code Documentation

- Include docstrings for all modules, classes, methods, and functions
- Follow Google-style docstring format
- Document parameters, return values, and exceptions
- Include examples for complex functions

### Project Documentation

- Update relevant documentation when making changes
- Create new documentation for new features
- Use clear, concise language
- Include examples and diagrams where appropriate

### README Updates

If your changes affect the project setup, usage, or features, update the README.md file accordingly.

## Issue Reporting

If you find a bug or have a feature request, please create an issue using the appropriate template:

- Bug Report: Use the bug report template to provide detailed information about the issue
- Feature Request: Use the feature request template to describe the new functionality

Before creating a new issue, please search existing issues to avoid duplicates.

## Security Vulnerabilities

If you discover a security vulnerability, please do NOT open an issue. Instead, follow the instructions in our [Security Policy](SECURITY.md) to report it responsibly.

## Licensing

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License. All new files should include the appropriate license header.

## Community

We value our community and appreciate all contributions. Here are some ways to get involved beyond code contributions:

- Help review pull requests
- Improve documentation
- Answer questions in issues
- Share your experience using the project

Thank you for contributing to the Document Management and AI Chatbot System!