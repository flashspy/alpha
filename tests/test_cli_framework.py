"""
Alpha CLI Interactive Testing Framework

Comprehensive testing framework for end-to-end CLI interaction testing.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from io import StringIO
import sys

from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config
from alpha.llm.service import LLMService, Message, LLMProvider, LLMResponse
from alpha.tools.registry import create_default_registry, ToolRegistry, ToolResult


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    description: str
    user_input: str
    expected_behavior: str
    validation_func: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)
    timeout: int = 30


@dataclass
class TestResult:
    """Test execution result."""
    test_case: TestCase
    passed: bool
    execution_time: float
    response: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing without API calls."""

    def __init__(self, api_key: str = "mock", model: str = "mock-model", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.call_count = 0
        self.responses = []

    def set_responses(self, responses: List[str]):
        """Set predefined responses for testing."""
        self.responses = responses
        self.call_count = 0

    async def complete(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """Return mock response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = "I understand. How can I help you?"

        self.call_count += 1

        return LLMResponse(
            content=response,
            model=self.model,
            tokens_used=100,
            finish_reason="stop"
        )

    async def stream_complete(
        self,
        messages: List[Message],
        **kwargs
    ):
        """Mock streaming response."""
        response = await self.complete(messages, **kwargs)
        # Yield character by character to simulate streaming
        for char in response.content:
            yield char


class MockToolRegistry(ToolRegistry):
    """Mock tool registry that records calls without executing."""

    def __init__(self):
        super().__init__()
        self.tool_calls = []

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Record tool call and return mock result."""
        self.tool_calls.append({
            "tool": tool_name,
            "params": kwargs,
            "timestamp": datetime.now().isoformat()
        })

        # Return mock results based on tool type
        if tool_name == "search":
            return ToolResult(
                success=True,
                output={
                    "query": kwargs.get("query", ""),
                    "results": [
                        {
                            "title": "Mock Search Result",
                            "url": "https://example.com",
                            "snippet": "This is a mock search result for testing.",
                            "source": "mock"
                        }
                    ],
                    "count": 1
                }
            )
        elif tool_name == "datetime":
            return ToolResult(
                success=True,
                output="2026-01-29T12:00:00+00:00"
            )
        elif tool_name == "http":
            return ToolResult(
                success=True,
                output={
                    "status_code": 200,
                    "body": '{"success": true, "data": "mock"}',
                    "headers": {}
                }
            )
        elif tool_name == "file":
            return ToolResult(
                success=True,
                output="Mock file content"
            )
        elif tool_name == "shell":
            return ToolResult(
                success=True,
                output="Mock command output"
            )
        elif tool_name == "calculator":
            return ToolResult(
                success=True,
                output=42.0
            )
        else:
            return ToolResult(
                success=True,
                output=f"Mock result for {tool_name}"
            )


class CLITestFramework:
    """
    CLI Interactive Testing Framework.

    Provides comprehensive testing capabilities for Alpha CLI interactions.
    """

    def __init__(self, use_mocks: bool = True):
        """
        Initialize test framework.

        Args:
            use_mocks: Whether to use mock providers (True for unit tests, False for integration tests)
        """
        self.use_mocks = use_mocks
        self.test_results: List[TestResult] = []
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """Setup test environment."""
        # Create mock or real components based on use_mocks
        if self.use_mocks:
            self.llm_provider = MockLLMProvider()
            self.tool_registry = MockToolRegistry()
        else:
            # Use real components for integration testing
            config = load_config('config.yaml')
            self.llm_service = LLMService.from_config(config.llm)
            self.tool_registry = create_default_registry()

    async def teardown(self):
        """Cleanup test environment."""
        pass

    async def run_test(self, test_case: TestCase) -> TestResult:
        """
        Run a single test case.

        Args:
            test_case: Test case to execute

        Returns:
            Test result
        """
        self.logger.info(f"Running test: {test_case.name}")
        start_time = datetime.now()

        try:
            # Setup mock responses if using mocks
            if self.use_mocks and hasattr(self, 'llm_provider'):
                # Define expected responses for the test
                self.llm_provider.set_responses([
                    test_case.expected_behavior
                ])

            # Simulate CLI interaction
            response, tool_calls = await self._simulate_interaction(test_case.user_input)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Validate result
            passed = True
            error = None

            if test_case.validation_func:
                try:
                    validation_result = test_case.validation_func(response, tool_calls)
                    if isinstance(validation_result, bool):
                        passed = validation_result
                    else:
                        passed = bool(validation_result)
                except Exception as e:
                    passed = False
                    error = f"Validation failed: {str(e)}"
            else:
                # Basic validation: check if response is not empty
                passed = bool(response.strip())

            return TestResult(
                test_case=test_case,
                passed=passed,
                execution_time=execution_time,
                response=response,
                tool_calls=tool_calls,
                error=error,
                metadata={
                    "mock_mode": self.use_mocks,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Test failed with exception: {e}", exc_info=True)

            return TestResult(
                test_case=test_case,
                passed=False,
                execution_time=execution_time,
                response="",
                error=str(e)
            )

    async def _simulate_interaction(self, user_input: str) -> tuple:
        """
        Simulate CLI interaction.

        Args:
            user_input: User's input message

        Returns:
            Tuple of (response text, tool calls)
        """
        if self.use_mocks:
            # Use mock provider
            messages = [
                Message(role="system", content="You are Alpha, a helpful AI assistant."),
                Message(role="user", content=user_input)
            ]

            response = await self.llm_provider.complete(messages)

            # Parse tool calls from response
            tool_calls = self._parse_tool_calls_from_response(response.content)

            # Also get tool calls from mock registry if available
            if hasattr(self.tool_registry, 'tool_calls'):
                tool_calls.extend(self.tool_registry.tool_calls)

            return response.content, tool_calls
        else:
            # Use real LLM service for integration testing
            messages = [Message(role="user", content=user_input)]
            response = await self.llm_service.complete(messages)
            tool_calls = self._parse_tool_calls_from_response(response.content)
            return response.content, tool_calls

    def _parse_tool_calls_from_response(self, response: str) -> list:
        """
        Parse tool calls from response text.

        Args:
            response: Response text that may contain TOOL: and PARAMS: lines

        Returns:
            List of tool call dictionaries
        """
        tool_calls = []
        lines = response.split('\n')
        current_tool = None
        current_params = None

        for line in lines:
            if line.startswith("TOOL:"):
                if current_tool and current_params:
                    tool_calls.append({
                        "tool": current_tool,
                        "params": current_params,
                        "timestamp": datetime.now().isoformat()
                    })
                current_tool = line.replace("TOOL:", "").strip()
                current_params = None
            elif line.startswith("PARAMS:"):
                params_str = line.replace("PARAMS:", "").strip()
                try:
                    current_params = json.loads(params_str)
                except json.JSONDecodeError:
                    # Try to parse as simple dict string
                    try:
                        current_params = eval(params_str)
                    except:
                        current_params = {"raw": params_str}

        # Add last tool call
        if current_tool and current_params:
            tool_calls.append({
                "tool": current_tool,
                "params": current_params,
                "timestamp": datetime.now().isoformat()
            })

        return tool_calls

    async def run_test_suite(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        Run a suite of test cases.

        Args:
            test_cases: List of test cases to execute

        Returns:
            List of test results
        """
        await self.setup()

        results = []
        for test_case in test_cases:
            result = await self.run_test(test_case)
            results.append(result)
            self.test_results.append(result)

        await self.teardown()

        return results

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate test report.

        Args:
            output_file: Optional file path to save report

        Returns:
            Report text
        """
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.passed)
        failed = total - passed

        report_lines = [
            "=" * 80,
            "Alpha CLI Interactive Test Report",
            "=" * 80,
            f"Generated: {datetime.now().isoformat()}",
            f"Total Tests: {total}",
            f"Passed: {passed} ({passed/total*100:.1f}%)" if total > 0 else "Passed: 0",
            f"Failed: {failed} ({failed/total*100:.1f}%)" if total > 0 else "Failed: 0",
            "=" * 80,
            "",
            "Test Results:",
            ""
        ]

        for i, result in enumerate(self.test_results, 1):
            status = "✓ PASS" if result.passed else "✗ FAIL"
            report_lines.extend([
                f"{i}. [{status}] {result.test_case.name}",
                f"   Description: {result.test_case.description}",
                f"   Execution Time: {result.execution_time:.3f}s",
                f"   Tags: {', '.join(result.test_case.tags)}",
            ])

            if not result.passed and result.error:
                report_lines.append(f"   Error: {result.error}")

            if result.tool_calls:
                report_lines.append(f"   Tool Calls: {len(result.tool_calls)}")

            report_lines.append("")

        report_lines.extend([
            "=" * 80,
            "Summary by Tag:",
            ""
        ])

        # Group results by tag
        tag_stats = {}
        for result in self.test_results:
            for tag in result.test_case.tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {"total": 0, "passed": 0}
                tag_stats[tag]["total"] += 1
                if result.passed:
                    tag_stats[tag]["passed"] += 1

        for tag, stats in sorted(tag_stats.items()):
            pass_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            report_lines.append(f"  {tag}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")

        report_lines.append("=" * 80)

        report = "\n".join(report_lines)

        if output_file:
            Path(output_file).write_text(report)
            self.logger.info(f"Report saved to {output_file}")

        return report
