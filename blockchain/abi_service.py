import aiohttp
import json
import logging
from core.redis.providers import CacheService
from web3 import AsyncWeb3


class ABIService:
    """
    Service for fetching contract ABI from blockchain explorers.
    
    Parameters
    ----------
    cache_service : CacheService
        Cache service for storing ABIs
    logger : logging.Logger
        Logger instance
    """
    
    EXPLORER_APIS = {
        "avalanche": "https://api.snowtrace.io/api",
        "ethereum": "https://api.etherscan.io/api"
    }
    
    def __init__(self, cache_service: CacheService, logger: logging.Logger):
        self.cache = cache_service
        self.logger = logger
    
    async def get_abi(
        self,
        contract_address: str,
        network: str,
        api_key: str,
        web3_client: AsyncWeb3
    ) -> list[dict[str, any]]:
        """
        Get contract ABI from explorer API or cache.
        For proxy contracts, attempts to get implementation ABI.
        
        Parameters
        ----------
        contract_address : str
            Contract address
        network : str
            Network name
        api_key : str
            Explorer API key
        web3_client : AsyncWeb3
            Web3 client for reading implementation address
            
        Returns
        -------
        list[dict[str, any]]
            Contract ABI (implementation ABI if proxy)
        """
        cache_key = f"abi:{network}:{contract_address.lower()}"
        
        self.logger.info(f"get_abi called for {contract_address} on {network}")
        
        cached = await self.cache.get(cache_key)
        if cached and isinstance(cached, list):
            self.logger.info(f"ABI found in cache for {contract_address}")
            return cached
        
        abi = await self._fetch_from_explorer(contract_address, network, api_key)
        
        # Проверяем прокси и пытаемся получить ABI имплементации
        if abi and web3_client and self._is_proxy_abi(abi):
            self.logger.info(f"Contract {contract_address} detected as proxy")
            impl_address = await self._get_implementation_address(
                contract_address, abi, web3_client
            )
            
            if impl_address:
                self.logger.info(f"Implementation address found: {impl_address}")
                impl_abi = await self._fetch_from_explorer(impl_address, network, api_key)
                if impl_abi:
                    self.logger.info(f"Implementation ABI loaded: {len(impl_abi)} items")
                    await self.cache.set(cache_key, impl_abi, ttl=86400 * 7)
                    return impl_abi
                else:
                    self.logger.warning(f"Failed to fetch implementation ABI for {impl_address}")
            else:
                self.logger.warning(f"Failed to get implementation address for proxy {contract_address}")
        
        if abi:
            await self.cache.set(cache_key, abi, ttl=86400 * 7)
        
        return abi
    
    def _is_proxy_abi(self, abi: list[dict[str, any]]) -> bool:
        """
        Check if ABI looks like a proxy contract.
        
        Parameters
        ----------
        abi : list[dict[str, any]]
            Contract ABI
            
        Returns
        -------
        bool
            True if ABI contains proxy patterns
        """
        proxy_functions = ['implementation', 'upgradeTo', 'upgradeToAndCall']
        function_names = {item['name'] for item in abi if item.get('type') == 'function' and 'name' in item}
        
        self.logger.info(f"Checking if proxy: functions in ABI = {function_names}")
        
        # Если есть хотя бы 2 из этих функций - скорее всего прокси
        matches = sum(1 for pf in proxy_functions if pf in function_names)
        self.logger.info(f"Proxy function matches: {matches}/3 - is_proxy={matches >= 2}")
        return matches >= 2
    
    async def _get_implementation_address(
        self,
        proxy_address: str,
        proxy_abi: list[dict[str, any]],
        web3_client
    ) -> str | None:
        """
        Get implementation address from proxy contract.
        Tries multiple methods: EIP-1967 storage slot, then implementation() function.
        
        Parameters
        ----------
        proxy_address : str
            Proxy contract address
        proxy_abi : list[dict[str, any]]
            Proxy contract ABI
        web3_client : AsyncWeb3
            Web3 client
            
        Returns
        -------
        str | None
            Implementation address or None
        """
        checksum_address = web3_client.to_checksum_address(proxy_address)
        
        # Метод 1: EIP-1967 storage slot для implementation
        # keccak256("eip1967.proxy.implementation") - 1
        IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        
        try:
            self.logger.info(f"Reading implementation from EIP-1967 storage slot")
            storage_value = await web3_client.eth.get_storage_at(checksum_address, IMPLEMENTATION_SLOT)
            impl_address = web3_client.to_checksum_address("0x" + storage_value.hex()[-40:])
            
            # Проверяем что это не нулевой адрес
            if impl_address != "0x0000000000000000000000000000000000000000":
                self.logger.info(f"Implementation address from storage: {impl_address}")
                return impl_address
        except Exception as e:
            self.logger.warning(f"Failed to read from EIP-1967 slot: {e}")
        
        # Метод 2: Вызов функции implementation()
        try:
            contract = web3_client.eth.contract(address=checksum_address, abi=proxy_abi)
            
            if hasattr(contract.functions, 'implementation'):
                self.logger.info(f"Calling implementation() on {proxy_address}")
                impl_address = await contract.functions.implementation().call()
                self.logger.info(f"implementation() returned: {impl_address}")
                return impl_address
        except Exception as e:
            self.logger.warning(f"Error calling implementation(): {e}")
        
        return None
    
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

