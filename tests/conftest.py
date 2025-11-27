import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock

from api.main import app
from api.core.dependencies import get_db_pool, get_minio_client


# Mock MinIO
@pytest.fixture
def mock_minio_client():
    mock = MagicMock()
    return mock


@pytest.fixture(autouse=True)
def override_minio(mock_minio_client):
    app.dependency_overrides[get_minio_client] = lambda: mock_minio_client
    yield
    app.dependency_overrides.pop(get_minio_client, None)


# Mock AsyncPG Pool
@pytest.fixture
def mock_db_pool():
    pool = MagicMock()  # acquire is not async, it returns a context manager

    # The context manager returned by acquire()
    connection = AsyncMock()
    context_manager = MagicMock()
    context_manager.__aenter__.return_value = connection
    context_manager.__aexit__.return_value = None

    pool.acquire.return_value = context_manager
    return pool


@pytest.fixture(autouse=True)
def override_db_pool(mock_db_pool):
    app.dependency_overrides[get_db_pool] = lambda: mock_db_pool
    yield
    app.dependency_overrides.pop(get_db_pool, None)


# Mock AuthRepository
from api.repositories.auth import AuthRepository
from api.core.dependencies import get_auth_repository


@pytest.fixture
def mock_auth_repo():
    repo = AsyncMock(spec=AuthRepository)
    return repo


@pytest.fixture(autouse=True)
def override_auth_repo(mock_auth_repo):
    app.dependency_overrides[get_auth_repository] = lambda: mock_auth_repo
    yield
    app.dependency_overrides.pop(get_auth_repository, None)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
