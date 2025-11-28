import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock


# Basic validation test
@pytest.mark.asyncio
async def test_register_user_validation_error(async_client: AsyncClient):
    # Missing required fields
    payload = {"username": "testuser"}
    response = await async_client.post("/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    # The health check depends on DB and MinIO.
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "storage" in data


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient, mock_auth_repo):
    # Setup mock
    mock_auth_repo.get_user_by_email.return_value = None  # User doesn't exist
    mock_auth_repo.create_user.return_value = None  # Success

    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "securepassword123",
    }

    response = await async_client.post("/auth/register", json=payload)

    assert response.status_code == 200
    # SuccessResponse likely has success=True
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert data["success"] is True

    # Verify mock calls
    mock_auth_repo.get_user_by_email.assert_called_once_with("newuser@example.com")
    mock_auth_repo.create_user.assert_called_once()


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, mock_auth_repo):
    # Setup mock user
    # We need a real hash for the password verification to pass
    from api.core.security import get_password_hash

    hashed = get_password_hash("securepassword123")

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    mock_user.hashed_password = hashed
    mock_user.is_active = True

    mock_auth_repo.get_user_by_email.return_value = mock_user
    mock_auth_repo.update_user_jti.return_value = None

    form_data = {"username": "test@example.com", "password": "securepassword123"}

    response = await async_client.post("/auth/login", data=form_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify cookies
    assert "refresh_token" in response.cookies
