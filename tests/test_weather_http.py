"""
Test HTTP tool with weather API
"""

import asyncio
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.tools.registry import create_default_registry


@pytest.mark.asyncio
async def test_weather_api():
    """Test accessing weather API using HTTP tool."""
    print("=" * 80)
    print("Testing Weather Query with HTTP Tool")
    print("=" * 80)
    print()

    registry = create_default_registry()

    # Test 1: Beijing weather
    print("Test 1: Query Beijing weather")
    print("-" * 40)
    result = await registry.execute_tool(
        "http",
        url="https://wttr.in/Beijing?format=j1&lang=zh-cn",
        method="GET"
    )

    if result.success:
        print("✓ Request succeeded")
        data = result.output.get("json", {})
        if data:
            current = data.get("current_condition", [{}])[0]
            print(f"  Temperature: {current.get('temp_C')}°C")
            print(f"  Feels like: {current.get('FeelsLikeC')}°C")
            print(f"  Humidity: {current.get('humidity')}%")
            print(f"  Wind: {current.get('windspeedKmph')} km/h")

            # Get Chinese weather description
            weather_desc = current.get("lang_zh-cn", [{}])
            if weather_desc:
                print(f"  Condition: {weather_desc[0].get('value', 'N/A')}")
        else:
            print(f"  Status Code: {result.output.get('status_code')}")
            print(f"  Response length: {len(result.output.get('body', ''))}")
    else:
        print(f"✗ Request failed: {result.error}")

    print()

    # Test 2: Shanghai weather
    print("Test 2: Query Shanghai weather")
    print("-" * 40)
    result = await registry.execute_tool(
        "http",
        url="https://wttr.in/Shanghai?format=j1&lang=zh-cn",
        method="GET"
    )

    if result.success:
        print("✓ Request succeeded")
        data = result.output.get("json", {})
        if data:
            location = data.get("nearest_area", [{}])[0]
            print(f"  Location: {location.get('areaName', [{}])[0].get('value', 'N/A')}")

            current = data.get("current_condition", [{}])[0]
            print(f"  Temperature: {current.get('temp_C')}°C")

            weather_desc = current.get("lang_zh-cn", [{}])
            if weather_desc:
                print(f"  Condition: {weather_desc[0].get('value', 'N/A')}")
    else:
        print(f"✗ Request failed: {result.error}")

    print()
    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_weather_api())
