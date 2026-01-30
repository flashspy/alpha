"""
Sandbox Manager for Safe Code Execution

This module provides Docker-based isolated execution environments for running
untrusted code safely. It implements resource limits, network isolation,
filesystem restrictions, and automatic cleanup.

Security Features:
- Docker container isolation
- Resource limits (CPU, memory, timeout)
- Network disabled by default
- Read-only root filesystem
- Non-root execution when possible
- Automatic cleanup on success or failure

Phase: 4.1 - Code Generation & Safe Execution
Requirements: REQ-4.2 (Safe Code Execution Sandbox)
"""

import os
import time
import tempfile
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """
    Configuration for sandbox execution environment.

    Attributes:
        language: Programming language (python, javascript, bash)
        docker_image: Docker image to use for execution
        timeout: Maximum execution time in seconds
        memory: Memory limit (e.g., "256m", "512m")
        cpu_quota: CPU quota (50000 = 50% of one CPU, 100000 = 100%)
        network_mode: Docker network mode ("none", "bridge", "host")
        working_dir: Working directory inside container
        read_only_rootfs: Mount root filesystem as read-only
        user: User to run as inside container (e.g., "1000:1000")
    """
    language: str
    docker_image: str
    timeout: int = 30
    memory: str = "256m"
    cpu_quota: int = 50000  # 50% of one CPU
    network_mode: str = "none"  # Isolated by default
    working_dir: str = "/workspace"
    read_only_rootfs: bool = True
    user: Optional[str] = None  # Run as non-root when specified


@dataclass
class ExecutionResult:
    """
    Result of code execution in sandbox.

    Attributes:
        success: Whether execution completed successfully (exit_code == 0)
        stdout: Standard output captured from execution
        stderr: Standard error captured from execution
        exit_code: Process exit code
        execution_time: Actual execution time in seconds
        error_message: Error message if execution failed
        timed_out: Whether execution was terminated due to timeout
        container_id: Docker container ID (for debugging)
    """
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None
    timed_out: bool = False
    container_id: Optional[str] = None


class DockerNotAvailableError(Exception):
    """Raised when Docker is not available or not running."""
    pass


class ContainerCreationError(Exception):
    """Raised when container creation fails."""
    pass


class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds timeout."""
    pass


class SandboxManager:
    """
    Manages Docker-based sandboxed code execution.

    This class handles the complete lifecycle of sandboxed code execution:
    1. Create temporary workspace
    2. Create isolated Docker container
    3. Execute code with resource limits
    4. Capture output and errors
    5. Clean up resources

    Example:
        >>> config = SandboxConfig(
        ...     language="python",
        ...     docker_image="python:3.12-slim",
        ...     timeout=30
        ... )
        >>> manager = SandboxManager(config)
        >>> if manager.is_docker_available():
        ...     container_id = manager.create_container("python", "print('Hello')")
        ...     result = manager.execute_code(container_id, timeout=30)
        ...     manager.cleanup_container(container_id)
        ...     print(result.stdout)
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        Initialize sandbox manager.

        Args:
            config: Optional default configuration. If not provided,
                   configuration must be specified per execution.
        """
        self.config = config
        self._docker_client = None
        self._docker_available = None
        self._active_containers: Dict[str, Any] = {}

        logger.info("SandboxManager initialized")

    @property
    def docker_client(self):
        """
        Lazy-load Docker client.

        Returns:
            Docker client instance

        Raises:
            DockerNotAvailableError: If Docker is not available
        """
        if self._docker_client is None:
            try:
                import docker
                self._docker_client = docker.from_env()
                # Test connection
                self._docker_client.ping()
                logger.info("Docker client initialized successfully")
            except ImportError:
                raise DockerNotAvailableError(
                    "Docker SDK not installed. Install with: pip install docker"
                )
            except Exception as e:
                raise DockerNotAvailableError(
                    f"Docker is not available or not running: {str(e)}"
                )
        return self._docker_client

    def is_docker_available(self) -> bool:
        """
        Check if Docker is installed and running.

        Returns:
            True if Docker is available, False otherwise
        """
        if self._docker_available is not None:
            return self._docker_available

        try:
            self.docker_client.ping()
            self._docker_available = True
            logger.info("Docker is available and running")
            return True
        except DockerNotAvailableError as e:
            logger.warning(f"Docker not available: {str(e)}")
            self._docker_available = False
            return False
        except Exception as e:
            logger.error(f"Error checking Docker availability: {str(e)}")
            self._docker_available = False
            return False

    def create_container(
        self,
        language: str,
        code: str,
        config: Optional[SandboxConfig] = None
    ) -> str:
        """
        Create Docker container for code execution.

        This method:
        1. Creates temporary workspace directory
        2. Writes code to file with appropriate extension
        3. Creates Docker container with resource limits
        4. Mounts workspace into container
        5. Returns container ID for later execution

        Args:
            language: Programming language (python, javascript, bash)
            code: Code to execute
            config: Optional execution configuration (overrides default)

        Returns:
            Container ID string

        Raises:
            DockerNotAvailableError: If Docker is not available
            ContainerCreationError: If container creation fails
        """
        if not self.is_docker_available():
            raise DockerNotAvailableError("Docker is required for sandboxed execution")

        # Use provided config or default
        exec_config = config or self.config
        if exec_config is None:
            raise ValueError("No configuration provided")

        logger.info(f"Creating container for {language} code execution")

        try:
            # Get language-specific configuration
            from .languages import get_handler
            handler = get_handler(language)
            lang_config = handler.get_execution_config()

            # Create temporary workspace
            workspace = tempfile.mkdtemp(prefix=f"alpha_sandbox_{language}_")
            logger.debug(f"Created workspace: {workspace}")

            # Determine file extension and write code
            extensions = {
                "python": "py",
                "javascript": "js",
                "js": "js",
                "bash": "sh",
                "sh": "sh"
            }
            ext = extensions.get(language.lower(), "txt")
            code_file = Path(workspace) / f"code.{ext}"

            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)

            # Make bash scripts executable
            if language.lower() in ["bash", "sh"]:
                os.chmod(code_file, 0o755)

            logger.debug(f"Code written to: {code_file}")

            # Prepare container configuration
            docker_config = {
                "image": exec_config.docker_image,
                "command": lang_config["command"] + [f"{exec_config.working_dir}/code.{ext}"],
                "detach": True,
                "network_mode": exec_config.network_mode,
                "mem_limit": exec_config.memory,
                "cpu_quota": exec_config.cpu_quota,
                "cpu_period": 100000,  # Standard period
                "volumes": {
                    workspace: {
                        "bind": exec_config.working_dir,
                        "mode": "rw"  # Container needs write access to workspace
                    }
                },
                "working_dir": exec_config.working_dir,
                "read_only": exec_config.read_only_rootfs,
                "remove": False,  # Manual cleanup for better control
                "stdin_open": False,
                "tty": False,
            }

            # Add user if specified (non-root execution)
            if exec_config.user:
                docker_config["user"] = exec_config.user

            # Add tmpfs for writable /tmp when using read-only rootfs
            if exec_config.read_only_rootfs:
                docker_config["tmpfs"] = {
                    "/tmp": "rw,noexec,nosuid,size=10m"
                }

            # Pull image if not available
            try:
                self.docker_client.images.get(exec_config.docker_image)
            except Exception:
                logger.info(f"Pulling Docker image: {exec_config.docker_image}")
                self.docker_client.images.pull(exec_config.docker_image)

            # Create container
            container = self.docker_client.containers.create(**docker_config)
            container_id = container.id

            # Track container and workspace for cleanup
            self._active_containers[container_id] = {
                "container": container,
                "workspace": workspace,
                "language": language
            }

            logger.info(f"Container created: {container_id[:12]}")
            return container_id

        except Exception as e:
            # Clean up workspace on failure
            if 'workspace' in locals():
                try:
                    import shutil
                    shutil.rmtree(workspace, ignore_errors=True)
                except Exception:
                    pass

            error_msg = f"Failed to create container: {str(e)}"
            logger.error(error_msg)
            raise ContainerCreationError(error_msg) from e

    def execute_code(
        self,
        container_id: str,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute code in container with timeout.

        This method:
        1. Starts the container
        2. Waits for completion with timeout
        3. Captures stdout and stderr
        4. Returns execution result

        Args:
            container_id: Container ID from create_container()
            timeout: Execution timeout in seconds (uses config default if not provided)

        Returns:
            ExecutionResult with output and status

        Raises:
            ValueError: If container_id is not found
            ExecutionTimeoutError: If execution exceeds timeout
        """
        if container_id not in self._active_containers:
            raise ValueError(f"Container not found: {container_id}")

        container_info = self._active_containers[container_id]
        container = container_info["container"]

        # Use provided timeout or config default
        if timeout is None:
            timeout = self.config.timeout if self.config else 30

        logger.info(f"Executing code in container {container_id[:12]} (timeout: {timeout}s)")

        start_time = time.time()
        result = ExecutionResult(
            success=False,
            container_id=container_id
        )

        try:
            # Start container
            container.start()

            # Wait for completion with timeout
            exit_status = container.wait(timeout=timeout)

            # Extract exit code (format varies by Docker API version)
            if isinstance(exit_status, dict):
                result.exit_code = exit_status.get("StatusCode", 0)
            else:
                result.exit_code = exit_status

            # Capture output
            result.stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            result.stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            # Calculate execution time
            result.execution_time = time.time() - start_time

            # Determine success
            result.success = (result.exit_code == 0)

            if result.success:
                logger.info(f"Execution completed successfully in {result.execution_time:.2f}s")
            else:
                result.error_message = f"Process exited with code {result.exit_code}"
                logger.warning(f"Execution failed: {result.error_message}")

            return result

        except Exception as e:
            result.execution_time = time.time() - start_time

            # Check if it's a timeout
            if "timed out" in str(e).lower() or result.execution_time >= timeout:
                result.timed_out = True
                result.error_message = f"Execution exceeded timeout of {timeout}s"
                logger.warning(result.error_message)

                # Try to stop the container
                try:
                    container.stop(timeout=5)
                except Exception:
                    try:
                        container.kill()
                    except Exception:
                        pass
            else:
                result.error_message = f"Execution error: {str(e)}"
                logger.error(result.error_message)

            # Try to capture any output before failure
            try:
                result.stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
                result.stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
            except Exception:
                pass

            return result

    def cleanup_container(self, container_id: str) -> None:
        """
        Clean up container and associated resources.

        This method:
        1. Stops container if running
        2. Removes container
        3. Deletes temporary workspace
        4. Removes from tracking

        Args:
            container_id: Container ID to clean up
        """
        if container_id not in self._active_containers:
            logger.warning(f"Container not found for cleanup: {container_id}")
            return

        logger.info(f"Cleaning up container {container_id[:12]}")

        container_info = self._active_containers[container_id]
        container = container_info["container"]
        workspace = container_info["workspace"]

        # Stop and remove container
        try:
            # Try graceful stop first
            try:
                container.stop(timeout=5)
            except Exception:
                # Force kill if stop fails
                try:
                    container.kill()
                except Exception:
                    pass

            # Remove container
            try:
                container.remove(force=True)
            except Exception as e:
                logger.warning(f"Failed to remove container: {str(e)}")
        except Exception as e:
            logger.error(f"Error during container cleanup: {str(e)}")

        # Clean up workspace
        try:
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)
            logger.debug(f"Workspace removed: {workspace}")
        except Exception as e:
            logger.warning(f"Failed to remove workspace: {str(e)}")

        # Remove from tracking
        del self._active_containers[container_id]

        logger.info(f"Container {container_id[:12]} cleaned up successfully")

    def enforce_limits(self, container_id: str) -> None:
        """
        Enforce resource limits on running container.

        This method can be used to update resource limits on a running container,
        though Docker's support for this is limited. Most limits should be set
        during container creation.

        Args:
            container_id: Container ID to enforce limits on

        Note:
            This method is provided for completeness but has limited functionality.
            Resource limits are best set during container creation.
        """
        if container_id not in self._active_containers:
            logger.warning(f"Container not found: {container_id}")
            return

        container_info = self._active_containers[container_id]
        container = container_info["container"]

        logger.info(f"Checking resource limits for container {container_id[:12]}")

        try:
            # Reload container state
            container.reload()

            # Get container stats
            stats = container.stats(stream=False)

            # Log current resource usage
            if "memory_stats" in stats:
                memory_usage = stats["memory_stats"].get("usage", 0)
                memory_limit = stats["memory_stats"].get("limit", 0)
                if memory_limit > 0:
                    memory_percent = (memory_usage / memory_limit) * 100
                    logger.debug(f"Memory usage: {memory_percent:.1f}%")

            if "cpu_stats" in stats:
                logger.debug("CPU stats available")

        except Exception as e:
            logger.warning(f"Failed to check resource limits: {str(e)}")

    def cleanup_all(self) -> None:
        """
        Clean up all active containers.

        This is useful for emergency cleanup or shutdown.
        """
        logger.info(f"Cleaning up {len(self._active_containers)} active containers")

        # Create list of container IDs to avoid modifying dict during iteration
        container_ids = list(self._active_containers.keys())

        for container_id in container_ids:
            try:
                self.cleanup_container(container_id)
            except Exception as e:
                logger.error(f"Failed to cleanup container {container_id[:12]}: {str(e)}")

    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.cleanup_all()
        except Exception:
            pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_all()
        return False


# Convenience function for simple execution
def execute_code_sandboxed(
    language: str,
    code: str,
    timeout: int = 30,
    memory: str = "256m",
    network_enabled: bool = False
) -> ExecutionResult:
    """
    Execute code in sandbox (convenience function).

    This is a high-level convenience function that handles the complete
    execution lifecycle: create container, execute, cleanup.

    Args:
        language: Programming language (python, javascript, bash)
        code: Code to execute
        timeout: Maximum execution time in seconds
        memory: Memory limit (e.g., "256m")
        network_enabled: Whether to enable network access

    Returns:
        ExecutionResult with output and status

    Example:
        >>> result = execute_code_sandboxed(
        ...     language="python",
        ...     code="print('Hello, World!')",
        ...     timeout=10
        ... )
        >>> print(result.stdout)
        Hello, World!
    """
    # Get language-specific configuration
    from .languages import get_handler
    handler = get_handler(language)
    lang_config = handler.get_execution_config()

    # Create configuration
    config = SandboxConfig(
        language=language,
        docker_image=lang_config["docker_image"],
        timeout=timeout,
        memory=memory,
        network_mode="bridge" if network_enabled else "none"
    )

    # Execute with automatic cleanup
    with SandboxManager(config) as manager:
        container_id = manager.create_container(language, code, config)
        try:
            result = manager.execute_code(container_id, timeout)
            return result
        finally:
            manager.cleanup_container(container_id)
