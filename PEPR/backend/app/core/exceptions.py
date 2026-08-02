from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("pepr")

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "data": {},
            "meta": {},
            "error": "Internal Server Error"
        },
    )
