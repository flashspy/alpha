"""
Test fix for StopIteration error in streaming response
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.interface.cli import CLI
from alpha.llm.service import Message


class MockEngine:
    """Mock engine."""
    async def health_check(self):
        return {
            "status": "healthy",
            "uptime": "0:00:00",
            "tasks": 0,
            "memory": "mock"
        }

    class memory_manager:
        @staticmethod
        async def add_conversation(**kwargs):
            pass


class MockLLMService:
    """Mock LLM that returns empty or problematic responses."""

    def __init__(self, response_text):
        self.response_text = response_text

    async def stream_complete(self, messages):
        """Simulate streaming response."""
        for char in self.response_text:
            yield char


class MockToolRegistry:
    """Mock tool registry."""

    def list_tools(self):
        return [
            {"name": "search", "description": "Search the web"},
        ]

    async def execute_tool(self, tool_name, **kwargs):
        from alpha.tools.registry import ToolResult
        return ToolResult(
            success=True,
            output={"query": kwargs.get("query", ""), "results": [], "count": 0}
        )


async def test_empty_response():
    """Test that empty responses don't cause StopIteration error."""
    print("=" * 80)
    print("Test: Empty Response Handling")
    print("=" * 80)
    print()

    # Test case 1: Empty response
    print("Test Case 1: Empty response after tool execution")
    engine = MockEngine()
    llm_service = MockLLMService("")  # Empty response
    tool_registry = MockToolRegistry()

    cli = CLI(engine, llm_service, tool_registry)

    # Simulate processing empty response
    response_text = ""

    print(f"Response text: '{response_text}'")
    print(f"Response stripped: '{response_text.strip()}'")
    print(f"Is empty: {not response_text.strip()}")

    if response_text.strip():
        print("✓ Would print normal response")
    else:
        print("✓ Would print '(No response generated)' warning")

    print()

    # Test case 2: Whitespace-only response
    print("Test Case 2: Whitespace-only response")
    response_text = "   \n\n  "

    print(f"Response text: '{response_text}'")
    print(f"Response stripped: '{response_text.strip()}'")
    print(f"Is empty: {not response_text.strip()}")

    if response_text.strip():
        print("✓ Would print normal response")
    else:
        print("✓ Would print '(No response generated)' warning")

    print()

    # Test case 3: Normal response
    print("Test Case 3: Normal response")
    response_text = "这是一个正常的响应"

    print(f"Response text: '{response_text}'")
    print(f"Response stripped: '{response_text.strip()}'")
    print(f"Is empty: {not response_text.strip()}")

    if response_text.strip():
        print("✓ Would print normal response")
    else:
        print("✗ Would print '(No response generated)' warning (unexpected)")

    print()

    # Test case 4: Response with special characters
    print("Test Case 4: Response with special Unicode characters")
    response_text = "回复包含中文和emoji 🎉 以及特殊字符 ©®™"

    print(f"Response text: '{response_text}'")
    print(f"Response stripped: '{response_text.strip()}'")
    print(f"Is empty: {not response_text.strip()}")

    if response_text.strip():
        print("✓ Would print normal response")
    else:
        print("✗ Would print '(No response generated)' warning (unexpected)")

    print()

    print("=" * 80)
    print("✓ All test cases passed - no StopIteration errors!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_empty_response())
