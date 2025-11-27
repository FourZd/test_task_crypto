from fastapi import APIRouter
from dishka.integrations.fastapi import inject
from dishka import FromComponent
from typing import Annotated
from blockchain.schemas import (
    GetBalanceRequest,
    BalanceResponse,
    GetEventsRequest,
    EventsResponse
)
from blockchain.usecases import GetWalletBalanceUseCase, GetContractEventsUseCase

router = APIRouter(
    prefix="/api/blockchain",
    tags=["Blockchain"]
)


@router.post("/balance", response_model=BalanceResponse)
@inject
async def get_wallet_balance(
    request: GetBalanceRequest,
    use_case: Annotated[
        GetWalletBalanceUseCase, FromComponent("blockchain")
    ]
) -> BalanceResponse:
    """Get wallet balance at specific block."""
    return await use_case(
        wallet_address=request.wallet_address,
        block_number=request.block_number,
        network=request.network
    )


@router.post("/events", response_model=EventsResponse)
@inject
async def get_contract_events(
    request: GetEventsRequest,
    use_case: Annotated[
        GetContractEventsUseCase, FromComponent("blockchain")
    ]
) -> EventsResponse:
    """Get all contract events from specified block to current."""
    return await use_case(
        contract_address=request.contract_address,
        from_block=request.from_block,
        network=request.network
    )

