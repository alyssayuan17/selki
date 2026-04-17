"""
Main FastAPI application entry point.

Run with: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.v1.presentations import router as presentations_router
from api.v1.auth import router as auth_router
from analyzer.logging_config import setup_logging
import config
import db

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

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


# Serve built frontend (production)
if FRONTEND_DIST.exists():
    # Vite-generated hashed assets
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Catch-all: serve root-level static files (favicon, SVGs, etc.) if they exist,
    # otherwise serve index.html so React Router handles the path.
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
