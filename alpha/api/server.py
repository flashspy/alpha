"""
Alpha REST API Server

FastAPI-based HTTP API for Alpha daemon interaction.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routes import tasks, status, health
from .schemas import ErrorResponse
from .dependencies import set_engine
from ..core.engine import AlphaEngine
from ..utils.config import load_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""

    logger.info("Starting Alpha API Server...")

    # Load configuration from project root
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config.yaml"
    config = load_config(str(config_path))

    # Initialize Alpha engine
    engine = AlphaEngine(config)
    await engine.startup()
    set_engine(engine)

    logger.info("Alpha API Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Alpha API Server...")
    await engine.shutdown()
    logger.info("Alpha API Server shut down")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="Alpha REST API",
        description="HTTP API for Alpha AI Assistant",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail=str(exc)
            ).model_dump()
        )

    # Include routers
    app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
    app.include_router(status.router, prefix="/api/v1", tags=["status"])
    app.include_router(health.router, prefix="/api", tags=["health"])

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Alpha REST API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/api/docs"
        }

    return app


async def start_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    reload: bool = False
):
    """
    Start API server.

    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload (development only)
    """
    logger.info(f"Starting API server on {host}:{port}")

    config = uvicorn.Config(
        app="alpha.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # For development testing
    asyncio.run(start_server(reload=True))
