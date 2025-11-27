import asyncio
import logging
from web3 import AsyncWeb3
from blockchain.entities import WalletBalanceEntity, ContractEventEntity


class Web3Service:
    """
    Service for interacting with blockchain networks.
    
    Parameters
    ----------
    web3_clients : dict[str, AsyncWeb3]
        Dictionary of Web3 clients for different networks
    logger : logging.Logger
        Logger instance
    """
    
    def __init__(
        self, web3_clients: dict[str, AsyncWeb3], 
        logger: logging.Logger
    ):
        self.web3_clients = web3_clients
        self.logger = logger
    
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
        event_abis = [abi for abi in contract_abi if abi.get('type') == 'event']
        
        self.logger.info(f"Contract: {contract_address}, Network: {network}")
        self.logger.info(f"Total ABI items: {len(contract_abi)}")
        self.logger.info(f"Event ABIs found: {len(event_abis)}")
        if event_abis:
            event_names = [e['name'] for e in event_abis]
            self.logger.info(f"Event names: {event_names}")
            for event_abi in event_abis:
                event = getattr(contract.events, event_abi['name'], None)
                if event and hasattr(event, 'event_signature_hash'):
                    self.logger.info(f"Event '{event_abi['name']}' signature hash: {event.event_signature_hash}")
        
        chunk_size = 2048
        total_chunks = (current_block - from_block) // chunk_size + 1
        total_blocks = current_block - from_block + 1
        self.logger.info(f"Fetching logs from block {from_block} to {current_block} (total blocks: {total_blocks}, chunks: {total_chunks})")
        
        # Ограничиваем количество параллельных запросов чтобы не перегрузить RPC
        semaphore = asyncio.Semaphore(50)
        
        batch_size = 100
        all_chunks_results = []
        
        chunk_ranges = []
        for start in range(from_block, current_block + 1, chunk_size):
            end = min(start + chunk_size - 1, current_block)
            chunk_ranges.append((start, end))
        
        for batch_idx in range(0, len(chunk_ranges), batch_size):
            batch_ranges = chunk_ranges[batch_idx:batch_idx + batch_size]
            current_batch_num = batch_idx // batch_size + 1
            total_batches = (len(chunk_ranges) + batch_size - 1) // batch_size
            
            self.logger.info(
                f"Processing batch {current_batch_num}/{total_batches}: "
                f"chunks {batch_idx + 1}-{min(batch_idx + batch_size, len(chunk_ranges))} of {len(chunk_ranges)}"
            )
            
            tasks = []
            for start, end in batch_ranges:
                tasks.append(self._fetch_logs_chunk_with_semaphore(
                    semaphore, web3, checksum_address, start, end)
                )
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_chunks_results.extend(batch_results)
            
            chunks_processed = len(all_chunks_results)
            blocks_processed = min(chunks_processed * chunk_size, total_blocks)
            progress_pct = (chunks_processed / len(chunk_ranges)) * 100
            
            self.logger.info(
                f"Batch {current_batch_num}/{total_batches} completed: "
                f"{chunks_processed}/{len(chunk_ranges)} chunks processed ({progress_pct:.1f}%), "
                f"~{blocks_processed}/{total_blocks} blocks scanned"
            )
        
        chunks_results = all_chunks_results
        
        total_logs = 0
        error_count = 0
        events = []
        for logs_chunk in chunks_results:
            if isinstance(logs_chunk, Exception):
                error_count += 1
                self.logger.warning(f"Chunk failed with error: {logs_chunk}")
                continue
            
            total_logs += len(logs_chunk)
            
            for log in logs_chunk:
                event_name = 'UnknownEvent'
                decoded_args = {}
                
                if log.get('topics'):
                    event_signature_hash = log['topics'][0].hex()
                    
                    matched = False
                    for event_abi in event_abis:
                        event = getattr(contract.events, event_abi['name'], None)
                        if event and hasattr(event, 'event_signature_hash'):
                            if event.event_signature_hash == event_signature_hash:
                                matched = True
                                try:
                                    decoded = event.process_log(log)
                                    event_name = decoded['event']
                                    decoded_args = {k: self._serialize_value(v) for k, v in decoded['args'].items()}
                                except Exception as e:
                                    self.logger.warning(f"Failed to decode event {event_abi['name']}: {e}")
                                    decoded_args = {
                                        'topics': [t.hex() for t in log['topics']],
                                        'data': log['data'].hex() if log['data'] else '0x'
                                    }
                                break
                    
                    if not matched:
                        self.logger.debug(f"Unknown event signature: {event_signature_hash}")
                
                if event_name == 'UnknownEvent':
                    decoded_args = {
                        'topics': [t.hex() for t in log['topics']],
                        'data': log['data'].hex() if log['data'] else '0x'
                    }
                
                events.append(
                    ContractEventEntity(
                        transaction_hash=log['transactionHash'].hex(),
                        block_number=log['blockNumber'],
                        log_index=log['logIndex'],
                        event_name=event_name,
                        args=decoded_args,
                        address=log['address'],
                        network=network
                    )
                )
        
        events.sort(key=lambda x: (x.block_number, x.log_index))
        
        self.logger.info(f"Fetched {total_logs} logs total, {error_count} chunks failed")
        self.logger.info(f"Decoded {len(events)} events successfully")
        
        return events
    
    async def _fetch_logs_chunk_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        web3: AsyncWeb3,
        contract_address: str,
        from_block: int,
        to_block: int
    ) -> list:
        """
        Fetch logs for a specific block range with semaphore control.
        
        Parameters
        ----------
        semaphore : asyncio.Semaphore
            Semaphore to limit concurrent requests
        web3 : AsyncWeb3
            Web3 client instance
        contract_address : str
            Contract address (checksum)
        from_block : int
            Starting block number
        to_block : int
            Ending block number
            
        Returns
        -------
        list
            List of log entries
        """
        async with semaphore:
            return await web3.eth.get_logs({
                'address': contract_address,
                'fromBlock': from_block,
                'toBlock': to_block
            })
    
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

