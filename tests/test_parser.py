"""
Test enhanced tool call parser
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.interface.cli import CLI


def test_parser():
    """Test tool call parser with different formats."""

    # Create a minimal CLI instance (we only need the parser methods)
    class MockEngine:
        pass

    class MockLLMService:
        pass

    class MockRegistry:
        pass

    cli = CLI(MockEngine(), MockLLMService(), MockRegistry())

    print("=" * 80)
    print("Testing Enhanced Tool Call Parser")
    print("=" * 80)
    print()

    # Test 1: Single-line JSON format (original)
    print("Test 1: Single-line JSON format")
    print("-" * 40)
    response1 = """我来帮您查询天气。

TOOL: http
PARAMS: {"url": "https://wttr.in/Beijing?format=j1", "method": "GET"}

正在查询中..."""

    tool_calls1 = cli._parse_tool_calls(response1)
    user_msg1 = cli._extract_user_message(response1)

    print(f"Tool calls parsed: {len(tool_calls1)}")
    if tool_calls1:
        print(f"  Type: {tool_calls1[0]['type']}")
        print(f"  Name: {tool_calls1[0]['name']}")
        print(f"  Params: {tool_calls1[0]['params']}")
    print(f"User message: {repr(user_msg1)}")
    print()

    # Test 2: Multi-line YAML format (problematic format from user)
    print("Test 2: Multi-line YAML format")
    print("-" * 40)
    response2 = """我来帮您查询成都今天的天气情况。

TOOL: http
PARAMS:
  url: "https://wttr.in/成都?format=j1&lang=zh-cn"
  method: "GET"

正在查询中..."""

    tool_calls2 = cli._parse_tool_calls(response2)
    user_msg2 = cli._extract_user_message(response2)

    print(f"Tool calls parsed: {len(tool_calls2)}")
    if tool_calls2:
        print(f"  Type: {tool_calls2[0]['type']}")
        print(f"  Name: {tool_calls2[0]['name']}")
        print(f"  Params: {tool_calls2[0]['params']}")
    print(f"User message: {repr(user_msg2)}")
    print()

    # Test 3: Multiple tools
    print("Test 3: Multiple tools (mixed format)")
    print("-" * 40)
    response3 = """让我先搜索，然后访问网站。

TOOL: search
PARAMS: {"query": "北京天气"}

TOOL: http
PARAMS:
  url: "https://example.com"
  method: "GET"

处理中..."""

    tool_calls3 = cli._parse_tool_calls(response3)
    user_msg3 = cli._extract_user_message(response3)

    print(f"Tool calls parsed: {len(tool_calls3)}")
    for i, call in enumerate(tool_calls3, 1):
        print(f"  Tool {i} Type: {call['type']}")
        print(f"  Tool {i} Name: {call['name']}")
        print(f"  Params {i}: {call['params']}")
    print(f"User message: {repr(user_msg3)}")
    print()

    # Test 4: YAML with nested structure
    print("Test 4: Complex YAML structure")
    print("-" * 40)
    response4 = """TOOL: http
PARAMS:
  url: "https://api.example.com/data"
  method: "POST"
  headers:
    Content-Type: "application/json"
  json:
    query: "test"

完成。"""

    tool_calls4 = cli._parse_tool_calls(response4)
    user_msg4 = cli._extract_user_message(response4)

    print(f"Tool calls parsed: {len(tool_calls4)}")
    if tool_calls4:
        print(f"  Type: {tool_calls4[0]['type']}")
        print(f"  Name: {tool_calls4[0]['name']}")
        print(f"  Params: {tool_calls4[0]['params']}")
    print(f"User message: {repr(user_msg4)}")
    print()

    print("=" * 80)
    print("All parser tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_parser()
