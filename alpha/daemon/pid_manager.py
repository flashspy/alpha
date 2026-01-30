"""
PID Manager for Daemon Process

Manages process ID file to prevent duplicate daemon instances.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PIDManager:
    """
    Manages PID file for daemon process.

    Features:
    - Create and lock PID file
    - Check for existing running instances
    - Clean up stale PID files
    - Remove PID file on shutdown
    """

    def __init__(self, pid_file: str = "/var/run/alpha/alpha.pid"):
        """
        Initialize PID manager.

        Args:
            pid_file: Path to PID file
        """
        self.pid_file = Path(pid_file)
        self.pid = os.getpid()

    def write(self) -> bool:
        """
        Write current process ID to PID file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)

            # Check for existing PID
            if self.is_running():
                logger.error(f"Alpha daemon already running with PID {self.read()}")
                return False

            # Write PID to file
            with open(self.pid_file, 'w') as f:
                f.write(str(self.pid))

            logger.info(f"PID file created: {self.pid_file} (PID: {self.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")
            return False

    def read(self) -> Optional[int]:
        """
        Read PID from PID file.

        Returns:
            PID if file exists and is valid, None otherwise
        """
        try:
            if not self.pid_file.exists():
                return None

            with open(self.pid_file, 'r') as f:
                pid_str = f.read().strip()
                return int(pid_str) if pid_str else None

        except Exception as e:
            logger.warning(f"Failed to read PID file: {e}")
            return None

    def is_running(self) -> bool:
        """
        Check if a process with the PID in PID file is running.

        Returns:
            True if process is running, False otherwise
        """
        pid = self.read()
        if pid is None:
            return False

        # Check if process exists
        try:
            # Send signal 0 to check if process exists (doesn't actually send signal)
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            # Process doesn't exist - stale PID file
            logger.warning(f"Stale PID file found for non-existent process {pid}")
            self.remove()
            return False
        except PermissionError:
            # Process exists but we don't have permission
            return True

    def remove(self) -> bool:
        """
        Remove PID file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.info(f"PID file removed: {self.pid_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove PID file: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        if not self.write():
            raise RuntimeError("Failed to create PID file - daemon may already be running")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up PID file."""
        self.remove()
