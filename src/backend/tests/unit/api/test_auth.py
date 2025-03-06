# Standard library imports
import unittest.mock  # unittest 3.8+
from datetime import timedelta  # datetime
import uuid  # uuid

# Third-party library imports
import pytest  # pytest 7.0.0+

# Local application imports
from src.backend.app.core.security import create_access_token, create_refresh_token, get_password_hash  # Import token creation function for testing
from src.backend.app.schemas.token import TokenRequest, RefreshTokenRequest  # Import token request schema for login tests
from src.backend.app.schemas.user import UserCreate  # Import user creation schema for registration tests
from src.backend.app.services.auth_service import store_refresh_token  # Import token storage function for token refresh tests


def test_login_success(client, test_user):
    """
    Tests successful login with valid credentials

    Args:
        client (TestClient): FastAPI test client
        test_user (User): Test user fixture

    Returns:
        None: No return value
    """
    # Create login data with test user's username and password
    login_data = {"username": test_user.username, "password": "testpassword"}
    # Send POST request to /auth/token endpoint with login data
    response = client.post("/auth/token", data=login_data)
    # Assert response status code is 200 (OK)
    assert response.status_code == 200
    # Assert response contains access_token, token_type, and refresh_token
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "refresh_token" in response.json()
    # Assert token_type is 'bearer'
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """
    Tests login failure with invalid credentials

    Args:
        client (TestClient): FastAPI test client

    Returns:
        None: No return value
    """
    # Create login data with invalid username and password
    login_data = {"username": "invaliduser", "password": "invalidpassword"}
    # Send POST request to /auth/token endpoint with invalid credentials
    response = client.post("/auth/token", data=login_data)
    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401
    # Assert response contains error detail about incorrect credentials
    assert "Incorrect username or password" in response.json()["detail"]


def test_refresh_token_success(client, test_user, test_db):
    """
    Tests successful token refresh with valid refresh token

    Args:
        client (TestClient): FastAPI test client
        test_user (User): Test user fixture
        test_db (Session): Database session fixture

    Returns:
        None: No return value
    """
    # Create token data with test user's ID and role
    token_data = {"sub": str(test_user.id), "role": test_user.role.name}
    # Generate refresh token for the test user
    refresh_token = create_refresh_token(data=token_data)
    # Store refresh token in the database
    store_refresh_token(test_db, refresh_token, str(test_user.id))
    # Create refresh token request with the generated token
    refresh_request = {"refresh_token": refresh_token}
    # Send POST request to /auth/refresh endpoint with refresh token
    response = client.post("/auth/refresh", json=refresh_request)
    # Assert response status code is 200 (OK)
    assert response.status_code == 200
    # Assert response contains new access_token, token_type, and refresh_token
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "refresh_token" in response.json()
    # Assert token_type is 'bearer'
    assert response.json()["token_type"] == "bearer"


def test_refresh_token_invalid(client):
    """
    Tests token refresh failure with invalid refresh token

    Args:
        client (TestClient): FastAPI test client

    Returns:
        None: No return value
    """
    # Create refresh token request with invalid token
    refresh_request = {"refresh_token": "invalidtoken"}
    # Send POST request to /auth/refresh endpoint with invalid token
    response = client.post("/auth/refresh", json=refresh_request)
    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401
    # Assert response contains error detail about invalid token
    assert "Invalid authentication token" in response.json()["detail"]


def test_refresh_token_expired(client, test_user, test_db):
    """
    Tests token refresh failure with expired refresh token

    Args:
        client (TestClient): FastAPI test client
        test_user (User): Test user fixture
        test_db (Session): Database session fixture

    Returns:
        None: No return value
    """
    # Create token data with test user's ID and role
    token_data = {"sub": str(test_user.id), "role": test_user.role.name}
    # Generate expired refresh token by setting expiration in the past
    expired_refresh_token = create_access_token(
        data=token_data, expires_delta=timedelta(minutes=-1)
    )
    # Store expired refresh token in the database
    store_refresh_token(test_db, expired_refresh_token, str(test_user.id))
    # Create refresh token request with the expired token
    refresh_request = {"refresh_token": expired_refresh_token}
    # Send POST request to /auth/refresh endpoint with expired token
    response = client.post("/auth/refresh", json=refresh_request)
    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401
    # Assert response contains error detail about expired token
    assert "Invalid authentication token" in response.json()["detail"]


def test_logout_success(client, test_user, test_db):
    """
    Tests successful logout with valid refresh token

    Args:
        client (TestClient): FastAPI test client
        test_user (User): Test user fixture
        test_db (Session): Database session fixture

    Returns:
        None: No return value
    """
    # Create token data with test user's ID and role
    token_data = {"sub": str(test_user.id), "role": test_user.role.name}
    # Generate refresh token for the test user
    refresh_token = create_refresh_token(data=token_data)
    # Store refresh token in the database
    store_refresh_token(test_db, refresh_token, str(test_user.id))
    # Create logout request with the generated token
    logout_request = {"refresh_token": refresh_token}
    # Send POST request to /auth/logout endpoint with refresh token
    response = client.post("/auth/logout", json=logout_request)
    # Assert response status code is 200 (OK)
    assert response.status_code == 200
    # Assert response contains success message
    assert "Successfully logged out" in response.json()["message"]
    # Verify token is marked as revoked in the database
    # TODO: Implement token revocation check in database


def test_logout_invalid_token(client):
    """
    Tests logout with invalid refresh token

    Args:
        client (TestClient): FastAPI test client

    Returns:
        None: No return value
    """
    # Create logout request with invalid token
    logout_request = {"refresh_token": "invalidtoken"}
    # Send POST request to /auth/logout endpoint with invalid token
    response = client.post("/auth/logout", json=logout_request)
    # Assert response status code is 200 (OK) for idempotency
    assert response.status_code == 200
    # Assert response contains success message
    assert "Successfully logged out" in response.json()["message"]


def test_register_success(client):
    """
    Tests successful user registration with valid data

    Args:
        client (TestClient): FastAPI test client

    Returns:
        None: No return value
    """
    # Create unique username, email, and strong password for registration
    username = f"newuser_{uuid.uuid4()}"
    email = f"newuser_{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"
    # Create user registration data with UserCreate schema
    registration_data = {"username": username, "email": email, "password": password}
    # Send POST request to /auth/register endpoint with registration data
    response = client.post("/auth/register", json=registration_data)
    # Assert response status code is 201 (Created)
    assert response.status_code == 201
    # Assert response contains user data with matching username and email
    assert response.json()["username"] == username
    assert response.json()["email"] == email
    # Assert response does not contain password
    assert "password" not in response.json()


def test_register_existing_username(client, test_user):
    """
    Tests registration failure with existing username

    Args:
        client (TestClient): FastAPI test client
        test_user (User): Test user fixture

    Returns:
        None: No return value
    """
    # Create registration data with existing test user's username but new email
    registration_data = {"username": test_user.username, "email": "newemail@example.com", "password": "StrongPassword123!"}
    # Send POST request to /auth/register endpoint with registration data
    response = client.post("/auth/register", json=registration_data)
    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400
    # Assert response contains error detail about username already registered
    assert "Username already registered" in response.json()["detail"]


def test_register_existing_email(client, test_user):
    """
    Tests registration failure with existing email

    Args:
        client (TestClient): FastAPI test client
        test_user (User): Test user fixture

    Returns:
        None: No return value
    """
    # Create registration data with new username but existing test user's email
    registration_data = {"username": "newusername", "email": test_user.email, "password": "StrongPassword123!"}
    # Send POST request to /auth/register endpoint with registration data
    response = client.post("/auth/register", json=registration_data)
    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400
    # Assert response contains error detail about email already registered
    assert "Email already registered" in response.json()["detail"]


def test_register_weak_password(client):
    """
    Tests registration failure with weak password

    Args:
        client (TestClient): FastAPI test client

    Returns:
        None: No return value
    """
    # Create registration data with valid username and email but weak password
    registration_data = {"username": "newusername", "email": "newemail@example.com", "password": "weak"}
    # Send POST request to /auth/register endpoint with registration data
    response = client.post("/auth/register", json=registration_data)
    # Assert response status code is 422 (Unprocessable Entity)
    assert response.status_code == 422
    # Assert response contains validation error about password strength
    assert "Password must be at least 10 characters long" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_login_async(async_client, test_user):
    """
    Tests async login endpoint with valid credentials

    Args:
        async_client (AsyncClient): FastAPI async test client
        test_user (User): Test user fixture

    Returns:
        None: No return value
    """
    # Create login data with test user's username and password
    login_data = {"username": test_user.username, "password": "testpassword"}
    # Send POST request to /auth/token/async endpoint with login data
    response = await async_client.post("/auth/token/async", json=login_data)
    # Assert response status code is 200 (OK)
    assert response.status_code == 200
    # Assert response contains access_token, token_type, and refresh_token
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "refresh_token" in response.json()
    # Assert token_type is 'bearer'
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_async(async_client, test_user, async_db):
    """
    Tests async token refresh endpoint with valid refresh token

    Args:
        async_client (AsyncClient): FastAPI async test client
        test_user (User): Test user fixture
        async_db (AsyncSession): Async database session fixture

    Returns:
        None: No return value
    """
    # Create token data with test user's ID and role
    token_data = {"sub": str(test_user.id), "role": test_user.role.name}
    # Generate refresh token for the test user
    refresh_token = create_refresh_token(data=token_data)
    # Store refresh token in the database asynchronously
    await store_refresh_token_async(async_db, refresh_token, str(test_user.id))
    # Create refresh token request with the generated token
    refresh_request = {"refresh_token": refresh_token}
    # Send POST request to /auth/refresh/async endpoint with refresh token
    response = await async_client.post("/auth/refresh/async", json=refresh_request)
    # Assert response status code is 200 (OK)
    assert response.status_code == 200
    # Assert response contains new access_token, token_type, and refresh_token
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "refresh_token" in response.json()
    # Assert token_type is 'bearer'
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_logout_async(async_client, test_user, async_db):
    """
    Tests async logout endpoint with valid refresh token

    Args:
        async_client (AsyncClient): FastAPI async test client
        test_user (User): Test user fixture
        async_db (AsyncSession): Async database session fixture

    Returns:
        None: No return value
    """
    # Create token data with test user's ID and role
    token_data = {"sub": str(test_user.id), "role": test_user.role.name}
    # Generate refresh token for the test user
    refresh_token = create_refresh_token(data=token_data)
    # Store refresh token in the database asynchronously
    await store_refresh_token_async(async_db, refresh_token, str(test_user.id))
    # Create logout request with the generated token
    logout_request = {"refresh_token": refresh_token}
    # Send POST request to /auth/logout/async endpoint with refresh token
    response = await async_client.post("/auth/logout/async", json=logout_request)
    # Assert response status code is 200 (OK)
    assert response.status_code == 200
    # Assert response contains success message
    assert "Successfully logged out" in response.json()["message"]
    # Verify token is marked as revoked in the database
    # TODO: Implement token revocation check in database


@pytest.mark.asyncio
async def test_register_async(async_client):
    """
    Tests async registration endpoint with valid data

    Args:
        async_client (AsyncClient): FastAPI async test client

    Returns:
        None: No return value
    """
    # Create unique username, email, and strong password for registration
    username = f"newuser_{uuid.uuid4()}"
    email = f"newuser_{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"
    # Create user registration data with UserCreate schema
    registration_data = {"username": username, "email": email, "password": password}
    # Send POST request to /auth/register/async endpoint with registration data
    response = await async_client.post("/auth/register/async", json=registration_data)
    # Assert response status code is 201 (Created)
    assert response.status_code == 201
    # Assert response contains user data with matching username and email
    assert response.json()["username"] == username
    assert response.json()["email"] == email
    # Assert response does not contain password
    assert "password" not in response.json()