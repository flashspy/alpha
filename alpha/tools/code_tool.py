"""
Code Execution Tool

Integrates the Code Execution system with Alpha's tool registry.
Enables the LLM agent to generate and execute custom code in a safe isolated environment.

Phase: 4.1 - Code Generation & Safe Execution
Requirements: REQ-4.3 - Code Execution Tool
Day 5: Tool Integration & Documentation
"""

import logging
from typing import Dict, Any, Optional

from alpha.tools.registry import Tool, ToolResult
from alpha.code_execution import (
    CodeGenerator,
    CodeValidator,
    SandboxManager,
    CodeExecutor,
    ExecutionOptions,
    CodeGenerationError
)
from alpha.code_execution.executor import UserRejectionError, ExecutionError

logger = logging.getLogger(__name__)


class CodeExecutionTool(Tool):
    """
    Tool for generating and executing custom code in a safe isolated environment.

    This tool integrates Alpha's code execution capabilities into the tool system,
    allowing the LLM agent to write, validate, and execute code when existing
    tools are insufficient for a task.

    Features:
    - Multi-language support (Python, JavaScript, Bash)
    - LLM-powered code generation
    - Syntax and security validation
    - Docker-based sandboxed execution
    - User approval workflow
    - Resource limits and timeouts
    - Automatic cleanup

    Example Usage:
        # Generate and execute code from a task description
        result = await tool.execute(
            task="Calculate the factorial of 10",
            language="python"
        )

        # Execute provided code directly
        result = await tool.execute(
            code="print('Hello, World!')",
            language="python",
            require_approval=False
        )

    Security:
    - Code is executed in isolated Docker containers
    - Network access disabled by default
    - Resource limits enforced (CPU, memory, time)
    - Security scanning before execution
    - User approval required by default
    """

    def __init__(self, llm_service, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Code Execution Tool.

        Args:
            llm_service: Alpha's LLM service for code generation
            config: Optional configuration dictionary for code execution settings
        """
        super().__init__(
            name="code_execution",
            description="Generate and execute custom code in a safe isolated environment. "
                       "Supports Python, JavaScript, and Bash. Use when existing tools are "
                       "insufficient for complex tasks requiring custom scripts."
        )

        self.llm_service = llm_service
        self.config = config or {}

        # Initialize code execution components (lazy initialization)
        self._generator: Optional[CodeGenerator] = None
        self._validator: Optional[CodeValidator] = None
        self._sandbox: Optional[SandboxManager] = None
        self._executor: Optional[CodeExecutor] = None

        # Track if Docker is available
        self._docker_available: Optional[bool] = None

        logger.info("CodeExecutionTool initialized")

    def _ensure_components_initialized(self) -> None:
        """
        Lazily initialize code execution components on first use.

        This allows the tool to be registered even if Docker is not available,
        providing graceful error messages at execution time.
        """
        if self._executor is not None:
            return  # Already initialized

        logger.info("Initializing code execution components")

        try:
            # Initialize components
            self._generator = CodeGenerator(self.llm_service)
            self._validator = CodeValidator()
            self._sandbox = SandboxManager()
            self._executor = CodeExecutor(
                generator=self._generator,
                validator=self._validator,
                sandbox=self._sandbox
            )

            # Check Docker availability
            self._docker_available = self._sandbox.is_docker_available()

            if not self._docker_available:
                logger.warning("Docker not available - code execution will fail at runtime")

            logger.info("Code execution components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize code execution components: {e}")
            raise

    async def execute(
        self,
        task: Optional[str] = None,
        code: Optional[str] = None,
        language: str = "python",
        timeout: int = 30,
        allow_network: bool = False,
        validate: bool = True,
        require_approval: bool = True,
        **kwargs
    ) -> ToolResult:
        """
        Execute the code execution tool.

        This method orchestrates the complete code execution pipeline:
        1. Validate parameters
        2. Initialize components if needed
        3. Generate code (if task provided) or use provided code
        4. Validate and execute code
        5. Return results

        Args:
            task: Description of what the code should do (required if code not provided)
            code: Code to execute directly (optional, will generate if not provided)
            language: Programming language (python, javascript, bash) - default: python
            timeout: Execution timeout in seconds - default: 30
            allow_network: Enable network access in sandbox - default: False
            validate: Run validation and security checks - default: True
            require_approval: Require user approval before execution - default: True
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with execution output and metadata

        Example:
            >>> # Generate code from task
            >>> result = await tool.execute(
            ...     task="Sort a list of numbers in ascending order",
            ...     language="python"
            ... )
            >>> print(result.output)

            >>> # Execute provided code
            >>> result = await tool.execute(
            ...     code="console.log('Hello');",
            ...     language="javascript",
            ...     require_approval=False
            ... )
        """
        logger.info(f"Code execution tool called with language={language}")

        try:
            # Step 1: Validate parameters
            validation_error = self._validate_parameters(task, code, language)
            if validation_error:
                return ToolResult(
                    success=False,
                    output=None,
                    error=validation_error,
                    metadata={"language": language}
                )

            # Step 2: Initialize components
            try:
                self._ensure_components_initialized()
            except Exception as e:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Failed to initialize code execution: {str(e)}",
                    metadata={"language": language}
                )

            # Step 3: Check Docker availability
            if not self._docker_available:
                return ToolResult(
                    success=False,
                    output=None,
                    error="Docker is not available. Code execution requires Docker to be installed and running.\n"
                          "Please install Docker and ensure the Docker daemon is running.\n"
                          "Installation: https://docs.docker.com/get-docker/",
                    metadata={"language": language, "docker_available": False}
                )

            # Step 4: Apply configuration defaults
            execution_config = self._build_execution_config(
                timeout=timeout,
                allow_network=allow_network,
                validate=validate,
                require_approval=require_approval
            )

            # Step 5: Execute code
            if task:
                # Generate and execute code from task description
                result = await self._execute_task(task, language, execution_config)
            else:
                # Execute provided code directly
                result = await self._execute_code_string(code, language, execution_config)

            # Step 6: Format and return result
            return self._format_result(result, language)

        except UserRejectionError as e:
            logger.info("User rejected code execution")
            return ToolResult(
                success=False,
                output=None,
                error="Code execution was rejected by the user",
                metadata={"language": language, "rejection": True}
            )

        except CodeGenerationError as e:
            logger.error(f"Code generation failed: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Code generation failed: {str(e)}",
                metadata={"language": language, "generation_error": True}
            )

        except ExecutionError as e:
            logger.error(f"Code execution failed: {e}")
            return ToolResult(
                success=False,
                output=None,
                error=f"Code execution failed: {str(e)}",
                metadata={"language": language, "execution_error": True}
            )

        except Exception as e:
            logger.error(f"Unexpected error in code execution tool: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=f"Unexpected error: {str(e)}",
                metadata={"language": language}
            )

    def _validate_parameters(
        self,
        task: Optional[str],
        code: Optional[str],
        language: str
    ) -> Optional[str]:
        """
        Validate tool parameters.

        Args:
            task: Task description
            code: Code string
            language: Programming language

        Returns:
            Error message if validation fails, None if valid
        """
        # Either task or code must be provided
        if not task and not code:
            return "Either 'task' or 'code' parameter must be provided"

        # Both task and code should not be provided
        if task and code:
            return "Provide either 'task' OR 'code', not both"

        # Validate language
        supported_languages = ["python", "javascript", "bash"]
        if language.lower() not in supported_languages:
            return f"Unsupported language: {language}. Supported: {', '.join(supported_languages)}"

        # Validate task/code content
        if task and not task.strip():
            return "Task description cannot be empty"

        if code and not code.strip():
            return "Code cannot be empty"

        return None  # Valid

    def _build_execution_config(
        self,
        timeout: int,
        allow_network: bool,
        validate: bool,
        require_approval: bool
    ) -> ExecutionOptions:
        """
        Build execution configuration from parameters and config file.

        Args:
            timeout: Execution timeout
            allow_network: Network access flag
            validate: Validation flag
            require_approval: Approval flag

        Returns:
            ExecutionOptions object
        """
        # Get defaults from config if available
        config_defaults = self.config.get("code_execution", {}).get("defaults", {})
        config_security = self.config.get("code_execution", {}).get("security", {})
        config_limits = self.config.get("code_execution", {}).get("limits", {})

        # Apply config defaults
        timeout = min(timeout, config_limits.get("max_execution_time", 300))
        validate = validate and config_security.get("scan_code", True)
        require_approval = require_approval or config_security.get("require_approval", True)

        return ExecutionOptions(
            generate_code=True,  # Will be set appropriately in execute methods
            validate_syntax=validate,
            check_security=validate,
            assess_quality=False,  # Optional feature, disabled for performance
            require_approval=require_approval,
            allow_network=allow_network,
            timeout=timeout,
            max_retries=2
        )

    async def _execute_task(
        self,
        task: str,
        language: str,
        config: ExecutionOptions
    ):
        """
        Execute a task by generating and running code.

        Args:
            task: Task description
            language: Programming language
            config: Execution options

        Returns:
            ExecutionResult from CodeExecutor
        """
        logger.info(f"Executing task: {task[:100]}...")

        # Ensure generate_code is enabled
        config.generate_code = True

        # Execute task
        result = await self._executor.execute_task(
            task=task,
            language=language,
            options=config,
            context=None  # Could pass additional context if needed
        )

        return result

    async def _execute_code_string(
        self,
        code: str,
        language: str,
        config: ExecutionOptions
    ):
        """
        Execute provided code string directly.

        Args:
            code: Code to execute
            language: Programming language
            config: Execution options

        Returns:
            ExecutionResult from CodeExecutor
        """
        logger.info(f"Executing provided {language} code ({len(code)} chars)")

        # Disable code generation since code is provided
        config.generate_code = False

        # Execute code
        result = await self._executor.execute_code_string(
            code=code,
            language=language,
            options=config
        )

        return result

    def _format_result(self, result, language: str) -> ToolResult:
        """
        Format execution result as ToolResult.

        Args:
            result: ExecutionResult from CodeExecutor
            language: Programming language

        Returns:
            ToolResult for tool system
        """
        if result.success:
            # Format successful execution
            output_parts = ["Code executed successfully"]

            if result.stdout and result.stdout.strip():
                output_parts.append(f"\nOutput:\n{result.stdout}")

            if result.stderr and result.stderr.strip():
                output_parts.append(f"\nWarnings/Info:\n{result.stderr}")

            output = "\n".join(output_parts)

            return ToolResult(
                success=True,
                output=output,
                error=None,
                metadata={
                    "language": language,
                    "execution_time": result.execution_time,
                    "exit_code": result.exit_code,
                    "timed_out": result.timed_out
                }
            )
        else:
            # Format failed execution
            error_parts = ["Code execution failed"]

            if result.error_message:
                error_parts.append(f"Error: {result.error_message}")

            if result.stderr and result.stderr.strip():
                error_parts.append(f"Standard Error:\n{result.stderr}")

            if result.timed_out:
                error_parts.append(f"Execution timed out (limit: {result.timeout}s)")

            error_message = "\n\n".join(error_parts)

            return ToolResult(
                success=False,
                output=result.stdout if result.stdout else None,
                error=error_message,
                metadata={
                    "language": language,
                    "execution_time": result.execution_time,
                    "exit_code": result.exit_code,
                    "timed_out": result.timed_out
                }
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics from the code executor.

        Returns:
            Dictionary with execution statistics

        Example:
            >>> stats = tool.get_statistics()
            >>> print(f"Success rate: {stats['success_rate']}%")
        """
        if self._executor:
            return self._executor.get_execution_statistics()
        else:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0
            }

    def is_available(self) -> bool:
        """
        Check if the code execution tool is available.

        Returns:
            True if Docker is available and components can be initialized
        """
        try:
            if self._docker_available is None:
                self._ensure_components_initialized()
            return self._docker_available
        except Exception:
            return False

    def __repr__(self) -> str:
        """String representation of the tool."""
        stats = self.get_statistics()
        return (
            f"CodeExecutionTool("
            f"executions={stats['total_executions']}, "
            f"success_rate={stats['success_rate']}%)"
        )
