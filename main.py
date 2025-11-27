from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dishka.integrations.fastapi import setup_dishka

from core.container import container
from core.exception_handler import (
    validation_exception_handler,
    http_exception_handler,
    starlette_exception_handler,
    custom_exception_handler
)
from core.exceptions import BaseCustomException
from blockchain.router import router as blockchain_router

app = FastAPI(
    title="Blockchain API Service",
    version="1.3.3.7",
    description="Test task for backend developer",
)

setup_dishka(container, app)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
app.add_exception_handler(BaseCustomException, custom_exception_handler)
app.add_exception_handler(Exception, custom_exception_handler)

app.include_router(blockchain_router)


@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns
    -------
    dict
        Application information
    """
    return {
        "name": "Blockchain API Service",
        "version": "1.3.3.7",
        "description": "Test task for backend developer",
        "endpoints": {
            "balance": "/api/blockchain/balance",
            "events": "/api/blockchain/events",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """
    Basic (or based xD) health check endpoint.
    
    Returns
    -------
    dict
        Health status
    """
    return {"status": "healthy but depressed", "version": "1.3.3.7"}

