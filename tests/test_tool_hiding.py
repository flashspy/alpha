"""
Integration test - Demonstrate tool call hiding
"""

import asyncio
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.interface.cli import CLI


class MockEngine:
    """Mock engine for testing."""
    async def health_check(self):
        return {
            "status": "healthy",
            "uptime": "0:00:00",
            "tasks": 0,
            "memory": "mock"
        }


class MockLLMService:
    """Mock LLM that returns multi-line YAML format."""

    async def stream_complete(self, messages):
        """Simulate LLM response with multi-line YAML PARAMS."""
        # Simulate the problematic response format
        response = """我来帮您查询成都今天的天气情况。

TOOL: http
PARAMS:
  url: "https://wttr.in/成都?format=j1&lang=zh-cn"
  method: "GET"

正在为您查询..."""

        for char in response:
            yield char


class MockToolRegistry:
    """Mock tool registry."""

    def list_tools(self):
        return [
            {"name": "http", "description": "Execute HTTP requests"},
            {"name": "search", "description": "Search the web"},
        ]

    async def execute_tool(self, tool_name, **kwargs):
        """Return mock weather data."""
        from alpha.tools.registry import ToolResult

        return ToolResult(
            success=True,
            output={
                "json": {
                    "current_condition": [{
                        "temp_C": "15",
                        "FeelsLikeC": "13",
                        "humidity": "45",
                        "windspeedKmph": "10",
                        "lang_zh-cn": [{"value": "晴"}]
                    }]
                }
            }
        )


@pytest.mark.asyncio
async def test_tool_hiding():
    """Test that tool calls are properly hidden from user."""

    print("=" * 80)
    print("Integration Test: Tool Call Hiding")
    print("=" * 80)
    print()

    # Create CLI with mocks
    engine = MockEngine()
    llm_service = MockLLMService()
    tool_registry = MockToolRegistry()

    cli = CLI(engine, llm_service, tool_registry)

    # Simulate the LLM response
    response = """我来帮您查询成都今天的天气情况。

TOOL: http
PARAMS:
  url: "https://wttr.in/成都?format=j1&lang=zh-cn"
  method: "GET"

正在为您查询..."""

    print("Step 1: LLM Raw Response")
    print("-" * 40)
    print(response)
    print()

    # Parse tool calls
    tool_calls = cli._parse_tool_calls(response)

    print("Step 2: Parsed Tool Calls")
    print("-" * 40)
    print(f"Number of tools detected: {len(tool_calls)}")
    if tool_calls:
        for i, call in enumerate(tool_calls, 1):
            print(f"  Tool {i} Type: {call['type']}")
            print(f"  Tool {i} Name: {call['name']}")
            print(f"  Params {i}: {call['params']}")
    print()

    # Extract user message
    user_message = cli._extract_user_message(response)

    print("Step 3: User-Facing Message (After Filtering)")
    print("-" * 40)
    print(user_message)
    print()

    print("Step 4: Verification")
    print("-" * 40)
    has_tool = "TOOL:" in user_message
    has_params = "PARAMS:" in user_message
    has_indented = any(line.startswith('  ') for line in user_message.split('\n'))

    print(f"Contains 'TOOL:': {has_tool} {'❌ FAILED' if has_tool else '✓ PASS'}")
    print(f"Contains 'PARAMS:': {has_params} {'❌ FAILED' if has_params else '✓ PASS'}")
    print(f"Contains indented lines: {has_indented} {'❌ FAILED' if has_indented else '✓ PASS'}")
    print()

    success = not (has_tool or has_params or has_indented)

    print("=" * 80)
    if success:
        print("✓ TEST PASSED: Tool call details successfully hidden from user!")
    else:
        print("✗ TEST FAILED: Tool call details leaked to user!")
    print("=" * 80)

    return success


if __name__ == "__main__":
    success = asyncio.run(test_tool_hiding())
    sys.exit(0 if success else 1)
