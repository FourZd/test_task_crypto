from dishka import Provider, Scope, provide, FromComponent
from blockchain.services import Web3Service
from blockchain.abi_service import ABIService
from blockchain.usecases import GetWalletBalanceUseCase, GetContractEventsUseCase
from typing import Annotated
from web3 import AsyncWeb3
from core.environment.config import Settings
from core.redis.providers import CacheService
import logging


class BlockchainProvider(Provider):
    """
    Provider for blockchain-related dependencies.
    """
    
    component = "blockchain"
    
    @provide(scope=Scope.APP)
    def get_web3_clients(
        self,
        settings: Annotated[Settings, FromComponent("environment")]
    ) -> dict[str, AsyncWeb3]:
        """
        Provide Web3 clients for different networks.
        
        Parameters
        ----------
        settings : Settings
            Application settings
            
        Returns
        -------
        dict[str, AsyncWeb3]
            Dictionary of Web3 clients
        """
        networks = ["avalanche", "ethereum"]
        return {
            network: AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.get_rpc_url(network)))
            for network in networks
        }
    
    @provide(scope=Scope.APP)
    def get_web3_service(
        self,
        web3_clients: Annotated[
            dict[str, AsyncWeb3], FromComponent("blockchain")
        ],
        logger: Annotated[logging.Logger, FromComponent("logger")],
        cache_service: Annotated[CacheService, FromComponent("cache")]
    ) -> Web3Service:
        """
        Provide Web3 service.
        
        Parameters
        ----------
        web3_clients : dict[str, AsyncWeb3]
            Dictionary of Web3 clients
        logger : logging.Logger
            Logger instance
        cache_service : CacheService
            Cache service instance for chunk caching
            
        Returns
        -------
        Web3Service
            Web3 service instance
        """
        return Web3Service(
            web3_clients=web3_clients, 
            logger=logger, 
            cache_service=cache_service
        )
    
    @provide(scope=Scope.APP)
    def get_abi_service(
        self,
        cache_service: Annotated[
            CacheService, FromComponent("cache")
        ],
        logger: Annotated[logging.Logger, FromComponent("logger")]
    ) -> ABIService:
        """
        Provide ABI service.
        
        Parameters
        ----------
        cache_service : CacheService
            Cache service instance
        logger : logging.Logger
            Logger instance
            
        Returns
        -------
        ABIService
            ABI service instance
        """
        return ABIService(cache_service=cache_service, logger=logger)
    
    @provide(scope=Scope.REQUEST)
    def get_wallet_balance_use_case(
        self,
        web3_service: Annotated[Web3Service, FromComponent("blockchain")],
        cache_service: Annotated[CacheService, FromComponent("cache")]
    ) -> GetWalletBalanceUseCase:
        """
        Provide get wallet balance use case.
        
        Parameters
        ----------
        web3_service : Web3Service
            Web3 service instance
        cache_service : CacheService
            Cache service instance
            
        Returns
        -------
        GetWalletBalanceUseCase
            Get wallet balance use case
        """
        return GetWalletBalanceUseCase(
            web3_service=web3_service,
            cache_service=cache_service
        )
    
    @provide(scope=Scope.REQUEST)
    def get_contract_events_use_case(
        self,
        web3_service: Annotated[Web3Service, FromComponent("blockchain")],
        cache_service: Annotated[CacheService, FromComponent("cache")],
        abi_service: Annotated[ABIService, FromComponent("blockchain")],
        settings: Annotated[Settings, FromComponent("environment")]
    ) -> GetContractEventsUseCase:
        """
        Provide get contract events use case.
        
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
            
        Returns
        -------
        GetContractEventsUseCase
            Get contract events use case
        """
        return GetContractEventsUseCase(
            web3_service=web3_service,
            cache_service=cache_service,
            abi_service=abi_service,
            settings=settings
        )

