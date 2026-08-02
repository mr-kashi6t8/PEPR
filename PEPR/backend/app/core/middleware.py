import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import contextvars
import logging

correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="UNKNOWN")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id.set(req_id)
        
        # Inject correlation ID into loggers
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = correlation_id.get()
            return record
        logging.setLogRecordFactory(record_factory)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
