from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from core.exceptions import BaseCustomException


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for request validation errors.
    
    Parameters
    ----------
    request : Request
        FastAPI request
    exc : RequestValidationError
        Validation error
        
    Returns
    -------
    JSONResponse
        Error response
    """
    errors = []
    for error in exc.errors():
        field_path = ".".join(
            str(x) for x in error["loc"] if not isinstance(x, int) and x != "body"
        )
        errors.append({
            "field": field_path or "body",
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation error",
            "errors": errors
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTP exceptions.
    
    Parameters
    ----------
    request : Request
        FastAPI request
    exc : HTTPException
        HTTP exception
        
    Returns
    -------
    JSONResponse
        Error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )


async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler for Starlette HTTP exceptions.
    
    Parameters
    ----------
    request : Request
        FastAPI request
    exc : StarletteHTTPException
        Starlette HTTP exception
        
    Returns
    -------
    JSONResponse
        Error response
    """
    return await http_exception_handler(request, HTTPException(status_code=exc.status_code, detail=exc.detail))


async def custom_exception_handler(request: Request, exc: Exception):
    """
    Handler for custom exceptions.
    
    Parameters
    ----------
    request : Request
        FastAPI request
    exc : Exception
        Exception
        
    Returns
    -------
    JSONResponse
        Error response
    """
    if isinstance(exc, BaseCustomException):
        return JSONResponse(
            status_code=exc.get_status_code(),
            content={
                "status": "error",
                "message": exc.message
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )

