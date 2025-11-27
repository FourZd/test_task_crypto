from blockchain.services import Web3Service
from blockchain.abi_service import ABIService
from blockchain.schemas import BalanceResponse, EventsResponse, EventResponse
from core.redis.providers import CacheService
from core.environment.config import Settings


class GetWalletBalanceUseCase:
    """
    Use case for getting wallet balance at specific block.
    
    Parameters
    ----------
    web3_service : Web3Service
        Web3 service instance
    cache_service : Optional[CacheService]
        Cache service instance
    """
    
    def __init__(self, web3_service: Web3Service, cache_service: CacheService):
        self.web3_service = web3_service
        self.cache = cache_service
    
    async def __call__(
        self,
        wallet_address: str,
        block_number: int,
        network: str
    ) -> BalanceResponse:
        """
        Execute use case.
        
        Parameters
        ----------
        wallet_address : str
            Wallet address
        block_number : int
            Block number
        network : str
            Network name
            
        Returns
        -------
        BalanceResponse
            Balance response
        """
        cache_key = f"balance:{network}:{wallet_address}:{block_number}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            return BalanceResponse(**cached)
        
        balance_entity = await self.web3_service.get_balance_at_block(
            wallet_address=wallet_address,
            block_number=block_number,
            network=network
        )
        
        response = BalanceResponse(
            wallet_address=balance_entity.wallet_address,
            block_number=balance_entity.block_number,
            balance_wei=balance_entity.balance_wei,
            balance_eth=balance_entity.balance_eth,
            network=balance_entity.network
        )
        
        await self.cache.set(cache_key, response.model_dump(), ttl=86400)
        
        return response


class GetContractEventsUseCase:
    """
    Use case for getting contract events.
    
    Parameters
    ----------
    web3_service : Web3Service
        Web3 service instance
    cache_service : CacheService
        Cache service instance
    abi_service : ABIService
        ABI service for fetching from API
    settings : Settings
        Application settings
    """
    
    def __init__(
        self,
        web3_service: Web3Service,
        cache_service: CacheService,
        abi_service: ABIService,
        settings: Settings
    ):
        self.web3_service = web3_service
        self.cache = cache_service
        self.abi_service = abi_service
        self.settings = settings
    
    async def __call__(
        self,
        contract_address: str,
        from_block: int,
        network: str
    ) -> EventsResponse:
        """
        Execute use case.
        
        Parameters
        ----------
        contract_address : str
            Contract address
        from_block : int
            Starting block number
        network : str
            Network name
            
        Returns
        -------
        EventsResponse
            Events response
        """
        web3_client = self.web3_service._get_client(network)
        current_block = await web3_client.eth.block_number
        
        cache_key = f"events:{network}:{contract_address}:{from_block}:{current_block}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            return EventsResponse(**cached)
        
        api_key = self.settings.snowtrace_api_key if network == "avalanche" else self.settings.etherscan_api_key
        abi = await self.abi_service.get_abi(contract_address, network, api_key, web3_client)
        
        events = await self.web3_service.get_contract_events(
            contract_address=contract_address,
            from_block=from_block,
            network=network,
            contract_abi=abi
        )
        
        event_responses = [
            EventResponse(
                transaction_hash=event.transaction_hash,
                block_number=event.block_number,
                log_index=event.log_index,
                event_name=event.event_name,
                args=event.args,
                address=event.address
            )
            for event in events
        ]
        
        response = EventsResponse(
            contract_address=contract_address,
            from_block=from_block,
            to_block=current_block,
            events=event_responses,
            network=network,
            total_events=len(event_responses)
        )
        
        await self.cache.set(cache_key, response.model_dump(), ttl=300)
        
        return response

