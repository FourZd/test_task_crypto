from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class GetBalanceRequest(BaseModel):
    """
    Request schema for getting wallet balance.
    
    Attributes
    ----------
    wallet_address : str
        Wallet address to check balance for
    block_number : int
        Block number to check balance at
    network : Literal["avalanche", "ethereum"]
        Network to check balance on (optional, defaults to avalanche)
    """
    wallet_address: str = Field(..., description="Wallet address to check balance for")
    block_number: int = Field(..., gt=0, description="Block number to check balance at")
    network: Literal["avalanche", "ethereum"] = Field(
        default="avalanche",
        description="Network to check balance on"
    )

    @field_validator('wallet_address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum address format')
        return v.lower()

    model_config = ConfigDict(from_attributes=True)


class BalanceResponse(BaseModel):
    """
    Response schema for balance query.
    
    Attributes
    ----------
    wallet_address : str
        Wallet address
    block_number : int
        Block number
    balance_wei : int
        Balance in Wei
    balance_eth : float
        Balance in ETH/AVAX
    network : str
        Network name
    """
    wallet_address: str
    block_number: int
    balance_wei: int
    balance_eth: float
    network: str

    model_config = ConfigDict(from_attributes=True)


class GetEventsRequest(BaseModel):
    """
    Request schema for getting contract events.
    
    Attributes
    ----------
    from_block : int
        Starting block number
    contract_address : str
        Contract address to get events from
    network : Literal["avalanche", "ethereum"]
        Network to query events on (optional, defaults to avalanche)
    """
    from_block: int = Field(..., gt=0, description="Starting block number")
    contract_address: str = Field(
        default="0x66357dCaCe80431aee0A7507e2E361B7e2402370",
        description="Contract address to get events from"
    )
    network: Literal["avalanche", "ethereum"] = Field(
        default="avalanche",
        description="Network to query events on"
    )

    @field_validator('contract_address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid contract address format')
        return v.lower()

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    """
    Response schema for a single event.
    
    Attributes
    ----------
    transaction_hash : str
        Transaction hash
    block_number : int
        Block number
    log_index : int
        Log index
    event_name : str
        Event name
    args : dict
        Event arguments
    address : str
        Contract address
    """
    transaction_hash: str
    block_number: int
    log_index: int
    event_name: str
    args: dict
    address: str

    model_config = ConfigDict(from_attributes=True)


class EventsResponse(BaseModel):
    """
    Response schema for events query.
    
    Attributes
    ----------
    contract_address : str
        Contract address
    from_block : int
        Starting block
    to_block : int
        Ending block (current block)
    events : list[EventResponse]
        List of events
    network : str
        Network name
    total_events : int
        Total number of events
    """
    contract_address: str
    from_block: int
    to_block: int
    events: list[EventResponse]
    network: str
    total_events: int

    model_config = ConfigDict(from_attributes=True)

