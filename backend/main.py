"""
Main FastAPI application entry point.

Run with: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.presentations import router as presentations_router
from api.v1.auth import router as auth_router
from analyzer.logging_config import setup_logging
import config
import db

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Selki API",
    description="Presentation analysis API for speech coaching",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(presentations_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "selki-api"}


@app.get("/")
async def root():
    return {
        "message": "Selki API",
        "version": "1.0.0",
        "docs": "/docs",
    }
