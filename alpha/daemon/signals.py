"""
Signal Handler for Daemon Process

Handles Unix signals for graceful shutdown and configuration reload.
"""

import signal
import logging
import asyncio
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SignalHandler:
    """
    Manages Unix signal handling for daemon process.

    Signals:
    - SIGTERM: Graceful shutdown
    - SIGINT: Immediate shutdown (Ctrl+C)
    - SIGHUP: Reload configuration
    """

    def __init__(self):
        """Initialize signal handler."""
        self.should_exit = False
        self.should_reload = False
        self.shutdown_callback: Optional[Callable] = None
        self.reload_callback: Optional[Callable] = None

    def setup(self, shutdown_callback: Optional[Callable] = None,
              reload_callback: Optional[Callable] = None):
        """
        Setup signal handlers.

        Args:
            shutdown_callback: Function to call on shutdown signal
            reload_callback: Function to call on reload signal
        """
        self.shutdown_callback = shutdown_callback
        self.reload_callback = reload_callback

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGHUP, self._handle_sighup)

        logger.info("Signal handlers registered (SIGTERM, SIGINT, SIGHUP)")

    def _handle_sigterm(self, signum, frame):
        """
        Handle SIGTERM signal (graceful shutdown).

        This is typically sent by systemd or 'kill' command.
        """
        logger.info("Received SIGTERM - initiating graceful shutdown")
        self.should_exit = True

        if self.shutdown_callback:
            try:
                # Try to call the shutdown callback
                if asyncio.iscoroutinefunction(self.shutdown_callback):
                    # If callback is async, schedule it
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.shutdown_callback())
                    else:
                        loop.run_until_complete(self.shutdown_callback())
                else:
                    self.shutdown_callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback: {e}")

    def _handle_sigint(self, signum, frame):
        """
        Handle SIGINT signal (Ctrl+C).

        Immediate shutdown request from user.
        """
        logger.info("Received SIGINT - initiating immediate shutdown")
        self.should_exit = True

        if self.shutdown_callback:
            try:
                if asyncio.iscoroutinefunction(self.shutdown_callback):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.shutdown_callback())
                    else:
                        loop.run_until_complete(self.shutdown_callback())
                else:
                    self.shutdown_callback()
            except Exception as e:
                logger.error(f"Error in shutdown callback: {e}")

    def _handle_sighup(self, signum, frame):
        """
        Handle SIGHUP signal (reload configuration).

        This allows reloading configuration without restarting the daemon.
        """
        logger.info("Received SIGHUP - reloading configuration")
        self.should_reload = True

        if self.reload_callback:
            try:
                if asyncio.iscoroutinefunction(self.reload_callback):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.reload_callback())
                    else:
                        loop.run_until_complete(self.reload_callback())
                else:
                    self.reload_callback()
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")

    def reset_reload_flag(self):
        """Reset the reload flag after configuration has been reloaded."""
        self.should_reload = False
