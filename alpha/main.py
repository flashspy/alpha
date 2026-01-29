"""Alpha AI Assistant - Main Entry Point"""

import asyncio
import logging
import sys
from pathlib import Path

from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/alpha.log')
        ]
    )


async def main():
    """Main entry point."""
    # Setup logging
    Path('logs').mkdir(exist_ok=True)
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Alpha AI Assistant Starting...")
    logger.info("=" * 60)

    try:
        # Load configuration
        config = load_config('config.yaml')
        logger.info(f"Loaded configuration: {config.name} v{config.version}")

        # Create and start engine
        engine = AlphaEngine(config)
        await engine.startup()

        # Run main loop
        await engine.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
