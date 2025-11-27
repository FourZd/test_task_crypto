from pydantic import BaseModel, ConfigDict


class WalletBalanceEntity(BaseModel):
    """
    Entity representing wallet balance at a specific block.
    
    Attributes
    ----------
    wallet_address : str
        The wallet address
    block_number : int
        The block number at which balance was checked
    balance_wei : int
        The balance in Wei (smallest unit)
    balance_eth : float
        The balance in ETH/AVAX
    network : str
        The network name (avalanche, ethereum)
    """
    wallet_address: str
    block_number: int
    balance_wei: int
    balance_eth: float
    network: str

    model_config = ConfigDict(from_attributes=True)


class ContractEventEntity(BaseModel):
    """
    Entity representing a contract event.
    
    Attributes
    ----------
    transaction_hash : str
        Transaction hash
    block_number : int
        Block number where event occurred
    log_index : int
        Log index in the transaction
    event_name : str
        Name of the event
    args : dict
        Event arguments
    address : str
        Contract address
    network : str
        Network name
    """
    transaction_hash: str
    block_number: int
    log_index: int
    event_name: str
    args: dict
    address: str
    network: str

    model_config = ConfigDict(from_attributes=True)

