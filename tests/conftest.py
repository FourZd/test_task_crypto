import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
import os


# Set test environment variables before imports
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_DB'] = '0'
os.environ['REDIS_PASSWORD'] = ''  # No password for mock
os.environ['SNOWTRACE_API_KEY'] = 'test'
os.environ['ETHERSCAN_API_KEY'] = 'test'


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.aclose = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def client(mock_redis):
    """
    Fixture for async test client with mocked Redis.
    
    Parameters
    ----------
    mock_redis : AsyncMock
        Mocked Redis client
    
    Yields
    ------
    AsyncClient
        Async HTTP client for testing
    """
    # Patch Redis before importing main app
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        # Import after patching to ensure mock is used
        from main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
