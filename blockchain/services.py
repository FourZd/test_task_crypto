from web3 import AsyncWeb3
from blockchain.entities import WalletBalanceEntity, ContractEventEntity


class Web3Service:
    """
    Service for interacting with blockchain networks.
    
    Parameters
    ----------
    web3_clients : dict[str, AsyncWeb3]
        Dictionary of Web3 clients for different networks
    """
    
    def __init__(self, web3_clients: dict[str, AsyncWeb3]):
        self.web3_clients = web3_clients
    
    def _get_client(self, network: str) -> AsyncWeb3:
        """
        Get Web3 client for specified network.
        
        Parameters
        ----------
        network : str
            Network name
            
        Returns
        -------
        AsyncWeb3
            Web3 client instance
            
        Raises
        ------
        ValueError
            If network is not supported
        """
        if network not in self.web3_clients:
            raise ValueError(f"Network {network} is not supported")
        return self.web3_clients[network]
    
    async def get_balance_at_block(
        self,
        wallet_address: str,
        block_number: int,
        network: str
    ) -> WalletBalanceEntity:
        """
        Get wallet balance at specific block.
        
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
        WalletBalanceEntity
            Wallet balance entity
        """
        web3 = self._get_client(network)
        
        checksum_address = web3.to_checksum_address(wallet_address)
        balance_wei = await web3.eth.get_balance(checksum_address, block_number)
        balance_eth = web3.from_wei(balance_wei, 'ether')
        
        return WalletBalanceEntity(
            wallet_address=wallet_address,
            block_number=block_number,
            balance_wei=int(balance_wei),
            balance_eth=float(balance_eth),
            network=network
        )
    
    async def get_contract_events(
        self,
        contract_address: str,
        from_block: int,
        network: str,
        contract_abi: list[dict[str, any]]
    ) -> list[ContractEventEntity]:
        """
        Get all events from contract starting from specified block.
        
        Parameters
        ----------
        contract_address : str
            Contract address
        from_block : int
            Starting block number
        network : str
            Network name
        contract_abi : list[dict[str, any]]
            Contract ABI
            
        Returns
        -------
        list[ContractEventEntity]
            List of contract events
        """
        web3 = self._get_client(network)
        
        checksum_address = web3.to_checksum_address(contract_address)
        current_block = await web3.eth.block_number
        
        contract = web3.eth.contract(address=checksum_address, abi=contract_abi)
        
        events = []
        
        for event_abi in contract_abi:
            if event_abi.get('type') != 'event':
                continue
            
            event_name = event_abi['name']
            event = getattr(contract.events, event_name, None)
            
            if event is None:
                continue
            
            try:
                event_filter = event.create_filter(
                    fromBlock=from_block,
                    toBlock=current_block
                )
                
                event_logs = await event_filter.get_all_entries()
                
                for log in event_logs:
                    events.append(
                        ContractEventEntity(
                            transaction_hash=log['transactionHash'].hex(),
                            block_number=log['blockNumber'],
                            log_index=log['logIndex'],
                            event_name=event_name,
                            args={k: self._serialize_value(v) for k, v in log['args'].items()},
                            address=log['address'],
                            network=network
                        )
                    )
            except Exception as e:
                continue
        
        events.sort(key=lambda x: (x.block_number, x.log_index))
        
        return events
    
    def _serialize_value(self, value: any) -> any:
        """
        Serialize value for JSON response.
        
        Parameters
        ----------
        value : any
            Value to serialize
            
        Returns
        -------
        any
            Serialized value
        """
        if isinstance(value, bytes):
            return value.hex()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return str(value) if not isinstance(value, (int, float, str, bool, type(None))) else value

