"""
Daemon Process Core

Implements Unix daemon process creation and management.
"""

import os
import sys
import logging
import atexit
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DaemonContext:
    """
    Daemon process context manager.

    Handles:
    - Process forking and detachment
    - Standard streams redirection
    - Working directory setup
    - umask configuration
    - Proper cleanup on exit
    """

    def __init__(
        self,
        working_directory: str = '/',
        umask: int = 0o022,
        stdin: str = '/dev/null',
        stdout: str = '/dev/null',
        stderr: str = '/dev/null',
        pid_file: Optional[str] = None
    ):
        """
        Initialize daemon context.

        Args:
            working_directory: Daemon working directory
            umask: File creation mask
            stdin: Redirect stdin to this file
            stdout: Redirect stdout to this file
            stderr: Redirect stderr to this file
            pid_file: Path to PID file
        """
        self.working_directory = working_directory
        self.umask = umask
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pid_file = pid_file

    def __enter__(self):
        """Enter daemon context - daemonize the process."""
        daemonize(
            working_directory=self.working_directory,
            umask=self.umask,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit daemon context - cleanup."""
        if self.pid_file and Path(self.pid_file).exists():
            try:
                Path(self.pid_file).unlink()
                logger.info(f"Removed PID file: {self.pid_file}")
            except Exception as e:
                logger.error(f"Failed to remove PID file: {e}")


def daemonize(
    working_directory: str = '/',
    umask: int = 0o022,
    stdin: str = '/dev/null',
    stdout: str = '/dev/null',
    stderr: str = '/dev/null'
) -> None:
    """
    Convert current process to a daemon process.

    This follows the standard Unix double-fork technique:
    1. First fork to create child process
    2. Parent exits (child becomes orphan, adopted by init)
    3. Child becomes session leader
    4. Second fork to ensure daemon can't acquire controlling terminal
    5. First child exits
    6. Second child continues as daemon
    7. Redirect standard streams
    8. Set working directory and umask

    Args:
        working_directory: Daemon working directory
        umask: File creation mask
        stdin: Redirect stdin to this file
        stdout: Redirect stdout to this file
        stderr: Redirect stderr to this file

    Raises:
        OSError: If fork fails
    """
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent process - exit
            sys.exit(0)

    except OSError as e:
        logger.error(f"First fork failed: {e}")
        sys.exit(1)

    # Decouple from parent environment
    os.chdir(working_directory)
    os.setsid()  # Create new session and process group
    os.umask(umask)

    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # First child exits
            sys.exit(0)

    except OSError as e:
        logger.error(f"Second fork failed: {e}")
        sys.exit(1)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()

    # Open file descriptors for standard streams
    stdin_fd = open(stdin, 'r')
    stdout_fd = open(stdout, 'a+')
    stderr_fd = open(stderr, 'a+')

    # Redirect
    os.dup2(stdin_fd.fileno(), sys.stdin.fileno())
    os.dup2(stdout_fd.fileno(), sys.stdout.fileno())
    os.dup2(stderr_fd.fileno(), sys.stderr.fileno())

    logger.info(f"Daemon process created (PID: {os.getpid()})")


def is_daemon() -> bool:
    """
    Check if current process is running as a daemon.

    Returns:
        True if process is a daemon, False otherwise
    """
    # Simple heuristic: daemons typically have no controlling terminal
    # and parent process is 1 (init/systemd)
    return os.getppid() == 1 or not os.isatty(sys.stdin.fileno())
