"""
Comprehensive Test Cases for Alpha CLI

Covers various scenarios including:
- Basic conversations
- Tool usage (search, datetime, calculator, file, shell, http)
- Multi-tool scenarios
- Error handling
- Edge cases
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_cli_framework import CLITestFramework, TestCase


def create_test_cases():
    """Create comprehensive test case suite."""

    test_cases = []

    # ========== Basic Conversation Tests ==========
    test_cases.append(TestCase(
        name="basic_greeting",
        description="Test basic greeting response",
        user_input="Hello",
        expected_behavior="Hello! How can I help you today?",
        validation_func=lambda resp, tools: len(resp) > 0 and len(tools) == 0,
        tags=["basic", "conversation"]
    ))

    test_cases.append(TestCase(
        name="simple_question",
        description="Test answering simple question without tools",
        user_input="What is the capital of France?",
        expected_behavior="The capital of France is Paris.",
        validation_func=lambda resp, tools: "paris" in resp.lower() and len(tools) == 0,
        tags=["basic", "conversation", "knowledge"]
    ))

    # ========== Search Tool Tests ==========
    test_cases.append(TestCase(
        name="search_general_query",
        description="Test web search functionality",
        user_input="Search for Python programming tutorials",
        expected_behavior="TOOL: search\nPARAMS: {\"query\": \"Python programming tutorials\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "search" for t in tools),
        tags=["tools", "search"]
    ))

    test_cases.append(TestCase(
        name="search_current_events",
        description="Test searching for current events",
        user_input="What's the latest news about AI?",
        expected_behavior="TOOL: search\nPARAMS: {\"query\": \"latest AI news\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "search" for t in tools),
        tags=["tools", "search", "current-events"]
    ))

    test_cases.append(TestCase(
        name="search_stock_market",
        description="Test searching for stock market information",
        user_input="今天股市行情如何",
        expected_behavior="TOOL: search\nPARAMS: {\"query\": \"今日股市行情\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "search" for t in tools),
        tags=["tools", "search", "finance", "chinese"]
    ))

    # ========== DateTime Tool Tests ==========
    test_cases.append(TestCase(
        name="datetime_current_time",
        description="Test getting current time",
        user_input="What time is it now?",
        expected_behavior="TOOL: datetime\nPARAMS: {\"operation\": \"now\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "datetime" for t in tools),
        tags=["tools", "datetime"]
    ))

    test_cases.append(TestCase(
        name="datetime_current_date",
        description="Test getting current date with alias",
        user_input="What's today's date?",
        expected_behavior="TOOL: datetime\nPARAMS: {\"operation\": \"current_date\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "datetime" for t in tools),
        tags=["tools", "datetime"]
    ))

    test_cases.append(TestCase(
        name="datetime_timezone_conversion",
        description="Test timezone conversion",
        user_input="What time is it in Tokyo?",
        expected_behavior="TOOL: datetime\nPARAMS: {\"operation\": \"now\", \"timezone\": \"Asia/Tokyo\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "datetime" for t in tools),
        tags=["tools", "datetime", "timezone"]
    ))

    # ========== Calculator Tool Tests ==========
    test_cases.append(TestCase(
        name="calculator_basic_math",
        description="Test basic calculation",
        user_input="Calculate 25 * 4 + 10",
        expected_behavior="TOOL: calculator\nPARAMS: {\"operation\": \"calculate\", \"expression\": \"25 * 4 + 10\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "calculator" for t in tools),
        tags=["tools", "calculator", "math"]
    ))

    test_cases.append(TestCase(
        name="calculator_unit_conversion",
        description="Test unit conversion",
        user_input="Convert 100 km to miles",
        expected_behavior="TOOL: calculator\nPARAMS: {\"operation\": \"convert_unit\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "calculator" for t in tools),
        tags=["tools", "calculator", "conversion"]
    ))

    # ========== HTTP Tool Tests ==========
    test_cases.append(TestCase(
        name="http_get_request",
        description="Test HTTP GET request",
        user_input="Fetch data from https://api.example.com/data",
        expected_behavior="TOOL: http\nPARAMS: {\"method\": \"GET\", \"url\": \"https://api.example.com/data\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "http" for t in tools),
        tags=["tools", "http", "api"]
    ))

    # ========== File Tool Tests ==========
    test_cases.append(TestCase(
        name="file_read_operation",
        description="Test reading a file",
        user_input="Read the contents of config.yaml",
        expected_behavior="TOOL: file\nPARAMS: {\"operation\": \"read\", \"path\": \"config.yaml\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "file" for t in tools),
        tags=["tools", "file", "read"]
    ))

    test_cases.append(TestCase(
        name="file_list_directory",
        description="Test listing directory contents",
        user_input="List files in the current directory",
        expected_behavior="TOOL: file\nPARAMS: {\"operation\": \"list\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "file" for t in tools),
        tags=["tools", "file", "list"]
    ))

    # ========== Shell Tool Tests ==========
    test_cases.append(TestCase(
        name="shell_list_files",
        description="Test shell command execution",
        user_input="Run ls -la command",
        expected_behavior="TOOL: shell\nPARAMS: {\"command\": \"ls -la\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "shell" for t in tools),
        tags=["tools", "shell", "filesystem"]
    ))

    # ========== Multi-Tool Scenarios ==========
    test_cases.append(TestCase(
        name="multi_tool_search_datetime",
        description="Test using search and datetime together",
        user_input="Search for today's weather",
        expected_behavior="TOOL: search\nPARAMS: {\"query\": \"today's weather\"}\nTOOL: datetime\nPARAMS: {\"operation\": \"now\"}",
        validation_func=lambda resp, tools: (
            any(t["tool"] == "search" for t in tools) and
            any(t["tool"] == "datetime" for t in tools)
        ),
        tags=["tools", "multi-tool", "search", "datetime"]
    ))

    test_cases.append(TestCase(
        name="multi_tool_complex_query",
        description="Test complex query requiring multiple tools",
        user_input="Calculate how many days until 2026-12-31 and search for New Year plans",
        expected_behavior="TOOL: datetime\nPARAMS: {\"operation\": \"now\"}\nTOOL: calculator\nPARAMS: {\"operation\": \"calculate\", \"expression\": \"days_between\"}\nTOOL: search\nPARAMS: {\"query\": \"New Year plans\"}",
        validation_func=lambda resp, tools: len(tools) >= 2,
        tags=["tools", "multi-tool", "complex"]
    ))

    # ========== Error Handling Tests ==========
    test_cases.append(TestCase(
        name="error_invalid_calculation",
        description="Test handling invalid calculation",
        user_input="Calculate abc + xyz",
        expected_behavior="Error or explanation",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["error-handling", "calculator"]
    ))

    test_cases.append(TestCase(
        name="error_file_not_found",
        description="Test handling non-existent file",
        user_input="Read the file nonexistent_file_12345.txt",
        expected_behavior="File not found error",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["error-handling", "file"]
    ))

    # ========== Edge Cases ==========
    test_cases.append(TestCase(
        name="edge_empty_search",
        description="Test search with minimal input",
        user_input="Search for a",
        expected_behavior="Search response",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["edge-case", "search"]
    ))

    test_cases.append(TestCase(
        name="edge_very_long_input",
        description="Test handling very long input",
        user_input="Tell me about " + "artificial intelligence " * 50,
        expected_behavior="Appropriate response",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["edge-case", "long-input"]
    ))

    test_cases.append(TestCase(
        name="edge_special_characters",
        description="Test handling special characters",
        user_input="Calculate (5 + 3) * 2 / (4 - 1)",
        expected_behavior="Calculation result",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["edge-case", "calculator", "special-chars"]
    ))

    # ========== Multilingual Tests ==========
    test_cases.append(TestCase(
        name="multilingual_chinese_query",
        description="Test Chinese language input",
        user_input="今天天气怎么样？",
        expected_behavior="Chinese response",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["multilingual", "chinese", "weather"]
    ))

    test_cases.append(TestCase(
        name="multilingual_mixed_language",
        description="Test mixed language input",
        user_input="Search for Python教程",
        expected_behavior="TOOL: search\nPARAMS: {\"query\": \"Python教程\"}",
        validation_func=lambda resp, tools: any(t["tool"] == "search" for t in tools),
        tags=["multilingual", "mixed", "search"]
    ))

    # ========== Performance Tests ==========
    test_cases.append(TestCase(
        name="performance_quick_response",
        description="Test quick response time",
        user_input="Hello",
        expected_behavior="Quick greeting",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["performance", "basic"],
        timeout=5
    ))

    test_cases.append(TestCase(
        name="performance_complex_query",
        description="Test complex query performance",
        user_input="Calculate the square root of 144, search for Python tutorials, and tell me the current time in New York",
        expected_behavior="Multiple tool results",
        validation_func=lambda resp, tools: len(resp) > 0,
        tags=["performance", "complex", "multi-tool"],
        timeout=30
    ))

    return test_cases


async def main():
    """Run comprehensive test suite."""
    print("=" * 80)
    print("Alpha CLI Comprehensive Test Suite")
    print("=" * 80)
    print()

    # Create test cases
    test_cases = create_test_cases()
    print(f"Created {len(test_cases)} test cases")
    print()

    # Initialize test framework
    framework = CLITestFramework(use_mocks=True)

    # Run tests
    print("Running tests...")
    print()

    results = await framework.run_test_suite(test_cases)

    # Generate and display report
    report = framework.generate_report(output_file="test_reports/cli_test_report.txt")
    print(report)

    # Exit with appropriate code
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    # Create test reports directory
    Path("test_reports").mkdir(exist_ok=True)

    # Run tests
    asyncio.run(main())
