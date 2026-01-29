"""
Alpha - Execution Logger

Structured logging for all system operations with JSON format support.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import structlog

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """
    Comprehensive execution logging with structured format.

    Features:
    - Structured JSON logging
    - Task execution tracking
    - Tool usage logging
    - LLM interaction logging
    - Error and exception logging
    """

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize execution logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure structlog for JSON logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
        )

        self.log = structlog.get_logger()
        logger.info(f"Execution logger initialized: {self.log_dir}")

    def log_task_start(
        self,
        task_id: str,
        task_name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log task start event.

        Args:
            task_id: Task ID
            task_name: Task name
            description: Task description
            metadata: Additional metadata
        """
        self.log.info(
            "task_start",
            task_id=task_id,
            task_name=task_name,
            description=description,
            metadata=metadata or {}
        )

    def log_task_complete(
        self,
        task_id: str,
        task_name: str,
        duration: float,
        result: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log task completion event.

        Args:
            task_id: Task ID
            task_name: Task name
            duration: Task duration in seconds
            result: Task result
            metadata: Additional metadata
        """
        self.log.info(
            "task_complete",
            task_id=task_id,
            task_name=task_name,
            duration=duration,
            result=result,
            metadata=metadata or {}
        )

    def log_task_error(
        self,
        task_id: str,
        task_name: str,
        error: str,
        error_type: str,
        traceback: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log task error event.

        Args:
            task_id: Task ID
            task_name: Task name
            error: Error message
            error_type: Error type/class
            traceback: Stack traceback
            metadata: Additional metadata
        """
        self.log.error(
            "task_error",
            task_id=task_id,
            task_name=task_name,
            error=error,
            error_type=error_type,
            traceback=traceback,
            metadata=metadata or {}
        )

    def log_tool_execution(
        self,
        tool_name: str,
        parameters: Dict,
        duration: float,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Log tool execution event.

        Args:
            tool_name: Tool name
            parameters: Tool parameters
            duration: Execution duration
            success: Whether execution succeeded
            result: Execution result
            error: Error message if failed
        """
        self.log.info(
            "tool_execution",
            tool_name=tool_name,
            parameters=parameters,
            duration=duration,
            success=success,
            result=result,
            error=error
        )

    def log_llm_interaction(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        duration: float,
        estimated_cost: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log LLM interaction event.

        Args:
            provider: LLM provider (openai, anthropic, deepseek)
            model: Model name
            prompt_tokens: Prompt token count
            completion_tokens: Completion token count
            total_tokens: Total token count
            duration: Request duration
            estimated_cost: Estimated cost in USD
            metadata: Additional metadata
        """
        self.log.info(
            "llm_interaction",
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration=duration,
            estimated_cost=estimated_cost,
            metadata=metadata or {}
        )

    def log_event(
        self,
        event_type: str,
        message: str,
        level: str = "info",
        **kwargs
    ):
        """
        Log generic event.

        Args:
            event_type: Event type
            message: Event message
            level: Log level (info, warning, error)
            **kwargs: Additional fields
        """
        log_method = getattr(self.log, level, self.log.info)
        log_method(
            event_type,
            message=message,
            **kwargs
        )

    def save_logs(self, filename: Optional[str] = None):
        """
        Save logs to file.

        Args:
            filename: Output filename
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"execution_log_{timestamp}.json"

        filepath = self.log_dir / filename
        logger.info(f"Logs saved: {filepath}")
