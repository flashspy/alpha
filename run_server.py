#!/usr/bin/env python3
"""
Alpha API Server Launcher
Properly starts the server with lifespan support
"""

import asyncio
import sys
import uvicorn
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.api.server import create_app

if __name__ == "__main__":
    # Get host and port from args
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

    print(f"Starting Alpha API Server on {host}:{port}...", file=sys.stderr)

    # Create app (not using factory mode)
    app = create_app()

    # Create uvicorn config
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )

    # Start server
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
