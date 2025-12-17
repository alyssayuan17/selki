"""
Main FastAPI application entry point.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.presentations import router as presentations_router
from analyzer.logging_config import setup_logging

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Triple-TS Speaks API",
    description="Presentation analysis API for speech coaching",
    version="1.0.0",
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(presentations_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "triple-ts-speaks-api"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Triple-TS Speaks API",
        "version": "1.0.0",
        "docs": "/docs",
    }
