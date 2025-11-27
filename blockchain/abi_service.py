import aiohttp
import json
from core.redis.providers import CacheService


class ABIService:
    """
    Service for fetching contract ABI from blockchain explorers.
    
    Parameters
    ----------
    cache_service : CacheService
        Cache service for storing ABIs
    """
    
    EXPLORER_APIS = {
        "avalanche": "https://api.snowtrace.io/api",
        "ethereum": "https://api.etherscan.io/api"
    }
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    async def get_abi(
        self,
        contract_address: str,
        network: str,
        api_key: str
    ) -> list[dict[str, any]]:
        """
        Get contract ABI from explorer API or cache.
        
        Parameters
        ----------
        contract_address : str
            Contract address
        network : str
            Network name
        api_key : str
            Explorer API key
            
        Returns
        -------
        list[dict[str, any]]
            Contract ABI
        """
        cache_key = f"abi:{network}:{contract_address.lower()}"
        
        cached = await self.cache.get(cache_key)
        if cached and isinstance(cached, list):
            return cached
        
        abi = await self._fetch_from_explorer(contract_address, network, api_key)
        
        if abi:
            await self.cache.set(cache_key, abi, ttl=86400 * 7)
        
        return abi
    
    async def _fetch_from_explorer(
        self,
        contract_address: str,
        network: str,
        api_key: str
    ) -> list[dict[str, any]]:
        """
        Fetch ABI from blockchain explorer API.
        
        Parameters
        ----------
        contract_address : str
            Contract address
        network : str
            Network name
        api_key : str
            Explorer API key
            
        Returns
        -------
        list[dict[str, any]]
            Contract ABI
        """
        api_url = self.EXPLORER_APIS.get(network)
        if not api_url:
            return []
        
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result"):
                            return json.loads(data["result"])
        except Exception:
            pass
        
        return []

