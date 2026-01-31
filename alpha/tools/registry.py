"""
Alpha - Tool System

Extensible tool framework for executing various operations.
"""

import logging
import asyncio
import subprocess
import math
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

import aiohttp
import pytz
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Tool execution result."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Abstract base class for tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result
        """
        pass

    def validate_params(self, required: List[str], provided: Dict[str, Any]):
        """Validate required parameters."""
        missing = [p for p in required if p not in provided]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")


class ShellTool(Tool):
    """Execute shell commands."""

    def __init__(self):
        super().__init__(
            name="shell",
            description="Execute shell commands"
        )

    async def execute(self, command: str, timeout: int = 30, **kwargs) -> ToolResult:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            **kwargs: Additional parameters

        Returns:
            Tool result with command output
        """
        self.validate_params(["command"], {"command": command})

        logger.info(f"Executing command: {command}")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                success = process.returncode == 0
                output = stdout.decode() if stdout else ""
                error = stderr.decode() if stderr else None

                logger.info(f"Command finished with return code: {process.returncode}")

                return ToolResult(
                    success=success,
                    output=output,
                    error=error,
                    metadata={"returncode": process.returncode}
                )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")

        except Exception as e:
            logger.error(f"Command execution failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )


class FileTool(Tool):
    """File operations."""

    def __init__(self):
        super().__init__(
            name="file",
            description="Read, write, and manage files"
        )

    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute file operation.

        Args:
            operation: Operation type (read, write, append, delete, list)
            path: File path
            content: Content for write/append operations
            **kwargs: Additional parameters

        Returns:
            Tool result
        """
        self.validate_params(["operation", "path"], locals())

        logger.info(f"File operation: {operation} on {path}")

        try:
            file_path = Path(path)

            if operation == "read":
                if not file_path.exists():
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"File not found: {path}"
                    )

                content = file_path.read_text()
                return ToolResult(success=True, output=content)

            elif operation == "write":
                if content is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="Content required for write operation"
                    )

                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                return ToolResult(
                    success=True,
                    output=f"Written {len(content)} bytes to {path}"
                )

            elif operation == "append":
                if content is None:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="Content required for append operation"
                    )

                with file_path.open('a') as f:
                    f.write(content)
                return ToolResult(
                    success=True,
                    output=f"Appended {len(content)} bytes to {path}"
                )

            elif operation == "delete":
                if file_path.exists():
                    file_path.unlink()
                    return ToolResult(success=True, output=f"Deleted {path}")
                else:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"File not found: {path}"
                    )

            elif operation == "list":
                if file_path.is_dir():
                    files = [str(f) for f in file_path.iterdir()]
                    return ToolResult(success=True, output=files)
                else:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Not a directory: {path}"
                    )

            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"File operation failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )


class SearchTool(Tool):
    """Web search tool."""

    def __init__(self):
        super().__init__(
            name="search",
            description="Search the web for information"
        )

    async def execute(self, query: str, limit: int = 5, timeout: int = 30, **kwargs) -> ToolResult:
        """
        Search the web.

        Args:
            query: Search query
            limit: Maximum number of results
            timeout: Search timeout in seconds (default: 30)
            **kwargs: Additional parameters

        Returns:
            Tool result with search results
        """
        self.validate_params(["query"], {"query": query})

        logger.info(f"Searching for: {query}")

        try:
            from ddgs import DDGS

            # Use run_in_executor to call sync DDGS in async context with timeout
            loop = asyncio.get_event_loop()

            def do_search():
                # Configure DDGS with increased timeout
                with DDGS(timeout=timeout) as ddgs:
                    return list(ddgs.text(query, max_results=min(limit, 20)))

            # Add asyncio timeout wrapper
            raw_results = await asyncio.wait_for(
                loop.run_in_executor(None, do_search),
                timeout=timeout + 5  # Extra 5 seconds buffer
            )

            # Format results
            results = []
            for result in raw_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": "duckduckgo"
                })

            return ToolResult(
                success=True,
                output={
                    "query": query,
                    "results": results,
                    "count": len(results)
                },
                metadata={"source": "duckduckgo", "limit": limit}
            )

        except ImportError:
            logger.warning("ddgs not installed, using placeholder")
            return ToolResult(
                success=True,
                output={
                    "query": query,
                    "results": [
                        {
                            "title": "Example Result",
                            "url": "https://example.com",
                            "snippet": "Install ddgs for real results: pip install ddgs",
                            "source": "placeholder"
                        }
                    ]
                },
                metadata={"source": "placeholder"}
            )
        except asyncio.TimeoutError:
            error_msg = f"Search timed out after {timeout} seconds. Network may be slow or unavailable."
            logger.warning(error_msg)
            return ToolResult(
                success=False,
                output=None,
                error=error_msg,
                metadata={
                    "timeout": timeout,
                    "suggestion": "Try using HTTP tool to access specific websites directly, or check network connection."
                }
            )
        except Exception as e:
            # Check if it's a timeout exception from ddgs
            error_str = str(e)
            if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                error_msg = f"Search request timed out. The search engines may be unreachable from your network."
                logger.warning(f"{error_msg} Details: {error_str}")
                return ToolResult(
                    success=False,
                    output=None,
                    error=error_msg,
                    metadata={
                        "timeout": timeout,
                        "suggestion": "Network connectivity issue detected. Consider using HTTP tool for direct API access."
                    }
                )

            logger.error(f"Search failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )


class HTTPTool(Tool):
    """HTTP request tool for API calls and web content fetching."""

    def __init__(self):
        super().__init__(
            name="http",
            description="Execute HTTP requests to fetch data from APIs and websites (supports JSON, HTML, and text content)"
        )

    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        follow_redirects: bool = True,
        **kwargs
    ) -> ToolResult:
        """
        Execute HTTP request.

        Args:
            url: Target URL
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            headers: Request headers
            params: Query parameters
            data: Request body data
            json: JSON request body
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow redirects
            **kwargs: Additional parameters

        Returns:
            Tool result with response data
        """
        self.validate_params(["url", "method"], {"url": url, "method": method})

        if not self._validate_url(url):
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid URL: {url}"
            )

        method = method.upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unsupported HTTP method: {method}"
            )

        logger.info(f"HTTP {method} request to {url}")

        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=follow_redirects
                ) as response:
                    elapsed = (datetime.now() - start_time).total_seconds()

                    response_headers = dict(response.headers)
                    status_code = response.status

                    # Try to get response body
                    try:
                        body = await response.text()
                    except Exception:
                        body = None

                    # Try to parse JSON if applicable
                    response_json = None
                    if body and 'application/json' in response_headers.get('Content-Type', ''):
                        try:
                            response_json = await response.json()
                        except Exception:
                            pass

                    success = 200 <= status_code < 300

                    return ToolResult(
                        success=success,
                        output={
                            "status_code": status_code,
                            "headers": response_headers,
                            "body": body,
                            "json": response_json,
                            "elapsed": elapsed,
                            "url": str(response.url)
                        },
                        error=None if success else f"HTTP {status_code}",
                        metadata={
                            "method": method,
                            "redirected": str(response.url) != url
                        }
                    )

        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=f"Request failed: {str(e)}"
            )
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output=None,
                error=f"Request timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Unexpected error in HTTP request: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )


class DateTimeTool(Tool):
    """Date and time operations with timezone support."""

    def __init__(self):
        super().__init__(
            name="datetime",
            description="Date and time operations, formatting, parsing, timezone conversion"
        )

    def _parse_datetime(self, dt_str: str, timezone: Optional[str] = None) -> datetime:
        """Parse datetime string."""
        if dt_str.lower() == "now":
            dt = datetime.now(pytz.UTC)
        else:
            dt = date_parser.parse(dt_str)
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)

        if timezone:
            tz = pytz.timezone(timezone)
            dt = dt.astimezone(tz)

        return dt

    def _format_datetime(self, dt: datetime, fmt: Optional[str] = None) -> str:
        """Format datetime to string."""
        if fmt is None:
            return dt.isoformat()

        # Convert common format aliases to strftime format
        format_aliases = {
            'YYYY': '%Y',
            'MM': '%m',
            'DD': '%d',
            'HH': '%H',
            'mm': '%M',
            'ss': '%S',
        }

        # Apply aliases
        result_fmt = fmt
        for alias, strftime_code in format_aliases.items():
            result_fmt = result_fmt.replace(alias, strftime_code)

        return dt.strftime(result_fmt)

    async def execute(
        self,
        operation: str,
        datetime_str: Optional[str] = None,
        format: Optional[str] = None,
        timezone: Optional[str] = None,
        duration: Optional[Dict[str, int]] = None,
        datetime1: Optional[str] = None,
        datetime2: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute datetime operation.

        Args:
            operation: Operation type (now, format, parse, add, subtract, diff, timezone_convert)
                      Aliases: current_date, today, current_time -> now
            datetime_str: Datetime string
            format: Format string for strftime/strptime
                   Supports aliases: YYYY->%Y, MM->%m, DD->%d, HH->%H, mm->%M, ss->%S
            timezone: Timezone name (e.g., 'Asia/Shanghai', 'UTC')
            duration: Duration dict {days, hours, minutes, seconds}
            datetime1, datetime2: For diff operation
            **kwargs: Additional parameters

        Returns:
            Tool result with datetime operation result
        """
        self.validate_params(["operation"], {"operation": operation})

        # Map common aliases to actual operations
        operation_aliases = {
            'current_date': 'now',
            'current_time': 'now',
            'today': 'now',
            'get_time': 'now',
            'get_date': 'now',
        }

        # Normalize operation
        operation = operation_aliases.get(operation.lower(), operation.lower())

        logger.info(f"DateTime operation: {operation}")

        try:
            if operation == "now":
                dt = datetime.now(pytz.timezone(timezone) if timezone else pytz.UTC)
                return ToolResult(
                    success=True,
                    output=self._format_datetime(dt, format),
                    metadata={"timezone": timezone or "UTC"}
                )

            elif operation == "format":
                if not datetime_str:
                    return ToolResult(success=False, output=None, error="datetime_str required")

                dt = self._parse_datetime(datetime_str, timezone)
                result = self._format_datetime(dt, format)
                return ToolResult(success=True, output=result)

            elif operation == "parse":
                if not datetime_str:
                    return ToolResult(success=False, output=None, error="datetime_str required")

                dt = self._parse_datetime(datetime_str, timezone)
                return ToolResult(
                    success=True,
                    output={
                        "iso": dt.isoformat(),
                        "timestamp": dt.timestamp(),
                        "timezone": str(dt.tzinfo)
                    }
                )

            elif operation == "add":
                if not datetime_str or not duration:
                    return ToolResult(success=False, output=None, error="datetime_str and duration required")

                dt = self._parse_datetime(datetime_str, timezone)
                delta = timedelta(
                    days=duration.get("days", 0),
                    hours=duration.get("hours", 0),
                    minutes=duration.get("minutes", 0),
                    seconds=duration.get("seconds", 0)
                )
                result_dt = dt + delta
                return ToolResult(success=True, output=self._format_datetime(result_dt, format))

            elif operation == "subtract":
                if not datetime_str or not duration:
                    return ToolResult(success=False, output=None, error="datetime_str and duration required")

                dt = self._parse_datetime(datetime_str, timezone)
                delta = timedelta(
                    days=duration.get("days", 0),
                    hours=duration.get("hours", 0),
                    minutes=duration.get("minutes", 0),
                    seconds=duration.get("seconds", 0)
                )
                result_dt = dt - delta
                return ToolResult(success=True, output=self._format_datetime(result_dt, format))

            elif operation == "diff":
                if not datetime1 or not datetime2:
                    return ToolResult(success=False, output=None, error="datetime1 and datetime2 required")

                dt1 = self._parse_datetime(datetime1, timezone)
                dt2 = self._parse_datetime(datetime2, timezone)
                delta = dt2 - dt1

                return ToolResult(
                    success=True,
                    output={
                        "days": delta.days,
                        "seconds": delta.seconds,
                        "total_seconds": delta.total_seconds(),
                        "hours": delta.total_seconds() / 3600,
                        "minutes": delta.total_seconds() / 60
                    }
                )

            elif operation == "timezone_convert":
                if not datetime_str or not timezone:
                    return ToolResult(success=False, output=None, error="datetime_str and timezone required")

                dt = self._parse_datetime(datetime_str)
                tz = pytz.timezone(timezone)
                result_dt = dt.astimezone(tz)
                return ToolResult(
                    success=True,
                    output=self._format_datetime(result_dt, format),
                    metadata={"from_timezone": str(dt.tzinfo), "to_timezone": timezone}
                )

            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"DateTime operation failed: {e}", exc_info=True)
            return ToolResult(success=False, output=None, error=str(e))


class CalculatorTool(Tool):
    """Safe mathematical expression evaluation and unit conversion."""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Mathematical calculations and unit conversions"
        )

        # Safe math functions whitelist
        self.safe_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'ln': math.log,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'pow': pow,
            'pi': math.pi,
            'e': math.e,
        }

        # Unit conversion factors
        self.conversions = {
            'length': {
                'm': 1.0,
                'km': 1000.0,
                'cm': 0.01,
                'mm': 0.001,
                'mi': 1609.34,
                'ft': 0.3048,
                'in': 0.0254,
            },
            'weight': {
                'kg': 1.0,
                'g': 0.001,
                'mg': 0.000001,
                'lb': 0.453592,
                'oz': 0.0283495,
            },
            'time': {
                's': 1.0,
                'min': 60.0,
                'h': 3600.0,
                'day': 86400.0,
            },
            'data': {
                'B': 1.0,
                'KB': 1024.0,
                'MB': 1024.0 ** 2,
                'GB': 1024.0 ** 3,
                'TB': 1024.0 ** 4,
            }
        }

    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression."""
        # Remove whitespace
        expr = expression.strip()

        # Replace constants first
        expr_lower = expr.lower()
        expr_lower = expr_lower.replace('pi', str(math.pi))
        expr_lower = expr_lower.replace('e', str(math.e))

        # For function calls, use a more permissive pattern
        # Allow function names and numbers/operators
        allowed_chars = r'^[0-9+\-*/().,\s]+$'
        # Check if expression has function calls
        has_functions = any(func in expr.lower() for func in self.safe_functions.keys() if isinstance(func, str))

        if not has_functions:
            # Simple expression, strict validation
            if not re.match(allowed_chars, expr_lower):
                raise ValueError("Expression contains invalid characters")

        # Replace constants in original expression
        expr = expr.replace('pi', str(math.pi))
        expr = expr.replace('e', str(math.e))

        # Create safe namespace
        safe_dict = {"__builtins__": {}}
        safe_dict.update(self.safe_functions)

        try:
            result = eval(expr, safe_dict)
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")

    def _convert_unit(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between units."""
        # Temperature conversion
        if from_unit in ['C', 'F', 'K'] or to_unit in ['C', 'F', 'K']:
            return self._convert_temperature(value, from_unit, to_unit)

        # Find category for other units
        category = None
        for cat, units in self.conversions.items():
            if from_unit in units and to_unit in units:
                category = cat
                break

        if not category:
            raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")

        # Standard conversion
        base_value = value * self.conversions[category][from_unit]
        result = base_value / self.conversions[category][to_unit]
        return result

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature units."""
        # Convert to Celsius first
        if from_unit == 'C':
            celsius = value
        elif from_unit == 'F':
            celsius = (value - 32) * 5 / 9
        elif from_unit == 'K':
            celsius = value - 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")

        # Convert from Celsius to target
        if to_unit == 'C':
            return celsius
        elif to_unit == 'F':
            return celsius * 9 / 5 + 32
        elif to_unit == 'K':
            return celsius + 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")

    async def execute(
        self,
        operation: str,
        expression: Optional[str] = None,
        value: Optional[float] = None,
        from_unit: Optional[str] = None,
        to_unit: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute calculator operation.

        Args:
            operation: Operation type (calculate, convert_unit)
            expression: Mathematical expression
            value: Numeric value for conversion
            from_unit: Source unit
            to_unit: Target unit
            **kwargs: Additional parameters

        Returns:
            Tool result with calculation result
        """
        self.validate_params(["operation"], {"operation": operation})

        logger.info(f"Calculator operation: {operation}")

        try:
            if operation == "calculate":
                if not expression:
                    return ToolResult(success=False, output=None, error="expression required")

                result = self._safe_eval(expression)
                return ToolResult(
                    success=True,
                    output=result,
                    metadata={"expression": expression}
                )

            elif operation == "convert_unit":
                if value is None or not from_unit or not to_unit:
                    return ToolResult(
                        success=False,
                        output=None,
                        error="value, from_unit, and to_unit required"
                    )

                result = self._convert_unit(value, from_unit, to_unit)
                return ToolResult(
                    success=True,
                    output=result,
                    metadata={
                        "value": value,
                        "from_unit": from_unit,
                        "to_unit": to_unit
                    }
                )

            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"Calculator operation failed: {e}", exc_info=True)
            return ToolResult(success=False, output=None, error=str(e))


class ToolRegistry:
    """
    Tool registry for managing available tools.

    Features:
    - Tool registration and discovery
    - Tool execution
    - Error handling
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def unregister(self, tool_name: str):
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, str]]:
        """List all registered tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Tool name
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)

        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {tool_name}"
            )

        try:
            result = await tool.execute(**kwargs)
            logger.info(f"Tool {tool_name} executed: success={result.success}")
            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )


def create_default_registry(llm_service=None, config=None) -> ToolRegistry:
    """
    Create registry with default tools.

    Args:
        llm_service: Optional LLM service for CodeExecutionTool
        config: Optional config dict for CodeExecutionTool settings

    Returns:
        ToolRegistry with default tools registered
    """
    registry = ToolRegistry()

    # Register default tools (no dependencies)
    registry.register(ShellTool())
    registry.register(FileTool())
    registry.register(SearchTool())
    registry.register(HTTPTool())
    registry.register(DateTimeTool())
    registry.register(CalculatorTool())

    # Register CodeExecutionTool if dependencies are available
    if llm_service is not None:
        try:
            from alpha.tools.code_tool import CodeExecutionTool

            # Check if code_execution is enabled in config
            config_dict = config.dict() if hasattr(config, 'dict') else (config or {})
            code_exec_config = config_dict.get('code_execution', {})

            # Default to enabled if not specified
            is_enabled = code_exec_config.get('enabled', True)

            if is_enabled:
                code_tool = CodeExecutionTool(llm_service, config_dict)
                registry.register(code_tool)
                logger.info("CodeExecutionTool registered successfully")
        except Exception as e:
            logger.warning(f"Failed to register CodeExecutionTool: {e}")
            # Continue without code execution tool - non-critical

    # Register BrowserTool (Phase 4.3 - REQ-4.5)
    try:
        from alpha.tools.browser_tool import BrowserTool

        # Check if browser_automation is enabled in config
        config_dict = config.dict() if hasattr(config, 'dict') else (config or {})
        browser_config = config_dict.get('browser_automation', {})

        # Default to enabled if not specified
        is_enabled = browser_config.get('enabled', True)

        if is_enabled:
            browser_tool = BrowserTool(browser_config)
            if browser_tool.is_available():
                registry.register(browser_tool)
                logger.info("BrowserTool registered successfully")
            else:
                logger.warning("BrowserTool not available (Playwright not installed)")
    except ImportError:
        logger.warning("BrowserTool not available (module not found)")
    except Exception as e:
        logger.warning(f"Failed to register BrowserTool: {e}")
        # Continue without browser tool - non-critical

    return registry
