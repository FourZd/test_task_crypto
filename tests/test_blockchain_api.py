import pytest
from httpx import AsyncClient


class TestBlockchainAPI:
    """
    Unit tests for blockchain API endpoints.
    
    These tests verify:
    1. API endpoints are accessible and return correct structure
    2. Input validation works correctly (Pydantic models)
    3. Error handling for invalid inputs
    
    Note: These are UNIT tests, not integration tests.
    They test API structure and validation, not actual blockchain interactions.
    """
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """
        Test root endpoint returns correct application information.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Blockchain API Service"
        assert data["version"] == "1.3.3.7"
        assert "endpoints" in data
        assert data["endpoints"]["balance"] == "/api/blockchain/balance"
        assert data["endpoints"]["events"] == "/api/blockchain/events"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """
        Test health check endpoint.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy but depressed"
        assert data["version"] == "1.3.3.7"
    
    @pytest.mark.asyncio
    async def test_get_balance_invalid_address_format(self, client: AsyncClient):
        """
        Test that API rejects invalid Ethereum address format.
        Verifies Pydantic validation works correctly.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "wallet_address": "invalid_address",
            "block_number": 1000000,
            "network": "avalanche"
        }
        
        response = await client.post("/api/blockchain/balance", json=payload)
        assert response.status_code == 422
        data = response.json()
        # Check that error response contains validation information
        assert "errors" in data or "detail" in data
    
    @pytest.mark.asyncio
    async def test_get_balance_invalid_address_length(self, client: AsyncClient):
        """
        Test that API rejects Ethereum address with invalid length.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "wallet_address": "0x123",  # Too short
            "block_number": 1000000,
            "network": "avalanche"
        }
        
        response = await client.post("/api/blockchain/balance", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_balance_invalid_block_number(self, client: AsyncClient):
        """
        Test that API rejects negative block numbers.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "wallet_address": "0x0000000000000000000000000000000000000000",
            "block_number": -1,
            "network": "avalanche"
        }
        
        response = await client.post("/api/blockchain/balance", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_balance_zero_block_number(self, client: AsyncClient):
        """
        Test that API rejects zero block number (must be > 0).
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "wallet_address": "0x0000000000000000000000000000000000000000",
            "block_number": 0,
            "network": "avalanche"
        }
        
        response = await client.post("/api/blockchain/balance", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_balance_invalid_network(self, client: AsyncClient):
        """
        Test that API rejects unsupported network names.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "wallet_address": "0x0000000000000000000000000000000000000000",
            "block_number": 1000000,
            "network": "bitcoin"  # Not supported
        }
        
        response = await client.post("/api/blockchain/balance", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_events_invalid_contract_address(self, client: AsyncClient):
        """
        Test that API rejects invalid contract address format.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "from_block": 1000000,
            "contract_address": "invalid_address",
            "network": "avalanche"
        }
        
        response = await client.post("/api/blockchain/events", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_events_invalid_block_number(self, client: AsyncClient):
        """
        Test that API rejects negative block numbers for events endpoint.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "from_block": -1,
            "contract_address": "0x66357dCaCe80431aee0A7507e2E361B7e2402370",
            "network": "avalanche"
        }
        
        response = await client.post("/api/blockchain/events", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_events_missing_required_field(self, client: AsyncClient):
        """
        Test that API rejects requests with missing required fields.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "contract_address": "0x66357dCaCe80431aee0A7507e2E361B7e2402370",
            # missing from_block
        }
        
        response = await client.post("/api/blockchain/events", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_balance_missing_required_field(self, client: AsyncClient):
        """
        Test that API rejects balance requests with missing required fields.
        
        Parameters
        ----------
        client : AsyncClient
            Test client fixture
        """
        payload = {
            "wallet_address": "0x0000000000000000000000000000000000000000",
            # missing block_number
        }
        
        response = await client.post("/api/blockchain/balance", json=payload)
        assert response.status_code == 422
