from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import global_exception_handler
from app.core.middleware import RequestIDMiddleware
from app.core.logging import setup_logging
from app.api.v1.router import api_router
import logging

setup_logging()
logger = logging.getLogger("pepr")

from app.core.scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

# Middleware
app.add_middleware(RequestIDMiddleware)

cors_origins = [str(origin) for origin in settings.CORS_ORIGINS] if settings.CORS_ORIGINS else ["*"]
allow_creds = False if "*" in cors_origins else True
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)

# Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to the PEPR API"}
